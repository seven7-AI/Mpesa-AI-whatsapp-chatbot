"""
Google Search Tool for Chat Agent

This module implements the Google Search tool for the chat agent,
allowing it to search the web for information.
"""

import os
import logging
from typing import Dict, Any, List, Optional
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
    """Input for Google Search."""
    query: str = Field(..., description="The search query to look up")
    num_results: int = Field(default=5, description="Number of search results to return")

class GoogleSearchTool(BaseTool):
    """Tool for searching the web using Google Search API."""
    name: str = "google_search"
    description: str = "Search the web for information using Google Search API"
    args_schema: type[GoogleSearchInput] = GoogleSearchInput
    
    def __init__(self):
        """Initialize the Google Search tool."""
        super().__init__()
        self._initialize_search_client()
        
    def _initialize_search_client(self) -> None:
        """Initialize the Google Search client."""
        try:
            # Check for required API key
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                error_msg = "Missing GOOGLE_API_KEY environment variable"
                logger.error(error_msg)
                raise EnvironmentError(error_msg)
            
            # Import the necessary libraries
            try:
                from googleapiclient.discovery import build
                self.service = build("customsearch", "v1", developerKey=api_key)
                
                # Check for Custom Search Engine ID
                self.cse_id = os.getenv("GOOGLE_CSE_ID")
                if not self.cse_id:
                    error_msg = "Missing GOOGLE_CSE_ID environment variable"
                    logger.error(error_msg)
                    raise EnvironmentError(error_msg)
                
                logger.info("Google Search API client initialized successfully.")
            except ImportError:
                # Fall back to SerpAPI if Google API client is not available
                try:
                    from serpapi import GoogleSearch
                    serpapi_key = os.getenv("SERPAPI_API_KEY")
                    if not serpapi_key:
                        error_msg = "Missing SERPAPI_API_KEY environment variable"
                        logger.error(error_msg)
                        raise EnvironmentError(error_msg)
                    
                    self.use_serpapi = True
                    self.serpapi_key = serpapi_key
                    logger.info("SerpAPI client initialized as fallback.")
                except ImportError:
                    error_msg = "Neither Google API client nor SerpAPI is available"
                    logger.error(error_msg)
                    raise ImportError(error_msg)
        except Exception as e:
            logger.error(f"Failed to initialize search client: {e}")
            raise
    
    def _run(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Run the Google Search tool."""
        try:
            logger.info(f"Searching for: {query}")
            
            if hasattr(self, 'use_serpapi') and self.use_serpapi:
                return self._search_with_serpapi(query, num_results)
            else:
                return self._search_with_google_api(query, num_results)
            
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            logger.exception(error_msg)
            return {"status": "error", "message": error_msg}
    
    def _search_with_google_api(self, query: str, num_results: int) -> Dict[str, Any]:
        """Search using Google Custom Search API."""
        try:
            result = self.service.cse().list(q=query, cx=self.cse_id, num=num_results).execute()
            
            search_results = []
            if "items" in result:
                for item in result["items"]:
                    search_results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    })
            
            return {
                "status": "success",
                "query": query,
                "results": search_results
            }
        except Exception as e:
            logger.exception(f"Google API search failed: {str(e)}")
            raise
    
    def _search_with_serpapi(self, query: str, num_results: int) -> Dict[str, Any]:
        """Search using SerpAPI as a fallback."""
        try:
            from serpapi import GoogleSearch
            
            search_params = {
                "q": query,
                "api_key": self.serpapi_key,
                "num": num_results
            }
            
            search = GoogleSearch(search_params)
            result = search.get_dict()
            
            search_results = []
            if "organic_results" in result:
                for item in result["organic_results"][:num_results]:
                    search_results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    })
            
            return {
                "status": "success",
                "query": query,
                "results": search_results
            }
        except Exception as e:
            logger.exception(f"SerpAPI search failed: {str(e)}")
            raise

# Factory function to get the search tool
def get_search_tool() -> BaseTool:
    """
    Get the Google Search tool.
    
    Returns:
        BaseTool: The Google Search tool
    """
    return GoogleSearchTool()
