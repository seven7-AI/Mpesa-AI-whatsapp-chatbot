"""
Airtable Tool for Chat Agent

This module implements the Airtable tool for the chat agent.
"""

import logging
from typing import Dict, Any, List, Optional, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from airtable_integration import AirtableClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Data Bundles Search Tools
class BundleSearchInput(BaseModel):
    """Input for searching data bundles."""
    query: str = Field(..., description="Search query for data bundles (e.g., 'daily', 'weekend', 'hourly')")

class PriceRangeSearchInput(BaseModel):
    """Input for searching data bundles by price range."""
    min_price: int = Field(..., description="Minimum price in KSh")
    max_price: int = Field(..., description="Maximum price in KSh")

class GetBundleByPriceInput(BaseModel):
    """Input for getting a bundle by exact price."""
    price: int = Field(..., description="Exact price of the bundle in KSh")

# Minutes and Airtime Search Tools
class MinutesSearchInput(BaseModel):
    """Input for searching minutes offers."""
    query: str = Field(..., description="Search query for minutes offers (e.g., 'unlimited', 'weekend', 'night')")

class MinutesPriceRangeInput(BaseModel):
    """Input for searching minutes offers by price range."""
    min_price: int = Field(..., description="Minimum price in KSh")
    max_price: int = Field(..., description="Maximum price in KSh")

class GetMinutesByPriceInput(BaseModel):
    """Input for getting minutes offer by exact price."""
    price: int = Field(..., description="Exact price of the minutes offer in KSh")

# Data Bundle Tools
class DataBundleSearchTool(BaseTool):
    """Tool for searching data bundles."""
    name: str = "search_data_bundles"
    description: str = "Search for data bundles by keyword (like 'daily', 'weekly', 'monthly', etc.)"
    args_schema: Type[BundleSearchInput] = BundleSearchInput
    client: AirtableClient = None
    
    def __init__(self):
        """Initialize the data bundle search tool."""
        super().__init__()
        self.client = AirtableClient()
    
    def _run(self, query: str) -> str:
        """
        Run the tool to search for data bundles.
        
        Args:
            query: Search query string
            
        Returns:
            Formatted string with matching bundles or error message
        """
        logger.info(f"Searching for data bundles with query: {query}")
        bundles = self.client.search_data_bundles(query)
        
        if not bundles:
            return f"No data bundles found matching '{query}'. Try a different search term like 'daily', 'weekly', or 'monthly'."
        
        result = f"Here are the data bundles matching '{query}':\n\n"
        for bundle in bundles:
            result += self.client.format_bundle_for_display(bundle) + "\n\n"
        
        return result

class PriceRangeSearchTool(BaseTool):
    """Tool for searching data bundles by price range."""
    name: str = "search_bundles_by_price_range"
    description: str = "Search for data bundles within a specific price range"
    args_schema: Type[PriceRangeSearchInput] = PriceRangeSearchInput
    client: AirtableClient = None
    
    def __init__(self):
        """Initialize the price range search tool."""
        super().__init__()
        self.client = AirtableClient()
    
    def _run(self, min_price: int, max_price: int) -> str:
        """
        Run the tool to search for data bundles by price range.
        
        Args:
            min_price: Minimum price in KSh
            max_price: Maximum price in KSh
            
        Returns:
            Formatted string with matching bundles or error message
        """
        logger.info(f"Searching for data bundles in price range: {min_price} - {max_price} KSh")
        bundles = self.client.search_bundles_by_price_range(min_price, max_price)
        
        if not bundles:
            return f"No data bundles found in the price range {min_price} - {max_price} KSh."
        
        result = f"Here are the data bundles in the price range {min_price} - {max_price} KSh:\n\n"
        for bundle in bundles:
            result += self.client.format_bundle_for_display(bundle) + "\n\n"
        
        return result

class GetBundleByPriceTool(BaseTool):
    """Tool for getting a bundle by exact price."""
    name: str = "get_bundle_by_price"
    description: str = "Get a specific data bundle by its exact price"
    args_schema: Type[GetBundleByPriceInput] = GetBundleByPriceInput
    client: AirtableClient = None
    
    def __init__(self):
        """Initialize the get bundle by price tool."""
        super().__init__()
        self.client = AirtableClient()
    
    def _run(self, price: int) -> str:
        """
        Run the tool to get a specific bundle by its price.
        
        Args:
            price: Exact price in KSh
            
        Returns:
            Formatted string with the bundle info or error message
        """
        logger.info(f"Getting bundle with exact price: {price} KSh")
        bundle = self.client.get_bundle_by_price(price)
        
        if not bundle:
            return f"No data bundle found with the exact price of {price} KSh."
        
        return f"Here is the data bundle with price {price} KSh:\n\n" + self.client.format_bundle_for_display(bundle)

