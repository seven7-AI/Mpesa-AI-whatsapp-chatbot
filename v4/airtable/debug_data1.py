"""
Diagnostic script to debug Airtable Data1 insertion issues
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

BASE_ID = "app8EacwvVAxYo2WX"  # Use your base ID
TOKEN = os.getenv("AIRTABLE_TOKEN")
TABLE_NAME = "Data1"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Define a simplified sample record - with minimal fields first
simple_record = {
    "Name": "Test Product",
    "Description": "Test description",
    "Price": 100,
    "Type": "Data"
}

# Try inserting just this simple record
url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
payload = {"records": [{"fields": simple_record}]}

try:
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        logger.info("Simple record added successfully!")
        
        # If successful, delete it to keep the table clean
        record_id = response.json()["records"][0]["id"]
        delete_url = f"{url}/{record_id}"
        requests.delete(delete_url, headers=headers)
    else:
        logger.error(f"Error: {response.status_code}")
        logger.error(f"Response: {response.text}")
except Exception as e:
    logger.error(f"Exception: {e}")

# Now try one complete sample record from your original data
sample_data_bundle = {
    "Name": "Daily Data 100MB",
    "Type": "Data",
    "Price": 20,
    "Validity": "Daily",
    "ValidityDuration": 1,
    "Description": "100MB data valid for 24 hours",
    "Keywords": "Budget",  # Changed from list to string
    "IsActive": True,
    "SortOrder": 1
}

logger.info("Trying to add complete sample record...")
payload = {"records": [{"fields": sample_data_bundle}]}

try:
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        logger.info("Complete record added successfully!")
        
        # If successful, delete it to keep the table clean
        record_id = response.json()["records"][0]["id"]
        delete_url = f"{url}/{record_id}"
        requests.delete(delete_url, headers=headers)
    else:
        logger.error(f"Error: {response.status_code}")
        logger.error(f"Response: {response.text}")
        
        # Parse the error for more details
        try:
            error_info = response.json()
            if "error" in error_info:
                logger.error(f"Error message: {error_info['error'].get('message')}")
                if "errors" in error_info["error"]:
                    for i, error in enumerate(error_info["error"]["errors"]):
                        logger.error(f"Detailed error {i+1}: {json.dumps(error, indent=2)}")
        except:
            logger.error("Could not parse error response")
except Exception as e:
    logger.error(f"Exception: {e}")

# If we reach here, try fields one by one
logger.info("\n--- Testing individual fields ---")
all_fields = {
    "Name": "Test Individual Fields",
    "Type": "Data",
    "Price": 20,
    "Validity": "Daily",
    "ValidityDuration": 1,
    "Description": "Testing each field",
    "Keywords": "Budget",
    "IsActive": True,
    "SortOrder": 1
}

# Test each field individually
for field_name, field_value in all_fields.items():
    test_record = {"Name": "Test Record"}  # Name is required
    if field_name != "Name":
        test_record[field_name] = field_value
    
    logger.info(f"Testing field: {field_name} = {field_value}")
    payload = {"records": [{"fields": test_record}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            logger.info(f"Field {field_name} is OK")
            
            # Delete the test record
            record_id = response.json()["records"][0]["id"]
            delete_url = f"{url}/{record_id}"
            requests.delete(delete_url, headers=headers)
        else:
            logger.error(f"Field {field_name} caused an error: {response.status_code}")
            logger.error(f"Response: {response.text}")
    except Exception as e:
        logger.error(f"Exception testing field {field_name}: {e}") 