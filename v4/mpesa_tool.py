"""
M-Pesa Till Payment Tool for Chat Agent

This module implements the M-Pesa Till payment tool for the chat agent.
"""

import os
import logging
import traceback
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
import requests

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
    error_msg = "Failed to import M-Pesa integration module"
    logger.error(f"{error_msg}. Trace: {traceback.format_exc()}")
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
            logger.error("M-Pesa module not available. Install the mpesa_integration package.")
            raise ImportError("M-Pesa module not available. Install the mpesa_integration package.")
            
        try:
            # Get environment variables
            consumer_key = os.getenv("MPESA_CONSUMER_KEY")
            consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")
            till_number = os.getenv("MPESA_SHORTCODE")
            passkey = os.getenv("MPESA_PASSKEY")
            callback_url = os.getenv("MPESA_CALLBACK_URL")
            environment = os.getenv("MPESA_ENVIRONMENT", "sandbox")
            
            logger.info(f"Initializing M-Pesa client with configuration:")
            logger.info(f"- Consumer Key: {'*' * (len(consumer_key or '') - 4) + (consumer_key or '')[-4:] if consumer_key else 'Not set'}")
            logger.info(f"- Till Number: {till_number or 'Not set'}")
            logger.info(f"- Callback URL: {callback_url or 'Not set'}")
            logger.info(f"- Environment: {environment}")
            
            # Check for required environment variables
            missing_vars = []
            if not consumer_key:
                missing_vars.append("MPESA_CONSUMER_KEY")
            if not consumer_secret:
                missing_vars.append("MPESA_CONSUMER_SECRET")
            if not till_number:
                missing_vars.append("MPESA_TILL_NUMBER")
            if not passkey:
                missing_vars.append("MPESA_PASSKEY")
            if not callback_url:
                missing_vars.append("MPESA_CALLBACK_URL")
            
            if missing_vars:
                error_msg = f"Missing required M-Pesa environment variables: {', '.join(missing_vars)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Inspect the MpesaConfig class signature to see available params
            try:
                import inspect
                config_params = inspect.signature(MpesaConfig.__init__).parameters
                logger.info(f"MpesaConfig accepts these parameters: {list(config_params.keys())}")
            except Exception as e:
                logger.warning(f"Could not inspect MpesaConfig parameters: {e}")
            
            # Configure M-Pesa client - using the most compatible parameters
            try:
                # Try with environment parameter if available in signature
                if 'environment' in inspect.signature(MpesaConfig.__init__).parameters:
                    logger.info("Using 'environment' parameter for MpesaConfig")
                    config = MpesaConfig(
                        consumer_key=consumer_key,
                        consumer_secret=consumer_secret,
                        shortcode=till_number,
                        passkey=passkey,
                        callback_url=callback_url,
                        environment=environment
                    )
                else:
                    # Try without environment parameter
                    logger.info("Using basic parameters for MpesaConfig (no environment)")
                    config = MpesaConfig(
                        consumer_key=consumer_key,
                        consumer_secret=consumer_secret,
                        shortcode=till_number,
                        passkey=passkey,
                        callback_url=callback_url
                    )
            except TypeError as e:
                logger.warning(f"Failed with original parameters: {e}")
                # Try with a more compatible set of parameters
                logger.info("Trying with minimal parameters for MpesaConfig")
                config = MpesaConfig(
                    consumer_key=consumer_key,
                    consumer_secret=consumer_secret,
                    shortcode=till_number,
                    passkey=passkey
                )
                
                # If we get here, it worked with minimal params
                if callback_url:
                    logger.info("Adding callback_url separately if possible")
                    if hasattr(config, 'callback_url'):
                        config.callback_url = callback_url
            
            self.client = MpesaClient(config)
            
            # Set environment explicitly if the client supports it
            if hasattr(self.client, 'environment') and environment:
                logger.info(f"Setting environment on client: {environment}")
                self.client.environment = environment
                
            logger.info(f"M-Pesa client initialized successfully for {environment} environment.")
            
        except Exception as e:
            error_msg = f"Failed to initialize M-Pesa client: {e}"
            logger.error(f"{error_msg}\nTraceback: {traceback.format_exc()}")
            raise RuntimeError(error_msg)
    
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
            
            # Format phone number if needed
            if phone_number.startswith("+"):
                phone_number = phone_number[1:]
            if phone_number.startswith("0"):
                phone_number = "254" + phone_number[1:]
            
            logger.info(f"Formatted phone number: {phone_number}")
            
            # Default values for Till payments
            account_reference = "Payment"
            transaction_desc = "M-Pesa Payment"
            
            logger.info(f"Calling M-Pesa API with parameters:")
            logger.info(f"- Phone: {phone_number}")
            logger.info(f"- Amount: {amount}")
            logger.info(f"- Account Reference: {account_reference}")
            logger.info(f"- Transaction Description: {transaction_desc}")
            
            # List available methods on the client
            available_methods = [method for method in dir(self.client) if not method.startswith('_') and callable(getattr(self.client, method))]
            logger.info(f"Available methods on MpesaClient: {available_methods}")
            
            # Use initiate_payment since that's what the logs show as available
            try:
                logger.info("Calling initiate_payment with standard parameters")
                response = self.client.initiate_payment(
                    phone_number=phone_number,
                    amount=amount,
                    account_reference=account_reference,
                    transaction_desc=transaction_desc,
                    transaction_type="CustomerBuyGoodsOnline"  # Till payment type
                )
            except Exception as e1:
                logger.warning(f"Error with standard initiate_payment call: {e1}")
                
                # Try with fewer parameters
                try:
                    logger.info("Trying simplified initiate_payment call")
                    response = self.client.initiate_payment(
                        phone_number=phone_number,
                        amount=amount
                    )
                except Exception as e2:
                    logger.warning(f"Simplified call also failed: {e2}")
                    
                    # Try with different argument names
                    try:
                        logger.info("Trying alternative parameter names")
                        response = self.client.initiate_payment(
                            phone=phone_number,
                            amount=amount
                        )
                    except Exception as e3:
                        logger.warning(f"Alternative parameter names failed: {e3}")
                        
                        # If all else failed, raise the original error
                        logger.error(f"All attempts failed. Original error: {e1}")
                        raise e1
            
            logger.info(f"Payment request response: {response}")
            
            # Try to adapt to different response formats
            success = False
            message = "Unknown status"
            checkout_id = None
            
            # Check for common response patterns
            if isinstance(response, dict):
                if "ResponseCode" in response and response.get("ResponseCode") == "0":
                    success = True
                    message = "Payment initiated successfully. Please check your phone to complete the transaction."
                    checkout_id = response.get("CheckoutRequestID")
                elif "errorCode" in response and response.get("errorCode") == "0":
                    success = True 
                    message = "Payment initiated successfully. Please check your phone to complete the transaction."
                    checkout_id = response.get("requestId")
                else:
                    # Look for any success indicator
                    for key in response:
                        if key.lower().endswith('code') and (response[key] == "0" or response[key] == 0):
                            success = True
                            message = "Payment initiated successfully. Please check your phone to complete the transaction."
                            # Look for any ID field
                            for id_key in response:
                                if 'id' in id_key.lower():
                                    checkout_id = response[id_key]
                                    break
                            break
            
            if success:
                success_msg = f"Payment initiated successfully. Checkout ID: {checkout_id}"
                logger.info(success_msg)
                return {
                    "success": True,
                    "message": message,
                    "checkout_request_id": checkout_id,
                    "response_details": response
                }
            else:
                # Try to extract error message
                error_msg = "Failed to initiate payment"
                if isinstance(response, dict):
                    for key in ["ResponseDescription", "errorMessage", "message", "detail"]:
                        if key in response:
                            error_msg = f"{error_msg}: {response[key]}"
                            break
                
                logger.error(error_msg)
                return {
                    "success": False,
                    "message": error_msg,
                    "response_details": response
                }
                
        except Exception as e:
            error_msg = f"Error initiating payment: {str(e)}"
            logger.exception(error_msg)
            logger.error(f"Detailed traceback: {traceback.format_exc()}")
            return {
                "success": False, 
                "message": error_msg,
                "exception_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }

class MpesaTransactionStatusTool(BaseTool):
    """Tool to check the status of an M-Pesa transaction."""
    
    name = "mpesa_transaction_status"
    description = """Useful for checking the status of an M-Pesa transaction.
    This tool requires a transaction ID (from the initial payment response) to check its status.
    Input should be a JSON string with: {"transaction_id": "NEF61H8J60"} OR {"originator_conversation_id": "AG_20190826_0000777ab7d848b9e721"}
    One of transaction_id or originator_conversation_id must be provided.
    """
    
    def __init__(self):
        """Initialize the M-Pesa Transaction Status Tool."""
        super().__init__()
        self._init_mpesa_client()
    
    def _init_mpesa_client(self):
        """Initialize the M-Pesa client."""
        try:
            # Check for required environment variables
            required_vars = [
                "MPESA_CONSUMER_KEY",
                "MPESA_CONSUMER_SECRET",
                "MPESA_SHORTCODE",
                "MPESA_PASSKEY"
            ]
            
            for var in required_vars:
                if not os.getenv(var):
                    raise EnvironmentError(f"Missing required environment variable: {var}")
            
            # Initialize M-Pesa configuration
            config = MpesaConfig(
                consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
                consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
                shortcode=os.getenv("MPESA_SHORTCODE"),
                passkey=os.getenv("MPESA_PASSKEY"),
                environment=os.getenv("MPESA_ENVIRONMENT", "sandbox")
            )
            
            # Initialize client
            self.client = MpesaClient(config)
            
            # Set URLs for transaction status
            self.result_url = os.getenv("MPESA_STATUS_RESULT_URL", 
                                        os.getenv("MPESA_CALLBACK_URL", "https://example.com/status/result"))
            self.timeout_url = os.getenv("MPESA_STATUS_TIMEOUT_URL", 
                                         os.getenv("MPESA_CALLBACK_URL", "https://example.com/status/timeout"))
            
            logger.info("M-Pesa Transaction Status tool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize M-Pesa Transaction Status tool: {e}")
            raise
    
    def _run(self, query: str) -> str:
        """
        Check the status of an M-Pesa transaction.
        
        Args:
            query: JSON string containing transaction_id or originator_conversation_id
            
        Returns:
            str: Transaction status information
        """
        try:
            # Parse the input JSON
            params = json.loads(query)
            
            transaction_id = params.get("transaction_id")
            originator_conversation_id = params.get("originator_conversation_id")
            
            if not transaction_id and not originator_conversation_id:
                return "Error: Either transaction_id or originator_conversation_id must be provided."
            
            # Prepare transaction status request
            # The initiator name and security credential would typically come from your M-Pesa API account
            # For sandbox testing, you can use the test credentials
            initiator = os.getenv("MPESA_INITIATOR", "testapi")
            security_credential = os.getenv("MPESA_SECURITY_CREDENTIAL", "Safaricom999!*!")
            
            status_request = {
                "Initiator": initiator,
                "SecurityCredential": security_credential,
                "CommandID": "TransactionStatusQuery",
                "PartyA": os.getenv("MPESA_SHORTCODE"),
                "IdentifierType": "4",  # For organization shortcode
                "ResultURL": self.result_url,
                "QueueTimeOutURL": self.timeout_url,
                "Remarks": "Check transaction status",
                "Occasion": "Status check"
            }
            
            # Add either TransactionID or OriginatorConversationID
            if transaction_id:
                status_request["TransactionID"] = transaction_id
            else:
                status_request["OriginatorConversationID"] = originator_conversation_id
            
            # Call the M-Pesa API
            # Note: We need to implement this method in the MpesaClient class
            response = self.client.check_transaction_status(status_request)
            
            # Process the response
            if response.get("ResponseCode") == "0":
                return f"Transaction status check initiated successfully. Response: {json.dumps(response)}"
            else:
                return f"Failed to check transaction status. Response: {json.dumps(response)}"
                
        except json.JSONDecodeError:
            return "Error: Invalid JSON input. Please provide a valid JSON string."
        except Exception as e:
            logger.error(f"Error checking transaction status: {e}")
            return f"Error checking transaction status: {str(e)}"

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
    
    logger.info("Creating M-Pesa Till tool directly...")
    return MpesaTillTool()

# Function to get the transaction status tool
def get_transaction_status_tool() -> MpesaTransactionStatusTool:
    """Get an instance of the M-Pesa Transaction Status tool."""
    return MpesaTransactionStatusTool()

def check_transaction_status(self, status_request: dict) -> dict:
    """
    Check the status of an M-Pesa transaction.
    
    Args:
        status_request: Dictionary with transaction status query parameters
        
    Returns:
        dict: Response from M-Pesa API
    """
    try:
        # Get the access token
        access_token = self._get_access_token()
        
        # Set up the API URL based on environment
        if self.config.environment == "production":
            url = "https://api.safaricom.co.ke/mpesa/transactionstatus/v1/query"
        else:
            url = "https://sandbox.safaricom.co.ke/mpesa/transactionstatus/v1/query"
        
        # Set up headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Make the API request
        response = requests.post(url, json=status_request, headers=headers)
        
        # Parse and return the response
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error checking transaction status: {response.text}")
            return {
                "ResponseCode": "1",
                "ResponseDescription": f"Error: {response.text}",
                "ErrorMessage": response.text
            }
            
    except Exception as e:
        logger.error(f"Exception checking transaction status: {e}")
        return {
            "ResponseCode": "1",
            "ResponseDescription": f"Exception: {str(e)}",
            "ErrorMessage": str(e)
        }
