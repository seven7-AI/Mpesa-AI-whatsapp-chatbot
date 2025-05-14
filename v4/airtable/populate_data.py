"""
Airtable Data Population Script

This script populates Airtable tables with telecom product data.
It assumes the tables and fields have been manually created.
"""

import os
import csv
import json
import logging
import argparse
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class AirtableDataPopulator:
    """Class to populate Airtable with telecom product data."""
    
    def __init__(self, token=None, base_id=None):
        """Initialize the Airtable data populator."""
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
        logger.info(f"Initialized data populator for base {base_id}")
    
    def check_table_exists(self, table_name):
        """Check if a table exists in the base."""
        url = f"https://api.airtable.com/v0/{self.base_id}/{table_name}"
        try:
            response = requests.get(url, headers=self.headers, params={"maxRecords": 1})
            return response.status_code == 200
        except:
            return False
            
    def clear_table(self, table_name: str) -> bool:
        """Clear all records from a table."""
        url = f"https://api.airtable.com/v0/{self.base_id}/{table_name}"
        
        try:
            # First, get all record IDs
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            records = response.json().get("records", [])
            record_ids = [record["id"] for record in records]
            
            # If no records, we're done
            if not record_ids:
                logger.info(f"No records to delete in {table_name}")
                return True
            
            # Delete records in batches of 10
            batch_size = 10
            for i in range(0, len(record_ids), batch_size):
                batch = record_ids[i:i+batch_size]
                ids_param = "&".join([f"records[]={id}" for id in batch])
                delete_url = f"{url}?{ids_param}"
                
                delete_response = requests.delete(delete_url, headers=self.headers)
                delete_response.raise_for_status()
                
                logger.info(f"Deleted batch of {len(batch)} records from {table_name}")
            
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error clearing table {table_name}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            return False
    
    def format_product_for_airtable(self, product):
        """Format a product record to be compatible with Airtable's field requirements."""
        # Make a copy to avoid modifying the original
        formatted = product.copy()
        
        # For Keywords: ensure it's an array for Multiple Select field
        if "Keywords" in formatted:
            # If it's already a string, convert to array
            if isinstance(formatted["Keywords"], str):
                # Split by comma and strip whitespace
                formatted["Keywords"] = [k.strip() for k in formatted["Keywords"].split(',')]
            # If it's not a list already, make it a list
            elif not isinstance(formatted["Keywords"], list):
                formatted["Keywords"] = [str(formatted["Keywords"])]
        
        # For Validity: ensure it matches predefined options
        if "Validity" in formatted:
            # Normalize to match exact casing of predefined options
            valid_options = ["Daily", "Weekly", "Monthly"]
            for option in valid_options:
                if formatted["Validity"].lower() == option.lower():
                    formatted["Validity"] = option
                    break
        
        return formatted
    
    def populate_products_table(self, products: List[Dict[str, Any]], table_name: str = "Data1"):
        """Populate the Products table with the provided data."""
        if not self.check_table_exists(table_name):
            raise ValueError(f"Table {table_name} doesn't exist. Please create it manually first.")
            
        url = f"https://api.airtable.com/v0/{self.base_id}/{table_name}"
        
        # Prepare records in Airtable format with proper formatting for Airtable compatibility
        records = [{"fields": self.format_product_for_airtable(product)} for product in products]
        
        # Split into batches of 10 (Airtable's limit)
        batch_size = 10
        total_added = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            payload = {"records": batch}
            
            try:
                response = requests.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                
                added = len(response.json().get("records", []))
                total_added += added
                logger.info(f"Added batch of {added} records to {table_name}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error adding batch: {e}")
                if hasattr(e, 'response') and e.response:
                    logger.error(f"Response: {e.response.text}")
                    try:
                        error_detail = response.json()
                        logger.error(f"Detailed error: {json.dumps(error_detail, indent=2)}")
                    except:
                        pass
        
        return total_added
    
    def populate_pricing_tiers(self, pricing_tiers: List[Dict[str, Any]], table_name: str = "Data2"):
        """Populate the Pricing Tiers table with the provided data."""
        if not self.check_table_exists(table_name):
            raise ValueError(f"Table {table_name} doesn't exist. Please create it manually first.")
            
        url = f"https://api.airtable.com/v0/{self.base_id}/{table_name}"
        
        # Prepare records in Airtable format
        records = [{"fields": tier} for tier in pricing_tiers]
        
        # Split into batches of 10 (Airtable's limit)
        batch_size = 10
        total_added = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            payload = {"records": batch}
            
            try:
                response = requests.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                
                added = len(response.json().get("records", []))
                total_added += added
                logger.info(f"Added batch of {added} records to {table_name}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error adding batch: {e}")
                if hasattr(e, 'response') and e.response:
                    logger.error(f"Response: {e.response.text}")
        
        return total_added

