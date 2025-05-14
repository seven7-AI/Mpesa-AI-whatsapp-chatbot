import requests
import json
import time
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class AirtableMetadataClient:
    """Client for interacting with Airtable Metadata API to create table structures."""
    
    BASE_URL = "https://api.airtable.com/v0/meta"
    
    def __init__(self, personal_access_token=None):
        """Initialize the Airtable Metadata client."""
        # Use provided token or get from environment
        self.token = personal_access_token or os.getenv("AIRTABLE_TOKEN")
        
        if not self.token:
            raise ValueError("No Airtable token provided. Set AIRTABLE_TOKEN environment variable.")
            
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        logger.info("Airtable Metadata client initialized")
    
    def create_base(self, name):
        """Create a new base."""
        url = f"{self.BASE_URL}/bases"
        
        # First, get list of workspaces to use the first available one
        workspaces_url = f"{self.BASE_URL}/workspaces"
        try:
            workspaces_response = requests.get(workspaces_url, headers=self.headers)
            workspaces_response.raise_for_status()
            
            workspaces = workspaces_response.json().get("workspaces", [])
            if not workspaces:
                raise Exception("No workspaces found for this account")
            
            # Use the first workspace
            workspace_id = workspaces[0]["id"]
            logger.info(f"Using workspace ID: {workspace_id}")
            
            # Now create the base with the specific workspace ID
            payload = {
                "name": name,
                "workspaceId": workspace_id
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            base_id = response.json()["id"]
            logger.info(f"Created base '{name}' with ID: {base_id}")
            return base_id
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create base: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise Exception(f"Failed to create base: {str(e)}")
    
    def create_table(self, base_id, name, description=""):
        """Create a new table in the specified base."""
        url = f"{self.BASE_URL}/bases/{base_id}/tables"
        payload = {
            "name": name,
            "description": description
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            table_id = response.json()["id"]
            logger.info(f"Created table '{name}' with ID: {table_id}")
            return table_id
        else:
            logger.error(f"Failed to create table: {response.text}")
            raise Exception(f"Failed to create table: {response.text}")
    
    def create_field(self, base_id, table_id, name, field_type, options=None):
        """Create a new field in the specified table."""
        url = f"{self.BASE_URL}/bases/{base_id}/tables/{table_id}/fields"
        
        payload = {
            "name": name,
            "type": field_type
        }
        
        if options:
            payload["options"] = options
            
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            field_id = response.json()["id"]
            logger.info(f"Created field '{name}' with ID: {field_id}")
            return field_id
        else:
            logger.error(f"Failed to create field: {response.text}")
            raise Exception(f"Failed to create field: {response.text}")
    
    def create_view(self, base_id, table_id, name, filter_formula=None):
        """Create a new view in the specified table."""
        url = f"{self.BASE_URL}/bases/{base_id}/tables/{table_id}/views"
        
        payload = {
            "name": name,
            "type": "grid"
        }
        
        if filter_formula:
            payload["filterFormula"] = filter_formula
            
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            view_id = response.json()["id"]
            logger.info(f"Created view '{name}' with ID: {view_id}")
            return view_id
        else:
            logger.error(f"Failed to create view: {response.text}")
            raise Exception(f"Failed to create view: {response.text}")

def create_telecom_product_base(client=None):
    """Create a complete telecom product base with all tables and fields."""
    # If no client is provided, create one using the environment token
    if client is None:
        token = os.getenv("AIRTABLE_TOKEN")
        if not token:
            raise ValueError("No Airtable token provided. Set AIRTABLE_TOKEN environment variable.")
        client = AirtableMetadataClient(token)
    
    # Create the base
    base_id = client.create_base("Telecom Products")
    
    # Create Products table
    products_table_id = client.create_table(
        base_id, 
        "Products", 
        "All telecom products including data bundles, minutes, and airtime"
    )
    
    # Create fields for Products table
    client.create_field(base_id, products_table_id, "Name", "singleLineText")
    
    # Type field with options
    type_options = {
        "choices": [
            {"name": "Data", "color": "blue"},
            {"name": "Minutes", "color": "green"},
            {"name": "Airtime", "color": "orange"}
        ]
    }
    client.create_field(base_id, products_table_id, "Type", "singleSelect", type_options)
    
    # Price field
    client.create_field(base_id, products_table_id, "Price", "number", {"precision": 2})
    
    # Validity fields
    validity_options = {
        "choices": [
            {"name": "Hourly", "color": "yellow"},
            {"name": "Daily", "color": "orange"},
            {"name": "Weekly", "color": "red"},
            {"name": "Monthly", "color": "purple"}
        ]
    }
    client.create_field(base_id, products_table_id, "Validity", "singleSelect", validity_options)
    client.create_field(base_id, products_table_id, "ValidityDuration", "number")
    
    # Description field
    client.create_field(base_id, products_table_id, "Description", "multilineText")
    
    # Keywords field
    keywords_options = {
        "choices": [
            {"name": "Weekend", "color": "blue"},
            {"name": "Night", "color": "black"},
            {"name": "Unlimited", "color": "green"},
            {"name": "Budget", "color": "yellow"},
            {"name": "Premium", "color": "red"}
        ]
    }
    client.create_field(base_id, products_table_id, "Keywords", "multipleSelects", keywords_options)
    
    # IsActive field
    client.create_field(base_id, products_table_id, "IsActive", "checkbox")
    
    # SortOrder field
    client.create_field(base_id, products_table_id, "SortOrder", "number")
    
    # Create formula field for search optimization
    search_tags_options = {
        "formula": "CONCATENATE({Name}, ' ', {Type}, ' ', {Validity}, ' ', {Keywords})"
    }
    client.create_field(base_id, products_table_id, "SearchTags", "formula", search_tags_options)
    
    # Create views for Products table
    client.create_view(
        base_id, 
        products_table_id, 
        "Active Data Products", 
        "AND({Type}='Data',{IsActive}=1)"
    )
    
    client.create_view(
        base_id, 
        products_table_id, 
        "Active Minutes Products", 
        "AND({Type}='Minutes',{IsActive}=1)"
    )
    
    # Create Pricing Tiers table
    pricing_table_id = client.create_table(
        base_id,
        "Pricing Tiers",
        "Price ranges for different product tiers"
    )
    
    # Create fields for Pricing Tiers table
    tier_options = {
        "choices": [
            {"name": "Budget", "color": "yellow"},
            {"name": "Standard", "color": "blue"},
            {"name": "Premium", "color": "red"}
        ]
    }
    client.create_field(base_id, pricing_table_id, "PriceTier", "singleSelect", tier_options)
    client.create_field(base_id, pricing_table_id, "MinPrice", "number")
    client.create_field(base_id, pricing_table_id, "MaxPrice", "number")
    client.create_field(base_id, pricing_table_id, "ProductType", "singleSelect", type_options)
    
    logger.info(f"Successfully created Telecom Products base with ID: {base_id}")
    return base_id

# Usage
if __name__ == "__main__":
    try:
        # Use token from environment variable
        token = os.getenv("AIRTABLE_TOKEN")
        if not token:
            raise ValueError("AIRTABLE_TOKEN environment variable is not set")
            
        base_id = create_telecom_product_base(AirtableMetadataClient(token))
        print(f"Base created successfully with ID: {base_id}")
        print("Now you can populate the tables with your product data")
    except Exception as e:
        print(f"Error: {str(e)}")