"""
Chat Agent with M-Pesa Till Payment Tool and Airtable Integration

This module implements a chat agent that can:
1. Provide information about data bundles and minutes offers
2. Initiate M-Pesa Till payments
"""

import os
import logging
import json
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Import from LangChain
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage
from langchain.schema.messages import ToolMessage
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI

# Import our tools
from mpesa_tool import get_mpesa_tool, get_transaction_status_tool
from airtable_tool import get_airtable_tools
from memory_handler import DynamicMemoryHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ChatAgent:
    """Chat agent with M-Pesa Till payment and Airtable integration."""
    
    def __init__(self):
        """Initialize the chat agent."""
        # Initialize memory handler
        self.memory_handler = DynamicMemoryHandler()
        
        # Initialize tools
        self.tools = self._get_tools()
        
        # Cache for agent executors to handle multiple users
        self.agent_executors = {}
        
        # Initialize user sessions for tracking phone numbers and payment states
        self.user_sessions = {}
        
        # Initialize the new transaction status tool
        self.transaction_status_tool = get_transaction_status_tool()
        
        logger.info("Chat agent initialized with tools and memory handler")
    
    def _get_tools(self) -> List[BaseTool]:
        """Get all tools for the agent."""
        tools = []
        
        # Add M-Pesa tool
        try:
            mpesa_tool = get_mpesa_tool()
            tools.append(mpesa_tool)
            logger.info("Added M-Pesa payment tool to the agent")
        except Exception as e:
            logger.error(f"Failed to initialize M-Pesa tool: {str(e)}")
        
        # Add Airtable tools
        try:
            airtable_tools = get_airtable_tools()
            tools.extend(airtable_tools)
            logger.info(f"Added {len(airtable_tools)} Airtable tools to the agent")
        except Exception as e:
            logger.error(f"Failed to initialize Airtable tools: {str(e)}")
        
        # Add the new transaction status tool
        tools.append(self.transaction_status_tool)
        
        return tools
    
    def _get_agent_executor(self, user_id: str) -> AgentExecutor:
        """
        Get or create an agent executor for a specific user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Agent executor instance
        """
        # Return cached executor if exists
        if user_id in self.agent_executors:
            return self.agent_executors[user_id]
        
        # Define the system message with instructions
        system_message = """You are a helpful assistant that can provide information about mobile data bundles and minutes/airtime offers. 
        
        You can search for options from our Airtable database and help users purchase them via M-Pesa.
        
        CRITICAL PAYMENT INSTRUCTIONS - READ CAREFULLY:
        1. NEVER initiate a payment without EXPLICIT confirmation from the user
        2. When a user asks about buying data bundles or airtime, ALWAYS first show options using search_data_bundles or search_minutes_offers
        3. NEVER use mpesa_till_payment tool until the user has selected a specific bundle and CLEARLY confirmed they want to pay
        4. Always get EXPLICIT confirmation by asking "Would you like to proceed with the payment of X KSh for Y bundle?"
        5. Wait for user to type "yes", "confirm", or "proceed" BEFORE initiating any payment
        
        DATA BUNDLES SEARCH CAPABILITIES:
        1. Use the search_data_bundles tool to find relevant options when users ask about available data plans
        2. Use the search_bundles_by_price_range tool when users want to see data options within a price range
        3. Use the get_bundle_by_price tool when users are interested in a specific data bundle price
        
        MINUTES AND AIRTIME SEARCH CAPABILITIES:
        1. Use the search_minutes_offers tool to find relevant minutes/airtime options when users ask about available calling plans, most users will refer to this as an offer
        2. Use the search_minutes_by_price_range tool when users want to see minutes options within a price range
        3. Use the get_minutes_by_price tool when users are interested in a specific minutes package price
        
        COMPLETE PAYMENT PROCESS:
        1. Get the user's phone number (ask if you don't have it already)
        2. ONLY THEN use the mpesa_till_payment tool with the correct amount and phone number
        3. AFTER initiating payment, ALWAYS check the transaction status using the mpesa_transaction_status tool
        4. If transaction status shows FAILURE, inform the user and suggest they try again
        5. If transaction status shows SUCCESS, confirm to the user that payment has been received and their purchase is complete
        
        TRANSACTION STATUS CHECKING:
        1. After initiating a payment, extract the transaction_id or originator_conversation_id from the payment response
        2. Use mpesa_transaction_status tool to check the status using this ID
        3. Parse the status response to determine if the transaction was successful or failed
        4. If status is "Completed" or shows success, inform the user their payment was successful and their purchase is complete
        5. If status shows any error or failure, politely ask the user if they would like to try the payment again
        
        PRODUCT INFORMATION FORMATTING:
        When displaying products to users, include:
        - Product name/description
        - Price in KSh
        - Validity period
        - Any special features
        
        Be conversational and helpful. If a user asks about buying something, ONLY show options first. Never jump directly to payment.
        """
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Get memory for the user
        memory = self.memory_handler.get_memory(user_id)
        
        # Create a chat model
        model = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            temperature=0.1
        )
        
        # Create the agent
        agent = create_openai_functions_agent(
            llm=model,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create the agent executor with tool-calling control
        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=memory,
            verbose=True,
            return_intermediate_steps=True,  # Get tool calls for inspection
            handle_parsing_errors=True,
            max_iterations=3  # Limit iterations to prevent runaway tool calls
        )
        
        # Cache the executor
        self.agent_executors[user_id] = executor
        
        return executor
    
    def process_message(self, message: str, user_id: str) -> str:
        """
        Process a message from a user.
        
        Args:
            message: The message text from the user
            user_id: Unique identifier for the user
            
        Returns:
            Response from the agent
        """
        logger.info(f"Processing message from user {user_id}: {message}")
        
        # Initialize user session if not exists
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                "payment_confirmed": False,
                "phone_number": None,
                "pending_payment": None,
            }
        
        # Check if this is a payment confirmation
        if self._is_payment_confirmation(message) and self.user_sessions[user_id].get("pending_payment"):
            # User confirmed a pending payment
            self.user_sessions[user_id]["payment_confirmed"] = True
            logger.info(f"User {user_id} confirmed payment")
        
        # Extract phone number from the message if present
        self._extract_and_store_phone_number(message, user_id)
        
        # Process the message
        try:
            agent_executor = self._get_agent_executor(user_id)
            response = agent_executor.invoke({"input": message})
            
            # Inspect tool calls to check for unauthorized payment attempts
            if "intermediate_steps" in response:
                steps = response["intermediate_steps"]
                self._check_and_block_payments(steps, user_id, message)
            
            logger.info(f"Got response for user {user_id}")
            return response["output"]
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg)
            return "I'm sorry, I encountered an error while processing your request. Please try again later."
    
    def _check_and_block_payments(self, steps, user_id: str, original_message: str) -> None:
        """
        Check for unauthorized payment attempts and block them if necessary.
        
        Args:
            steps: Intermediate steps from the agent
            user_id: Unique identifier for the user
            original_message: Original message from the user
        """
        for step in steps:
            tool_call = step[0]
            if hasattr(tool_call, "tool") and tool_call.tool == "mpesa_till_payment":
                # Check if the user explicitly asked to make a payment
                payment_keywords = ["proceed", "confirm", "pay", "yes", "authorize", "go ahead"]
                
                if not any(keyword in original_message.lower() for keyword in payment_keywords):
                    logger.warning(f"Blocked unauthorized payment attempt for user {user_id}")
                    tool_call.args = {"error": "Payment attempt blocked. Must get explicit confirmation first."}
    
    def _is_payment_confirmation(self, message: str) -> bool:
        """
        Check if a message is confirming a payment.
        
        Args:
            message: User message
            
        Returns:
            True if message is confirming payment, False otherwise
        """
        confirmation_phrases = [
            "confirm payment", "proceed with payment", "yes proceed", 
            "go ahead", "pay now", "confirm", "proceed", "pay", "yes"
        ]
        
        message_lower = message.lower()
        
        for phrase in confirmation_phrases:
            if phrase in message_lower:
                return True
        
        return False
    
    def _extract_and_store_phone_number(self, message: str, user_id: str) -> None:
        """
        Extract and store the user's phone number from a message.
        
        Args:
            message: User message
            user_id: Unique identifier for the user
        """
        # Look for phone numbers in the message
        kenyan_phone_pattern = r'(?:254|\+254|0)([17]\d{8})'
        matches = re.findall(kenyan_phone_pattern, message)
        
        if matches:
            # Format properly for M-Pesa (should start with 254)
            phone = matches[0]
            if phone.startswith("0"):
                phone = "254" + phone[1:]
            elif not phone.startswith("254"):
                phone = "254" + phone
            
            # Store in user session
            self.user_sessions[user_id]["phone_number"] = phone
            logger.info(f"Stored phone number {phone} for user {user_id}")
        # Fallback to the older pattern-matching logic
        elif "my phone number is" in message.lower() or "use this number" in message.lower():
            parts = message.split()
            for part in parts:
                # Look for something that could be a phone number
                if part.isdigit() and len(part) >= 9:
                    # Format properly for M-Pesa (should start with 254)
                    phone = part
                    if phone.startswith("0"):
                        phone = "254" + phone[1:]
                    elif phone.startswith("+254"):
                        phone = phone[1:]
                    elif not phone.startswith("254"):
                        phone = "254" + phone
                    
                    # Store in user session
                    self.user_sessions[user_id]["phone_number"] = phone
                    logger.info(f"Stored phone number {phone} for user {user_id}")
                    break
    
    def clear_user_memory(self, user_id: str) -> None:
        """
        Clear memory for a specific user.
        
        Args:
            user_id: Unique identifier for the user
        """
        self.memory_handler.clear_memory(user_id)
        
        # Also remove from agent_executors cache if present
        if user_id in self.agent_executors:
            del self.agent_executors[user_id]
        
        # Clear user session data
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]