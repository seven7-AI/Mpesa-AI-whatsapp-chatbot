"""
Script to set up Select field options in Airtable
"""

import os
import json
import logging
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

BASE_ID = "app8EacwvVAxYo2WX"
TOKEN = os.getenv("AIRTABLE_TOKEN")
TABLE_NAME = "Data1"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Define the valid options for each select field
select_options = {
    "Type": ["Data", "Minutes"],
    "Validity": ["Daily", "Weekly", "Monthly"],
    "Keywords": ["Budget", "Standard", "Premium", "Unlimited", "Night"]
}

# Function to add a record with each option to create the select options
def initialize_select_field(field_name, options):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    
    logger.info(f"Initializing select options for {field_name}...")
    
    for option in options:
        # Create a test record with the option
        test_record = {
            "Name": f"Option Initializer - {field_name}",
            field_name: option if field_name != "Keywords" else [option]
        }
        
        payload = {"records": [{"fields": test_record}]}
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                logger.info(f"Added option '{option}' for {field_name}")
                
                # Delete the test record
                record_id = response.json()["records"][0]["id"]
                delete_url = f"{url}/{record_id}"
                requests.delete(delete_url, headers=headers)
            else:
                logger.error(f"Error adding option '{option}' for {field_name}: {response.status_code}")
                logger.error(f"Response: {response.text}")
        except Exception as e:
            logger.error(f"Exception adding option '{option}' for {field_name}: {e}")

# Initialize each select field with its options
for field_name, options in select_options.items():
    initialize_select_field(field_name, options)

logger.info("Select options initialization complete!") 