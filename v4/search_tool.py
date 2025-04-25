"""
Google Search Tool for Chat Agent

This module implements a Google Search tool that can be used by the chat agent
to search for information on the web.
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class GoogleSearchInput(BaseModel):
    """Input schema for Google Search."""
    query: str = Field(..., description="The search query to look up")
    num_results: int = Field(default=5, description="Number of search results to return")

class GoogleSearchTool(BaseTool):
    """Tool for searching the web using Google Search API."""
    name: str = "google_search"
    description: str = "Search the web for information using Google Search API"
    args_schema: type[GoogleSearchInput] = GoogleSearchInput
    
    # Add field for search client to satisfy Pydantic
    search_client: Optional[Any] = None
    
    def __init__(self):
        """Initialize the Google Search tool."""
        super().__init__()
        self._initialize_search_client()
        
    def _initialize_search_client(self) -> None:
        """Initialize a mock search client since langchain_community is not available."""
        try:
            # First check if we have the API key
            api_key = os.getenv("SERP_API_KEY")
            if not api_key:
                logger.warning("Missing SERP_API_KEY environment variable")
                self.search_client = None
                return
                
            # Try to import the module - if it's not there, we'll use a mock
            try:
                from langchain_community.utilities import SerpAPIWrapper
                self.search_client = SerpAPIWrapper(serpapi_api_key=api_key)
                logger.info("SerpAPI client initialized successfully.")
            except ImportError:
                logger.warning("langchain_community module not available, using mock search implementation")
                self.search_client = None
                
        except Exception as e:
            error_msg = f"Failed to initialize search client: {e}"
            logger.error(error_msg)
            self.search_client = None
    
    def _run(self, query: str, num_results: int = 5) -> str:
        """
        Run the Google Search tool.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            str: Formatted search results
        """
        try:
            logger.info(f"Searching for: {query}")
            
            # Use mock implementation if the real client is not available
            if self.search_client is None:
                return (
                    "Search functionality is currently unavailable. "
                    "To enable web search, please install the 'langchain_community' package with: "
                    "pip install langchain_community"
                )
                
            results = self.search_client.run(query)
            logger.info(f"Search completed successfully, found results")
            return results
            
        except Exception as e:
            error_msg = f"Error during search: {e}"
            logger.error(error_msg)
            return f"Search error: {error_msg}"

# Function to get the search tool instance
def get_search_tool() -> GoogleSearchTool:
    """
    Get an instance of the Google Search tool.
    
    Returns:
        GoogleSearchTool: An instance of the Google Search tool
    """
    return GoogleSearchTool()
