"""
Alternative Airtable Table Creator

This module uses the standard Airtable API to create and configure tables.
Use this if you don't have access to the Metadata API.
"""

import os
import requests
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class AirtableStandardClient:
    """Client for interacting with standard Airtable API to create and populate tables."""
    
    BASE_URL = "https://api.airtable.com/v0"
    
    def __init__(self, personal_access_token=None, base_id=None):
        """Initialize the Airtable client."""
        self.token = personal_access_token or os.getenv("AIRTABLE_TOKEN")
        
        if not self.token:
            raise ValueError("No Airtable token provided. Set AIRTABLE_TOKEN environment variable.")
        
        self.base_id = base_id
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        logger.info("Airtable client initialized")
    
    def check_connection(self):
        """Check if the connection to Airtable works by attempting to get table list."""
        if not self.base_id:
            logger.error("No base ID provided. Please create a base manually and provide its ID.")
            return False
        
        # Airtable API now requires a specific API endpoint that lists tables
        # For regular API, we'll try to access a known table name
        url = f"https://api.airtable.com/v0/meta/bases/{self.base_id}/tables"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                logger.info("Connection to Airtable successful!")
                return True
            elif response.status_code == 404:
                # If metadata API isn't available, try an alternative approach
                logger.info("Metadata API not available, trying alternative method")
                
                # Try to create a test table to verify access
                test_url = f"{self.BASE_URL}/{self.base_id}/Test Table"
                test_payload = {"records": [{"fields": {"Name": "Test"}}]}
                
                test_response = requests.post(test_url, headers=self.headers, json=test_payload)
                
                if test_response.status_code in [200, 201, 422]:  # 422 means table/field exists already
                    logger.info("Connection to Airtable successful via alternative method!")
                    return True
                else:
                    logger.error(f"Failed to connect to Airtable: {test_response.status_code}")
                    logger.error(f"Response: {test_response.text}")
                    return False
            else:
                logger.error(f"Failed to connect to Airtable: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Airtable: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            return False
    
    def create_products_table(self, table_name="Products"):
        """Create the Products table with initial fields."""
        # In the standard API, tables are created when you first add records to them
        url = f"{self.BASE_URL}/{self.base_id}/{table_name}"
        
        # Create sample record to initialize the table with our fields
        sample_record = {
            "fields": {
                "Name": "Sample Product (Delete Me)",
                "Type": "Data",
                "Price": 0,
                "Validity": "Daily",
                "ValidityDuration": 1,
                "Description": "This is a sample product to initialize the table structure",
                "Keywords": ["Sample"],
                "IsActive": False,
                "SortOrder": 999
            }
        }
        
        payload = {"records": [sample_record]}
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"Created {table_name} table with initial structure")
            
            # Get the record ID to delete it later
            record_id = response.json()["records"][0]["id"]
            
            # Delete the sample record
            delete_url = f"{url}/{record_id}"
            delete_response = requests.delete(delete_url, headers=self.headers)
            delete_response.raise_for_status()
            logger.info("Removed sample record")
            
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create table: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            return False
    
    def create_pricing_tiers_table(self, table_name="Pricing Tiers"):
        """Create the Pricing Tiers table with initial fields."""
        url = f"{self.BASE_URL}/{self.base_id}/{table_name}"
        
        # Create sample record to initialize the table with our fields
        sample_record = {
            "fields": {
                "PriceTier": "Sample",
                "MinPrice": 0,
                "MaxPrice": 0,
                "ProductType": "Data"
            }
        }
        
        payload = {"records": [sample_record]}
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"Created {table_name} table with initial structure")
            
            # Get the record ID to delete it later
            record_id = response.json()["records"][0]["id"]
            
            # Delete the sample record
            delete_url = f"{url}/{record_id}"
            delete_response = requests.delete(delete_url, headers=self.headers)
            delete_response.raise_for_status()
            logger.info("Removed sample record")
            
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create table: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            return False

def setup_tables(base_id, token=None):
    """Set up the tables in the provided base."""
    client = AirtableStandardClient(token, base_id)
    
    if not client.check_connection():
        return False
    
    # Create the tables
    products_success = client.create_products_table()
    pricing_success = client.create_pricing_tiers_table()
    
    return products_success and pricing_success

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Set up Airtable tables")
    parser.add_argument("--base-id", required=True, help="Airtable base ID")
    parser.add_argument("--token", help="Airtable API token (defaults to AIRTABLE_TOKEN env var)")
    
    args = parser.parse_args()
    
    token = args.token or os.getenv("AIRTABLE_TOKEN")
    if not token:
        print("No token provided. Set AIRTABLE_TOKEN in .env file or provide --token argument")
        exit(1)
    
    if not args.base_id:
        print("Base ID is required. Create a base manually in Airtable and provide its ID")
        exit(1)
    
    success = setup_tables(args.base_id, token)
    
    if success:
        print(f"Tables created successfully in base {args.base_id}")
        print("You can now run populate_data.py to add records")
    else:
        print("Failed to create tables. Check the logs for details") 