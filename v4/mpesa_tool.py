"""
M-Pesa Integration Tool for Chat Agent

This module implements the M-Pesa integration tool for the chat agent,
focusing on paybill and till payment transactions.
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from mpesa_integration.mpesa import MpesaClient, MpesaConfig
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

class MpesaPaymentInput(BaseModel):
    """Input for M-Pesa payment transactions."""
    phone_number: str = Field(..., description="Customer phone number in format 2547XXXXXXXX")
    amount: int = Field(..., description="Amount to be paid in KES")
    account_reference: str = Field(..., description="Account reference for the transaction (e.g., invoice number)")
    transaction_desc: str = Field(default="Payment", description="Description of the transaction")
    payment_type: str = Field(..., description="Type of payment: 'till' or 'paybill'")

class MpesaTillTool(BaseTool):
    """Tool for initiating M-Pesa Till payments."""
    name: str = "mpesa_till_payment"
    description: str = "Initiates an M-Pesa payment using Till Number"
    args_schema: type[BaseModel] = MpesaPaymentInput
    
    def __init__(self):
        """Initialize the M-Pesa Till payment tool."""
        super().__init__()
        self._initialize_mpesa_client("till")
        
    def _initialize_mpesa_client(self, payment_type: str) -> None:
        """Initialize the M-Pesa client with appropriate configuration."""
        try:
            # Verify required environment variables
            required_env_vars = [
                "MPESA_CONSUMER_KEY",
                "MPESA_CONSUMER_SECRET",
                "MPESA_PASSKEY",
                "MPESA_SHORTCODE",  # Till Number
                "MPESA_CALLBACK_URL"
            ]
            
            for var in required_env_vars:
                if not os.getenv(var):
                    error_msg = f"Missing environment variable for Till: {var}"
                    logger.error(error_msg)
                    raise EnvironmentError(error_msg)
            
            # Create M-Pesa configuration
            config = MpesaConfig(
                consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
                consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
                shortcode=os.getenv("MPESA_SHORTCODE"),  # Till Number
                passkey=os.getenv("MPESA_PASSKEY"),
                callback_url=os.getenv("MPESA_CALLBACK_URL"),
                environment=os.getenv("MPESA_ENVIRONMENT", "sandbox")
            )
            
            # Initialize M-Pesa client
            self.client = MpesaClient(config)
            logger.info(f"MpesaClient initialized successfully for {payment_type.capitalize()}.")
            
        except Exception as e:
            logger.error(f"Failed to initialize MpesaClient for {payment_type.capitalize()}: {e}")
            raise
    
    def _run(self, phone_number: str, amount: int, account_reference: str, 
             transaction_desc: str = "Payment", payment_type: str = "till") -> Dict[str, Any]:
        """Run the M-Pesa Till payment tool."""
        try:
            logger.info(f"Initiating Till payment: phone={phone_number}, amount={amount}, "
                       f"account_ref={account_reference}")
            
            response = self.client.initiate_payment(
                phone_number=phone_number,
                amount=amount,
                account_reference=account_reference,
                transaction_desc=transaction_desc
            )
            
            logger.info(f"M-Pesa API Response (Till): {response}")
            
            if response.get("ResponseCode") != "0":
                error_msg = f"M-Pesa API Error: {response.get('ResponseDescription')}"
                logger.error(error_msg)
                return {"status": "error", "message": error_msg, "details": response}
            
            return {
                "status": "success",
                "message": "Payment request initiated successfully",
                "details": response
            }
            
        except Exception as e:
            error_msg = f"Till payment initiation failed: {str(e)}"
            logger.exception(error_msg)
            return {"status": "error", "message": error_msg}

class MpesaPaybillTool(BaseTool):
    """Tool for initiating M-Pesa Paybill payments."""
    name: str = "mpesa_paybill_payment"
    description: str = "Initiates an M-Pesa payment using Paybill Number"
    args_schema: type[BaseModel] = MpesaPaymentInput
    
    def __init__(self):
        """Initialize the M-Pesa Paybill payment tool."""
        super().__init__()
        self._initialize_mpesa_client("paybill")
        
    def _initialize_mpesa_client(self, payment_type: str) -> None:
        """Initialize the M-Pesa client with appropriate configuration."""
        try:
            # Verify required environment variables
            required_env_vars = [
                "MPESA_CONSUMER_KEY",
                "MPESA_CONSUMER_SECRET",
                "MPESA_PASSKEY",
                "MPESA_SHORTCODE",  # Paybill Number
                "MPESA_BUSINESS_SHORTCODE",  # Same as SHORTCODE for Paybill
                "MPESA_CALLBACK_URL"
            ]
            
            for var in required_env_vars:
                if not os.getenv(var):
                    error_msg = f"Missing environment variable for Paybill: {var}"
                    logger.error(error_msg)
                    raise EnvironmentError(error_msg)
            
            # Create M-Pesa configuration
            config = MpesaConfig(
                consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
                consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
                shortcode=os.getenv("MPESA_SHORTCODE"),  # Paybill Number
                business_shortcode=os.getenv("MPESA_BUSINESS_SHORTCODE"),  # Same as SHORTCODE
                passkey=os.getenv("MPESA_PASSKEY"),
                callback_url=os.getenv("MPESA_CALLBACK_URL"),
                environment=os.getenv("MPESA_ENVIRONMENT", "sandbox")
            )
            
            # Initialize M-Pesa client
            self.client = MpesaClient(config)
            logger.info(f"MpesaClient initialized successfully for {payment_type.capitalize()}.")
            
        except Exception as e:
            logger.error(f"Failed to initialize MpesaClient for {payment_type.capitalize()}: {e}")
            raise
    
    def _run(self, phone_number: str, amount: int, account_reference: str, 
             transaction_desc: str = "Payment", payment_type: str = "paybill") -> Dict[str, Any]:
        """Run the M-Pesa Paybill payment tool."""
        try:
            logger.info(f"Initiating Paybill payment: phone={phone_number}, amount={amount}, "
                       f"account_ref={account_reference}")
            
            response = self.client.initiate_payment(
                phone_number=phone_number,
                amount=amount,
                account_reference=account_reference,  # Crucial for Paybill reconciliation
                transaction_desc=transaction_desc
            )
            
            logger.info(f"M-Pesa API Response (Paybill): {response}")
            
            if response.get("ResponseCode") != "0":
                error_msg = f"M-Pesa API Error: {response.get('ResponseDescription')}"
                logger.error(error_msg)
                return {"status": "error", "message": error_msg, "details": response}
            
            return {
                "status": "success",
                "message": "Payment request initiated successfully",
                "details": response
            }
            
        except Exception as e:
            error_msg = f"Paybill payment initiation failed: {str(e)}"
            logger.exception(error_msg)
            return {"status": "error", "message": error_msg}

# Factory function to get the appropriate M-Pesa tool
def get_mpesa_tool(payment_type: str) -> BaseTool:
    """
    Get the appropriate M-Pesa tool based on payment type.
    
    Args:
        payment_type: Type of payment ('till' or 'paybill')
        
    Returns:
        BaseTool: The appropriate M-Pesa tool
    """
    if payment_type.lower() == "till":
        return MpesaTillTool()
    elif payment_type.lower() == "paybill":
        return MpesaPaybillTool()
    else:
        raise ValueError(f"Invalid payment type: {payment_type}. Must be 'till' or 'paybill'.")
