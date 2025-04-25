"""
Chat Agent with M-Pesa Till Payment Tool

This module implements the main chat agent that uses the M-Pesa Till payment tool
to process payments via chat.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.tools import BaseTool
from langchain.schema import SystemMessage

# Import only the till payment tool
from mpesa_tool import get_mpesa_tool, MpesaTillTool

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
    """Chat agent that uses M-Pesa Till payment tool."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.7):
        """
        Initialize the chat agent.
        
        Args:
            model_name: The OpenAI model to use
            temperature: The temperature for model responses
        """
        self.model_name = model_name
        self.temperature = temperature
        self._initialize_agent()
    
    def _initialize_agent(self) -> None:
        """Initialize the LangChain agent with the Till payment tool."""
        try:
            # Check for OpenAI API key
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                error_msg = "Missing OPENAI_API_KEY environment variable"
                logger.error(error_msg)
                raise EnvironmentError(error_msg)
            
            # Initialize the language model
            self.llm = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                api_key=openai_api_key
            )
            
            # Initialize tools - create directly instead of using factory method
            logger.info("Creating M-Pesa Till tool directly...")
            till_tool = MpesaTillTool()
            self.tools = [till_tool]
            logger.info(f"Created tools: {[t.name for t in self.tools]}")
            
            # Create system message
            system_message = """
            You are Seven, a helpful assistant that can process M-Pesa Till payments.

            You can use the mpesa_till_payment tool to initiate payments.
            
            When a user wants to make a payment:
            1. Ask for their phone number (format: 2547XXXXXXXX)
            2. Ask for the amount they want to pay
            3. Use the mpesa_till_payment tool with these parameters
            
            Always be polite, helpful, and concise in your responses.
            """
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=system_message),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])
            
            # Create memory
            self.memory = ConversationBufferMemory(
                return_messages=True,
                memory_key="chat_history"
            )
            
            # Create agent - explicitly log the tools being passed
            logger.info(f"Creating agent with tools: {[t.name for t in self.tools]}")
            agent = create_openai_tools_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # Create agent executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                handle_parsing_errors=True
            )
            
            logger.info("Chat agent initialized successfully.")
            
        except Exception as e:
            logger.error(f"Failed to initialize chat agent: {e}")
            raise
    
    def process_message(self, message: str) -> str:
        """
        Process a message from the user.
        
        Args:
            message: The user's message
            
        Returns:
            str: The agent's response
        """
        try:
            logger.info(f"Processing message: {message}")
            # Log the tools available to the agent
            logger.info(f"Available tools for agent: {[t.name for t in self.tools]}")
            response = self.agent_executor.invoke({"input": message})
            logger.info(f"Agent response: {response['output']}")
            return response["output"]
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.exception(error_msg)
            return f"I'm sorry, I encountered an error: {str(e)}"