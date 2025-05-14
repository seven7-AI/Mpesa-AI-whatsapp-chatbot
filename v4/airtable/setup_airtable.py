"""
Airtable Setup Script

This script sets up Airtable tables with the correct field structure before populating data.
"""

import os
import requests
import logging
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class AirtableSetup:
    """Class to set up Airtable tables with proper fields."""
    
    def __init__(self, token=None, base_id=None):
        """Initialize the Airtable setup."""
        self.token = token or os.getenv("AIRTABLE_TOKEN")
        if not self.token:
            raise ValueError("No Airtable token provided. Set AIRTABLE_TOKEN environment variable.")
        
        if not base_id:
            raise ValueError("Base ID is required.")
            
        self.base_id = base_id
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        logger.info(f"Initialized setup for base {base_id}")
    
    def check_table_exists(self, table_name):
        """Check if a table exists in the base."""
        url = f"https://api.airtable.com/v0/{self.base_id}/{table_name}"
        try:
            response = requests.get(url, headers=self.headers, params={"maxRecords": 1})
            return response.status_code == 200
        except:
            return False
    
    def create_field_in_table(self, table_name, field_name, field_value):
        """Create a field in a table by adding a record with the field."""
        url = f"https://api.airtable.com/v0/{self.base_id}/{table_name}"
        
        # Create a sample record with the field
        sample_record = {
            "fields": {
                field_name: field_value
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json={"records": [sample_record]})
            if response.status_code in [200, 201]:
                logger.info(f"Created field '{field_name}' in table {table_name}")
                
                # Get the record ID to delete it
                record_id = response.json()["records"][0]["id"]
                
                # Delete the sample record
                delete_url = f"{url}/{record_id}"
                requests.delete(delete_url, headers=self.headers)
                
                return True
            else:
                logger.error(f"Failed to create field '{field_name}' in table {table_name}: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error creating field '{field_name}' in table {table_name}: {e}")
            return False
    
    def setup_products_table(self, table_name="Data1"):
        """Set up the Products table with the necessary fields."""
        # Check if table exists
        if not self.check_table_exists(table_name):
            # Create the table with the Name field
            if not self.create_field_in_table(table_name, "Name", "Sample Product"):
                logger.error(f"Could not create table {table_name}")
                return False
        
        # Create all the required fields
        fields = {
            "Type": "Data",
            "Price": 100,
            "Validity": "Daily",
            "ValidityDuration": 1,
            "Description": "Sample description",
            "Keywords": "Sample, Test",
            "IsActive": True,
            "SortOrder": 1
        }
        
        for field_name, field_value in fields.items():
            if not self.create_field_in_table(table_name, field_name, field_value):
                logger.warning(f"Could not create field '{field_name}' in table {table_name}")
        
        logger.info(f"Finished setting up table {table_name}")
        return True
    
    def setup_pricing_tiers_table(self, table_name="Data2"):
        """Set up the Pricing Tiers table with the necessary fields."""
        # Check if table exists
        if not self.check_table_exists(table_name):
            # Create the table with a Name field
            if not self.create_field_in_table(table_name, "Name", "Sample Pricing Tier"):
                logger.error(f"Could not create table {table_name}")
                return False
        
        # Create all the required fields
        fields = {
            "PriceTier": "Budget",
            "MinPrice": 0,
            "MaxPrice": 50,
            "ProductType": "Data"
        }
        
        for field_name, field_value in fields.items():
            if not self.create_field_in_table(table_name, field_name, field_value):
                logger.warning(f"Could not create field '{field_name}' in table {table_name}")
        
        logger.info(f"Finished setting up table {table_name}")
        return True

def main():
    """Main function to set up Airtable tables."""
    parser = argparse.ArgumentParser(description="Set up Airtable tables with the correct fields")
    parser.add_argument("--token", help="Airtable API token (defaults to AIRTABLE_TOKEN env var)")
    parser.add_argument("--base-id", required=True, help="Airtable base ID")
    parser.add_argument("--data-table", default="Data1", help="Table name for products (default: Data1)")
    parser.add_argument("--pricing-table", default="Data2", help="Table name for pricing tiers (default: Data2)")
    args = parser.parse_args()
    
    # Create setup object
    setup = AirtableSetup(args.token, args.base_id)
    
    # Set up tables
    products_success = setup.setup_products_table(args.data_table)
    pricing_success = setup.setup_pricing_tiers_table(args.pricing_table)
    
    if products_success and pricing_success:
        logger.info("Tables set up successfully!")
        logger.info("You can now run populate_data.py to add data to the tables.")
    else:
        logger.error("Failed to set up one or more tables.")

if __name__ == "__main__":
    main() 