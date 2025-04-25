"""
M-Pesa Till Payment Tool for Chat Agent

This module implements the M-Pesa Till payment tool for the chat agent.
"""

import os
import logging
from typing import Dict, Any, Optional
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

# Import the real M-Pesa integration
try:
    from mpesa_integration.mpesa import MpesaClient, MpesaConfig
    logger.info("Successfully imported M-Pesa integration module")
    HAS_MPESA_MODULE = True
except ImportError:
    logger.error("Failed to import M-Pesa integration module")
    HAS_MPESA_MODULE = False

class MpesaPaymentInput(BaseModel):
    """Input for M-Pesa Till payment transactions."""
    phone_number: str = Field(..., description="Customer phone number in format 2547XXXXXXXX")
    amount: int = Field(..., description="Amount to be paid in KES")

class MpesaTillTool(BaseTool):
    """Tool for initiating M-Pesa Till payments."""
    name: str = "mpesa_till_payment"
    description: str = "Initiates an M-Pesa payment using Till Number"
    args_schema: type[BaseModel] = MpesaPaymentInput
    
    # Add this field to fix the error
    client: Optional[Any] = None
    is_demo_mode: bool = False
    
    def __init__(self):
        """Initialize the M-Pesa Till payment tool."""
        super().__init__()
        self._initialize_mpesa_client()
    
    def _initialize_mpesa_client(self) -> None:
        """Initialize the M-Pesa client for Till payments."""
        if not HAS_MPESA_MODULE:
            logger.warning("M-Pesa module not available, running in demo mode")
            self.is_demo_mode = True
            self.client = None
            return
            
        try:
            # Get environment variables
            consumer_key = os.getenv("MPESA_CONSUMER_KEY")
            consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")
            till_number = os.getenv("MPESA_TILL_NUMBER")
            passkey = os.getenv("MPESA_PASSKEY")
            callback_url = os.getenv("MPESA_CALLBACK_URL", "https://example.com/callback")
            
            # Check for required environment variables
            if not all([consumer_key, consumer_secret, till_number, passkey]):
                logger.warning("Missing required M-Pesa environment variables, running in demo mode")
                self.is_demo_mode = True
                self.client = None
                return
            
            # Configure M-Pesa client
            config = MpesaConfig(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                shortcode=till_number,  # Use shortcode parameter
                passkey=passkey,
                callback_url=callback_url,
                env="sandbox"  # Use sandbox by default
            )
            
            self.client = MpesaClient(config)
            logger.info("M-Pesa client initialized successfully.")
            
        except Exception as e:
            error_msg = f"Failed to initialize M-Pesa client: {e}"
            logger.error(error_msg)
            self.is_demo_mode = True
            self.client = None
    
    def _run(self, phone_number: str, amount: int) -> Dict[str, Any]:
        """
        Run the M-Pesa Till payment tool.
        
        Args:
            phone_number: The customer's phone number
            amount: The amount to be paid
            
        Returns:
            Dict[str, Any]: The payment response
        """
        try:
            logger.info(f"Initiating Till payment of KES {amount} from {phone_number}")
            
            if self.is_demo_mode or not self.client:
                logger.warning("Running in demo mode - simulating payment")
                return {
                    "success": True,
                    "message": "[DEMO MODE] Payment would be initiated in production. In demo mode, no actual payment is processed. Please check your phone to complete the transaction.",
                    "checkout_request_id": "demo-checkout-id-123"
                }
            
            # Default values for Till payments
            account_reference = "Test"
            transaction_desc = "Payment"
            
            # Initiate the payment
            response = self.client.initiate_stk_push(
                phone_number=phone_number,
                amount=amount,
                account_reference=account_reference,
                transaction_desc=transaction_desc,
                transaction_type="CustomerBuyGoodsOnline"  # Till payment type
            )
            
            logger.info(f"Payment request response: {response}")
            
            if response.get("ResponseCode") == "0":
                return {
                    "success": True,
                    "message": "Payment initiated successfully. Please check your phone to complete the transaction.",
                    "checkout_request_id": response.get("CheckoutRequestID")
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to initiate payment: {response.get('ResponseDescription', 'Unknown error')}",
                    "response_code": response.get("ResponseCode")
                }
                
        except Exception as e:
            error_msg = f"Error initiating payment: {e}"
            logger.exception(error_msg)
            return {"success": False, "message": error_msg}

# Factory function to get the M-Pesa Till tool
def get_mpesa_tool(payment_type: str = "till") -> BaseTool:
    """
    Get the M-Pesa Till tool.
    
    Args:
        payment_type: Type of payment (only 'till' is supported)
        
    Returns:
        BaseTool: The M-Pesa Till tool
    """
    if payment_type.lower() != "till":
        logger.warning(f"Unsupported payment type: {payment_type}. Only 'till' is supported.")
        
    return MpesaTillTool()
