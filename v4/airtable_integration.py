"""
Airtable Integration for Data and Minutes Bundles

This module provides integration with Airtable to fetch and query data bundles and minutes/airtime offers.
"""

import os
import logging
import requests
from typing import Dict, List, Any, Optional
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

class AirtableClient:
    """Client for interacting with Airtable Data and Minutes Bundles."""
    
    BASE_URL = "https://api.airtable.com/v0"
    
    def __init__(self):
        """Initialize the Airtable client."""
        self.token = os.getenv("AIRTABLE_TOKEN")
        self.base_id = "appAXYewNJiZkGSsB"  # Hardcoded from the API docs
        self.data_bundles_table = "Data Bundles"
        self.minutes_table = "Minutes and Airtime"
        
        if not self.token:
            raise ValueError("AIRTABLE_TOKEN environment variable is not set")
        
        logger.info(f"Airtable client initialized for base {self.base_id}")
    
    def _make_request(self, endpoint: str, method: str = "GET", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the Airtable API.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Request parameters
            
        Returns:
            API response as dictionary
        """
        url = f"{self.BASE_URL}/{self.base_id}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Airtable API request error: {str(e)}")
            raise
    
    # Data Bundles Methods
    
    def search_data_bundles(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for data bundles by query string.
        
        Args:
            query: Search query
            
        Returns:
            List of matching data bundle records
        """
        logger.info(f"Searching data bundles with query: {query}")
        
        # Convert query to lowercase for case-insensitive search
        query = query.lower()
        
        # Get all data bundles
        response = self._make_request(self.data_bundles_table)
        records = response.get("records", [])
        
        # Filter records by query
        matching_records = []
        for record in records:
            fields = record.get("fields", {})
            data_offer = fields.get("Data Offer", "").lower()
            validity = fields.get("Validity Period", "").lower()
            
            if query in data_offer or query in validity:
                matching_records.append(record)
        
        logger.info(f"Found {len(matching_records)} matching data bundles")
        return matching_records
    
    def search_bundles_by_price_range(self, min_price: int, max_price: int) -> List[Dict[str, Any]]:
        """
        Search for data bundles within a price range.
        
        Args:
            min_price: Minimum price in KSh
            max_price: Maximum price in KSh
            
        Returns:
            List of matching data bundle records
        """
        logger.info(f"Searching data bundles in price range: {min_price} - {max_price} KSh")
        
        # Get all data bundles
        response = self._make_request(self.data_bundles_table)
        records = response.get("records", [])
        
        # Filter records by price range
        matching_records = []
        for record in records:
            fields = record.get("fields", {})
            price = fields.get("Price (KSh)", 0)
            
            if min_price <= price <= max_price:
                matching_records.append(record)
        
        logger.info(f"Found {len(matching_records)} data bundles in price range")
        return matching_records
    
    def get_bundle_by_price(self, price: int) -> Optional[Dict[str, Any]]:
        """
        Get a data bundle by its exact price.
        
        Args:
            price: Price in KSh
            
        Returns:
            Data bundle record or None if not found
        """
        logger.info(f"Getting data bundle with price: {price} KSh")
        
        # Get all data bundles
        response = self._make_request(self.data_bundles_table)
        records = response.get("records", [])
        
        # Find record with matching price
        for record in records:
            fields = record.get("fields", {})
            bundle_price = fields.get("Price (KSh)", 0)
            
            if bundle_price == price:
                logger.info(f"Found data bundle with price {price} KSh")
                return record
        
        logger.info(f"No data bundle found with price {price} KSh")
        return None
    
    # Minutes and Airtime Methods
    
    def search_minutes_offers(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for minutes offers by query string.
        
        Args:
            query: Search query
            
        Returns:
            List of matching minutes offer records
        """
        logger.info(f"Searching minutes offers with query: {query}")
        
        # Convert query to lowercase for case-insensitive search
        query = query.lower()
        
        # Get all minutes offers
        response = self._make_request(self.minutes_table)
        records = response.get("records", [])
        
        # Filter records by query
        matching_records = []
        for record in records:
            fields = record.get("fields", {})
            offer_name = fields.get("Offer Name", "").lower()
            validity = fields.get("Validity Period", "").lower()
            
            if query in offer_name or query in validity:
                matching_records.append(record)
        
        logger.info(f"Found {len(matching_records)} matching minutes offers")
        return matching_records
    
    def search_minutes_by_price_range(self, min_price: int, max_price: int) -> List[Dict[str, Any]]:
        """
        Search for minutes offers within a price range.
        
        Args:
            min_price: Minimum price in KSh
            max_price: Maximum price in KSh
            
        Returns:
            List of matching minutes offer records
        """
        logger.info(f"Searching minutes offers in price range: {min_price} - {max_price} KSh")
        
        # Get all minutes offers
        response = self._make_request(self.minutes_table)
        records = response.get("records", [])
        
        # Filter records by price range
        matching_records = []
        for record in records:
            fields = record.get("fields", {})
            price = fields.get("Price in KSh", 0)
            
            if min_price <= price <= max_price:
                matching_records.append(record)
        
        logger.info(f"Found {len(matching_records)} minutes offers in price range")
        return matching_records
    
    def get_minutes_by_price(self, price: int) -> Optional[Dict[str, Any]]:
        """
        Get a minutes offer by its exact price.
        
        Args:
            price: Price in KSh
            
        Returns:
            Minutes offer record or None if not found
        """
        logger.info(f"Getting minutes offer with price: {price} KSh")
        
        # Get all minutes offers
        response = self._make_request(self.minutes_table)
        records = response.get("records", [])
        
        # Find record with matching price
        for record in records:
            fields = record.get("fields", {})
            offer_price = fields.get("Price in KSh", 0)
            
            if offer_price == price:
                logger.info(f"Found minutes offer with price {price} KSh")
                return record
        
        logger.info(f"No minutes offer found with price {price} KSh")
        return None
    
    def format_bundle_for_display(self, bundle: Dict[str, Any]) -> str:
        """
        Format a data bundle record for display to the user.
        
        Args:
            bundle: Data bundle record
            
        Returns:
            Formatted string representation
        """
        fields = bundle.get("fields", {})
        name = fields.get("Data Offer", "Unknown Bundle")
        price = fields.get("Price (KSh)", "N/A")
        validity = fields.get("Validity Period", "N/A")
        
        return f"📱 {name} - KSh {price} ({validity})"
    
    def format_minutes_for_display(self, minutes_offer: Dict[str, Any]) -> str:
        """
        Format a minutes offer record for display to the user.
        
        Args:
            minutes_offer: Minutes offer record
            
        Returns:
            Formatted string representation
        """
        fields = minutes_offer.get("fields", {})
        name = fields.get("Offer Name", "Unknown Offer")
        price = fields.get("Price in KSh", "N/A")
        validity = fields.get("Validity Period", "N/A")
        
        return f"📞 {name} - KSh {price} ({validity})" 