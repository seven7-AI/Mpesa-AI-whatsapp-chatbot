"""
WhatsApp Integration for Chat Agent

This module implements the WhatsApp integration for the chat agent
using Twilio's WhatsApp API.
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from pydantic import BaseModel

# Import our chat agent
from chat_agent import ChatAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class WhatsAppIntegration:
    """WhatsApp integration for the chat agent using Twilio."""
    
    def __init__(self, chat_agent: ChatAgent):
        """
        Initialize the WhatsApp integration.
        
        Args:
            chat_agent: The chat agent to use for processing messages
        """
        self.chat_agent = chat_agent
        self._initialize_twilio()
    
    def _initialize_twilio(self) -> None:
        """Initialize the Twilio client."""
        try:
            # Check for required Twilio credentials
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
            
            if not account_sid or not auth_token or not self.whatsapp_number:
                error_msg = "Missing Twilio credentials in environment variables"
                logger.error(error_msg)
                raise EnvironmentError(error_msg)
            
            # Initialize Twilio client
            self.client = Client(account_sid, auth_token)
            self.validator = RequestValidator(auth_token)
            
            logger.info("Twilio client initialized successfully.")
            
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            raise
    
    async def validate_twilio_request(self, request: Request) -> bool:
        """
        Validate that the request is coming from Twilio.
        
        Args:
            request: The incoming request
            
        Returns:
            bool: Whether the request is valid
        """
        try:
            # Get the request URL and headers
            url = str(request.url)
            headers = dict(request.headers)
            signature = headers.get("X-Twilio-Signature", "")
            
            # Get the request body
            body = await request.form()
            
            # Validate the request
            return self.validator.validate(url, dict(body), signature)
            
        except Exception as e:
            logger.error(f"Error validating Twilio request: {e}")
            return False
    
    async def process_whatsapp_message(self, request: Request) -> Dict[str, Any]:
        """
        Process an incoming WhatsApp message.
        
        Args:
            request: The incoming request
            
        Returns:
            Dict[str, Any]: The response to send back
        """
        try:
            # Validate the request
            if not await self.validate_twilio_request(request):
                error_msg = "Invalid Twilio request signature"
                logger.error(error_msg)
                raise HTTPException(status_code=403, detail=error_msg)
            
            # Parse the request
            body = await request.form()
            from_number = body.get("From", "")
            message_body = body.get("Body", "")
            
            logger.info(f"Received WhatsApp message from {from_number}: {message_body}")
            
            # Process the message with the chat agent
            response = self.chat_agent.process_message(message_body)
            
            # Send the response back to the user
            self._send_whatsapp_message(from_number, response)
            
            return {"status": "success", "message": "Message processed successfully"}
            
        except Exception as e:
            error_msg = f"Error processing WhatsApp message: {str(e)}"
            logger.exception(error_msg)
            return {"status": "error", "message": error_msg}
    
    def _send_whatsapp_message(self, to_number: str, message: str) -> None:
        """
        Send a WhatsApp message.
        
        Args:
            to_number: The recipient's phone number
            message: The message to send
        """
        try:
            # Send the message
            self.client.messages.create(
                from_=f"whatsapp:{self.whatsapp_number}",
                body=message,
                to=f"whatsapp:{to_number}"
            )
            
            logger.info(f"Sent WhatsApp message to {to_number}")
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            raise
