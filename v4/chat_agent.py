"""
Chat Agent with M-Pesa and Search Tools

This module implements the main chat agent that uses the M-Pesa integration
and Google Search tools to interact with users.
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

# Import our custom tools
from mpesa_tool import get_mpesa_tool
from search_tool import get_search_tool

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
    """Chat agent that uses M-Pesa and Search tools."""
    
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
        """Initialize the LangChain agent with tools."""
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
            
            # Initialize tools
            self.tools = self._get_tools()
            
            # Create system message
            system_message = """
            You are a helpful assistant that can process payments via M-Pesa and search the web for information.
            
            For M-Pesa payments, you can use either Till or Paybill payment methods.
            - Till payments are for direct merchant payments
            - Paybill payments require an account reference for reconciliation
            
            When a user wants to make a payment:
            1. Ask for their phone number (format: 2547XXXXXXXX)
            2. Ask for the amount they want to pay
            3. For Paybill payments, ask for an account reference (e.g., invoice number)
            4. Confirm the details before initiating the payment
            
            You can also search the web for information when users ask questions.
            
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
                memory_key="chat_history",
                return_messages=True
            )
            
            # Create agent
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
    
    def _get_tools(self) -> List[BaseTool]:
        """Get the tools for the agent."""
        tools = []
        
        # Add M-Pesa tools
        try:
            till_tool = get_mpesa_tool("till")
            paybill_tool = get_mpesa_tool("paybill")
            tools.extend([till_tool, paybill_tool])
            logger.info("M-Pesa tools added successfully.")
        except Exception as e:
            logger.warning(f"Failed to add M-Pesa tools: {e}")
        
        # Add Search tool
        try:
            search_tool = get_search_tool()
            tools.append(search_tool)
            logger.info("Search tool added successfully.")
        except Exception as e:
            logger.warning(f"Failed to add Search tool: {e}")
        
        return tools
    
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
            response = self.agent_executor.invoke({"input": message})
            logger.info(f"Agent response: {response['output']}")
            return response["output"]
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.exception(error_msg)
            return f"I'm sorry, I encountered an error: {str(e)}"
    
    def add_tool(self, tool: BaseTool) -> None:
        """
        Add a new tool to the agent.
        
        Args:
            tool: The tool to add
        """
        try:
            self.tools.append(tool)
            
            # Reinitialize the agent with the updated tools
            agent = create_openai_tools_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=self.agent_executor.agent.prompt
            )
            
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                handle_parsing_errors=True
            )
            
            logger.info(f"Added new tool: {tool.name}")
        except Exception as e:
            logger.error(f"Failed to add tool: {e}")
            raise