def get_sample_data_bundles() -> List[Dict[str, Any]]:
    """Get sample data bundles for testing."""
    return [
        {
            "Name": "Daily Data 100MB",
            "Type": "Data",
            "Price": 20,
            "Validity": "Daily",
            "ValidityDuration": 1,
            "Description": "100MB data valid for 24 hours",
            "Keywords": ["Budget"],
            "IsActive": True,
            "SortOrder": 1
        },
        {
            "Name": "Weekly Data 1GB",
            "Type": "Data",
            "Price": 100,
            "Validity": "Weekly",
            "ValidityDuration": 7,
            "Description": "1GB data valid for 7 days",
            "Keywords": ["Standard"],
            "IsActive": True,
            "SortOrder": 2
        },
        {
            "Name": "Monthly Data 5GB",
            "Type": "Data",
            "Price": 300,
            "Validity": "Monthly",
            "ValidityDuration": 30,
            "Description": "5GB data valid for 30 days",
            "Keywords": ["Standard"],
            "IsActive": True,
            "SortOrder": 3
        },
        {
            "Name": "Monthly Unlimited Data",
            "Type": "Data",
            "Price": 1000,
            "Validity": "Monthly",
            "ValidityDuration": 30,
            "Description": "Unlimited data for 30 days",
            "Keywords": ["Premium", "Unlimited"],
            "IsActive": True,
            "SortOrder": 4
        }
    ]

def get_sample_minutes_offers() -> List[Dict[str, Any]]:
    """Get sample minutes bundles for testing."""
    return [
        {
            "Name": "Daily 50 Minutes",
            "Type": "Minutes",
            "Price": 20,
            "Validity": "Daily",
            "ValidityDuration": 1,
            "Description": "50 minutes valid for 24 hours",
            "Keywords": ["Budget"],
            "IsActive": True,
            "SortOrder": 5
        },
        {
            "Name": "Weekly 300 Minutes",
            "Type": "Minutes",
            "Price": 100,
            "Validity": "Weekly",
            "ValidityDuration": 7,
            "Description": "300 minutes valid for 7 days",
            "Keywords": ["Standard"],
            "IsActive": True,
            "SortOrder": 6
        },
        {
            "Name": "Monthly 1000 Minutes",
            "Type": "Minutes",
            "Price": 250,
            "Validity": "Monthly", 
            "ValidityDuration": 30,
            "Description": "1000 minutes valid for 30 days",
            "Keywords": ["Standard"],
            "IsActive": True,
            "SortOrder": 7
        },
        {
            "Name": "Monthly Unlimited Minutes",
            "Type": "Minutes",
            "Price": 500, 
            "Validity": "Monthly",
            "ValidityDuration": 30,
            "Description": "Unlimited minutes for 30 days",
            "Keywords": ["Premium", "Unlimited"],
            "IsActive": True,
            "SortOrder": 8
        },
        {
            "Name": "Evening Minutes",
            "Type": "Minutes",
            "Price": 30,
            "Validity": "Daily",
            "ValidityDuration": 1,
            "Description": "Unlimited minutes valid from 6pm to 6am",
            "Keywords": ["Night", "Unlimited"],
            "IsActive": True,
            "SortOrder": 9
        }
    ]

def get_sample_pricing_tiers() -> List[Dict[str, Any]]:
    """Get sample pricing tiers for testing."""
    return [
        {
            "Name": "Budget Data",
            "PriceTier": "Budget",
            "MinPrice": 0,
            "MaxPrice": 50,
            "ProductType": "Data"
        },
        {
            "Name": "Standard Data",
            "PriceTier": "Standard",
            "MinPrice": 51,
            "MaxPrice": 300,
            "ProductType": "Data"
        },
        {
            "Name": "Premium Data",
            "PriceTier": "Premium",
            "MinPrice": 301,
            "MaxPrice": 5000,
            "ProductType": "Data"
        },
        {
            "Name": "Budget Minutes",
            "PriceTier": "Budget",
            "MinPrice": 0,
            "MaxPrice": 100,
            "ProductType": "Minutes"
        },
        {
            "Name": "Standard Minutes",
            "PriceTier": "Standard",
            "MinPrice": 101,
            "MaxPrice": 500,
            "ProductType": "Minutes"
        },
        {
            "Name": "Premium Minutes",
            "PriceTier": "Premium",
            "MinPrice": 501,
            "MaxPrice": 5000,
            "ProductType": "Minutes"
        }
    ]

