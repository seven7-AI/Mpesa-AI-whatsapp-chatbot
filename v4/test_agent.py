"""
Test script for M-Pesa Chat Agent

This script tests the functionality of the M-Pesa Chat Agent system.
"""

import os
import logging
import json
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_chat_agent():
    """Test the chat agent directly."""
    try:
        from chat_agent import ChatAgent
        
        logger.info("Testing chat agent...")
        
        # Initialize chat agent
        chat_agent = ChatAgent()
        
        # Test general conversation
        test_messages = [
            "Hello, how are you?",
            "What can you help me with?",
            "Tell me about M-Pesa payments"
        ]
        
        for message in test_messages:
            logger.info(f"Test message: {message}")
            response = chat_agent.process_message(message)
            logger.info(f"Response: {response}")
            
        logger.info("Chat agent test completed successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Error testing chat agent: {e}")
        return False

def test_web_api():
    """Test the FastAPI web API."""
    try:
        logger.info("Testing web API...")
        
        # Start the server in a separate process
        import subprocess
        import time
        
        server_process = subprocess.Popen(
            ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        time.sleep(5)
        
        # Test health endpoint
        health_response = requests.get("http://localhost:8000/health")
        logger.info(f"Health check response: {health_response.json()}")
        
        # Test chat endpoint
        chat_data = {
            "message": "Hello, I'd like to know more about M-Pesa payments",
            "user_id": "test_user_123"
        }
        
        chat_response = requests.post(
            "http://localhost:8000/chat",
            json=chat_data
        )
        
        logger.info(f"Chat response: {chat_response.json()}")
        
        # Stop the server
        server_process.terminate()
        server_process.wait()
        
        logger.info("Web API test completed successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Error testing web API: {e}")
        # Make sure to terminate the server process if it exists
        if 'server_process' in locals():
            server_process.terminate()
            server_process.wait()
        return False

def test_mpesa_tool_initialization():
    """Test the initialization of M-Pesa tools."""
    try:
        from mpesa_tool import get_mpesa_tool
        
        logger.info("Testing M-Pesa tool initialization...")
        
        # Check if environment variables are set
        required_env_vars = [
            "MPESA_CONSUMER_KEY",
            "MPESA_CONSUMER_SECRET",
            "MPESA_PASSKEY",
            "MPESA_SHORTCODE",
            "MPESA_CALLBACK_URL"
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning(f"Missing environment variables for M-Pesa: {missing_vars}")
            logger.info("Skipping M-Pesa tool initialization test.")
            return True
        
        # Try to initialize the tools
        try:
            till_tool = get_mpesa_tool("till")
            logger.info("Till tool initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing Till tool: {e}")
            return False
        
        try:
            paybill_tool = get_mpesa_tool("paybill")
            logger.info("Paybill tool initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing Paybill tool: {e}")
            return False
        
        logger.info("M-Pesa tool initialization test completed successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Error testing M-Pesa tool initialization: {e}")
        return False

def test_search_tool_initialization():
    """Test the initialization of Search tool."""
    try:
        from search_tool import get_search_tool
        
        logger.info("Testing Search tool initialization...")
        
        # Check if environment variables are set
        if not os.getenv("GOOGLE_API_KEY") and not os.getenv("SERPAPI_API_KEY"):
            logger.warning("Missing API keys for search. Skipping Search tool initialization test.")
            return True
        
        # Try to initialize the tool
        try:
            search_tool = get_search_tool()
            logger.info("Search tool initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing Search tool: {e}")
            return False
        
        logger.info("Search tool initialization test completed successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Error testing Search tool initialization: {e}")
        return False

def run_all_tests():
    """Run all tests."""
    logger.info("Starting tests for M-Pesa Chat Agent...")
    
    test_results = {
        "chat_agent": test_chat_agent(),
        "mpesa_tool": test_mpesa_tool_initialization(),
        "search_tool": test_search_tool_initialization(),
        "web_api": test_web_api()
    }
    
    logger.info(f"Test results: {test_results}")
    
    if all(test_results.values()):
        logger.info("All tests passed successfully!")
    else:
        logger.warning("Some tests failed. Check the logs for details.")
    
    return test_results

if __name__ == "__main__":
    run_all_tests()