# Minutes Tools
class MinutesSearchTool(BaseTool):
    """Tool for searching minutes offers."""
    name: str = "search_minutes_offers"
    description: str = "Search for minutes and airtime offers by keyword (like 'unlimited', 'night', 'weekend', etc.)"
    args_schema: Type[MinutesSearchInput] = MinutesSearchInput
    client: AirtableClient = None
    
    def __init__(self):
        """Initialize the minutes search tool."""
        super().__init__()
        self.client = AirtableClient()
    
    def _run(self, query: str) -> str:
        """
        Run the tool to search for minutes offers.
        
        Args:
            query: Search query string
            
        Returns:
            Formatted string with matching offers or error message
        """
        logger.info(f"Searching for minutes offers with query: {query}")
        offers = self.client.search_minutes_offers(query)
        
        if not offers:
            return f"No minutes offers found matching '{query}'. Try a different search term like 'unlimited', 'night', or 'weekend'."
        
        result = f"Here are the minutes offers matching '{query}':\n\n"
        for offer in offers:
            result += self.client.format_minutes_for_display(offer) + "\n\n"
        
        return result

class MinutesPriceRangeTool(BaseTool):
    """Tool for searching minutes offers by price range."""
    name: str = "search_minutes_by_price_range"
    description: str = "Search for minutes and airtime offers within a specific price range"
    args_schema: Type[MinutesPriceRangeInput] = MinutesPriceRangeInput
    client: AirtableClient = None
    
    def __init__(self):
        """Initialize the minutes price range search tool."""
        super().__init__()
        self.client = AirtableClient()
    
    def _run(self, min_price: int, max_price: int) -> str:
        """
        Run the tool to search for minutes offers by price range.
        
        Args:
            min_price: Minimum price in KSh
            max_price: Maximum price in KSh
            
        Returns:
            Formatted string with matching offers or error message
        """
        logger.info(f"Searching for minutes offers in price range: {min_price} - {max_price} KSh")
        offers = self.client.search_minutes_by_price_range(min_price, max_price)
        
        if not offers:
            return f"No minutes offers found in the price range {min_price} - {max_price} KSh."
        
        result = f"Here are the minutes offers in the price range {min_price} - {max_price} KSh:\n\n"
        for offer in offers:
            result += self.client.format_minutes_for_display(offer) + "\n\n"
        
        return result

class GetMinutesByPriceTool(BaseTool):
    """Tool for getting a minutes offer by exact price."""
    name: str = "get_minutes_by_price"
    description: str = "Get a specific minutes or airtime offer by its exact price"
    args_schema: Type[GetMinutesByPriceInput] = GetMinutesByPriceInput
    client: AirtableClient = None
    
    def __init__(self):
        """Initialize the get minutes by price tool."""
        super().__init__()
        self.client = AirtableClient()
    
    def _run(self, price: int) -> str:
        """
        Run the tool to get a specific minutes offer by its price.
        
        Args:
            price: Exact price in KSh
            
        Returns:
            Formatted string with the offer info or error message
        """
        logger.info(f"Getting minutes offer with exact price: {price} KSh")
        offer = self.client.get_minutes_by_price(price)
        
        if not offer:
            return f"No minutes or airtime offer found with the exact price of {price} KSh."
        
        return f"Here is the minutes offer with price {price} KSh:\n\n" + self.client.format_minutes_for_display(offer)

def get_airtable_tools() -> List[BaseTool]:
    """
    Get all Airtable tools.
    
    Returns:
        List of Airtable tools for the agent
    """
    return [
        # Data bundle tools
        DataBundleSearchTool(),
        PriceRangeSearchTool(),
        GetBundleByPriceTool(),
        # Minutes and airtime tools
        MinutesSearchTool(),
        MinutesPriceRangeTool(),
        GetMinutesByPriceTool()
    ] 