def load_products_from_csv(csv_path: str) -> List[Dict[str, Any]]:
    """Load product data from a CSV file."""
    products = []
    
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert numeric fields
                if 'Price' in row:
                    row['Price'] = float(row['Price'])
                if 'ValidityDuration' in row:
                    row['ValidityDuration'] = int(row['ValidityDuration'])
                if 'SortOrder' in row:
                    row['SortOrder'] = int(row['SortOrder'])
                
                # Convert IsActive to boolean
                if 'IsActive' in row:
                    row['IsActive'] = row['IsActive'].lower() == 'true'
                
                # Convert Keywords to list
                if 'Keywords' in row:
                    row['Keywords'] = [k.strip() for k in row['Keywords'].split(',')]
                    
                products.append(row)
                
        logger.info(f"Loaded {len(products)} products from {csv_path}")
        return products
    except Exception as e:
        logger.error(f"Error loading products from CSV: {e}")
        return []

def main():
    """Main function for populating Airtable with sample data."""
    parser = argparse.ArgumentParser(description="Populate Airtable with telecom product data")
    parser.add_argument("--token", help="Airtable API token (defaults to AIRTABLE_TOKEN env var)")
    parser.add_argument("--base-id", required=True, help="Airtable base ID")
    parser.add_argument("--data-csv", help="CSV file with data products")
    parser.add_argument("--minutes-csv", help="CSV file with minutes products")
    parser.add_argument("--clear", action="store_true", help="Clear tables before populating")
    parser.add_argument("--sample", action="store_true", help="Use sample data")
    parser.add_argument("--data-table", default="Data1", help="Table name for products (default: Data1)")
    parser.add_argument("--pricing-table", default="Data2", help="Table name for pricing tiers (default: Data2)")
    args = parser.parse_args()
    
    # Get token from arguments or environment
    token = args.token or os.getenv("AIRTABLE_TOKEN")
    if not token:
        logger.error("No Airtable token provided. Set AIRTABLE_TOKEN environment variable.")
        return
    
    # Initialize populator
    populator = AirtableDataPopulator(token, args.base_id)
    
    # Check if tables exist
    if not populator.check_table_exists(args.data_table):
        logger.error(f"Table {args.data_table} doesn't exist. Please create it manually first.")
        print("\nPlease run: python v4/airtable/manual_setup_instructions.py")
        return
        
    if not populator.check_table_exists(args.pricing_table):
        logger.error(f"Table {args.pricing_table} doesn't exist. Please create it manually first.")
        print("\nPlease run: python v4/airtable/manual_setup_instructions.py")
        return
    
    # Clear tables if requested
    if args.clear:
        logger.info("Clearing existing data...")
        populator.clear_table(args.data_table)
        populator.clear_table(args.pricing_table)
    
    # Determine data sources
    data_products = []
    minutes_products = []
    
    if args.sample:
        # Use sample data
        data_products = get_sample_data_bundles()
        minutes_products = get_sample_minutes_offers()
        pricing_tiers = get_sample_pricing_tiers()
    else:
        # Load from CSV files if provided
        if args.data_csv:
            data_products = load_products_from_csv(args.data_csv)
        else:
            data_products = get_sample_data_bundles()
            
        if args.minutes_csv:
            minutes_products = load_products_from_csv(args.minutes_csv)
        else:
            minutes_products = get_sample_minutes_offers()
        
        pricing_tiers = get_sample_pricing_tiers()
    
    # Populate tables
    all_products = data_products + minutes_products
    logger.info(f"Populating {args.data_table} table with {len(all_products)} records...")
    populator.populate_products_table(all_products, args.data_table)
    
    logger.info(f"Populating {args.pricing_table} table with {len(pricing_tiers)} records...")
    populator.populate_pricing_tiers(pricing_tiers, args.pricing_table)
    
    logger.info("Data population complete!")

if __name__ == "__main__":
    main()
