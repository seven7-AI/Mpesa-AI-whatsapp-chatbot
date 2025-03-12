from langchain.tools import BaseTool
from datetime import datetime
import base64
from pydantic import BaseModel, Field
from typing import Optional, Type, ClassVar
from src.config.env import MPESA_PASSKEY, MPESA_CALLBACK_URL 
from src.config.constants import PROCESS_REQUEST_URL, TRANSACTION_TYPE_BUY_GOODS
import requests

class TillPaymentInput(BaseModel):
    amount: float = Field(description="The amount to be paid")
    phone_number: str = Field(description="The customer's phone number (e.g., '2547XXXXXXXX')")
    short_code: str = Field(description="The Till Number (short code) to receive the payment")
    account_reference: str = Field(description="Reference for the transaction, e.g., order ID")

class TillPaymentOutput(BaseModel):
    checkout_request_id: Optional[str] = Field(description="ID for the initiated STK Push request")
    response_code: Optional[str] = Field(description="Response code from Mpesa (e.g., '0' for success)")
    error_message: Optional[str] = Field(description="Error message if the request fails")

class TillAgent(BaseTool):
    name: ClassVar[str] = "initiate_till_payment"
    description: ClassVar[str] = "Initiates an Mpesa Till payment (Buy Goods) using STK Push."
    args_schema: Type[BaseModel] = TillPaymentInput

    def _run(self, amount: float, phone_number: str, short_code: str, account_reference: str, access_token: str) -> TillPaymentOutput:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode((short_code + MPESA_PASSKEY + timestamp).encode()).decode()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "BusinessShortCode": short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": TRANSACTION_TYPE_BUY_GOODS,
            "Amount": str(amount),
            "PartyA": phone_number,
            "PartyB": short_code,
            "PhoneNumber": phone_number,
            "CallBackURL": MPESA_CALLBACK_URL,
            "AccountReference": account_reference,
            "TransactionDesc": "Till Payment"
        }
        try:
            response = requests.post(PROCESS_REQUEST_URL, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            checkout_request_id = response_data.get("CheckoutRequestID")
            response_code = response_data.get("ResponseCode")
            if response_code == "0":
                return TillPaymentOutput(checkout_request_id=checkout_request_id, response_code=response_code, error_message=None)
            else:
                return TillPaymentOutput(checkout_request_id=None, response_code=response_code, error_message=f"STK Push failed. Response Code: {response_code}")
        except requests.exceptions.RequestException as e:
            return TillPaymentOutput(checkout_request_id=None, response_code=None, error_message=f"Error during STK Push: {str(e)}")

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented for TillAgent yet.")