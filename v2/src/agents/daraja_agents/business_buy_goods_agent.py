from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, ClassVar
from src.config.env import MPESA_INITIATOR_USERNAME, MPESA_SECURITY_CREDENTIAL, MPESA_CALLBACK_URL
import requests

class BusinessBuyGoodsInput(BaseModel):
    amount: float = Field(description="The amount to pay")
    sender_short_code: str = Field(description="Your business shortcode (PartyA)")
    receiver_short_code: str = Field(description="The Till Number or merchant shortcode to receive the payment (PartyB)")
    account_reference: str = Field(description="Reference for the transaction, up to 13 characters")
    remarks: str = Field(description="Additional info for the transaction, up to 100 characters")
    requester_phone: Optional[str] = Field(default=None, description="Optional consumer phone number on whose behalf payment is made")

class BusinessBuyGoodsOutput(BaseModel):
    transaction_id: Optional[str] = Field(description="ID of the B2B transaction")
    result_code: Optional[str] = Field(description="Result code from Mpesa (e.g., '0' for success)")
    error_message: Optional[str] = Field(description="Error message if the request fails")

class BusinessBuyGoodsAgent(BaseTool):
    name: ClassVar[str] = "initiate_business_buy_goods"
    description: ClassVar[str] = "Initiates an Mpesa B2B payment to a Till Number or merchant for goods/services."
    args_schema: Type[BaseModel] = BusinessBuyGoodsInput

    def _run(self, amount: float, sender_short_code: str, receiver_short_code: str, account_reference: str, remarks: str, requester_phone: Optional[str], access_token: str) -> BusinessBuyGoodsOutput:
        url = "https://sandbox.safaricom.co.ke/mpesa/b2b/v1/paymentrequest"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "Initiator": MPESA_INITIATOR_USERNAME,
            "SecurityCredential": MPESA_SECURITY_CREDENTIAL,
            "CommandID": "BusinessBuyGoods",
            "SenderIdentifierType": "4",  # Shortcode type
            "ReceiverIdentifierType": "4",  # Till/Merchant shortcode type
            "Amount": str(amount),
            "PartyA": requester_phone,
            "PartyB": receiver_short_code,
            "AccountReference": account_reference,
            "Remarks": remarks,
            "QueueTimeOutURL": f"{MPESA_CALLBACK_URL}/queue",
            "ResultURL": f"{MPESA_CALLBACK_URL}/result"
        }
        if requester_phone:
            payload["Requester"] = requester_phone

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            transaction_id = response_data.get("TransactionID")
            result_code = response_data.get("ResultCode")
            if result_code == "0":
                return BusinessBuyGoodsOutput(transaction_id=transaction_id, result_code=result_code, error_message=None)
            else:
                return BusinessBuyGoodsOutput(transaction_id=None, result_code=result_code, error_message=f"B2B payment failed. Result Code: {result_code}")
        except requests.exceptions.RequestException as e:
            return BusinessBuyGoodsOutput(transaction_id=None, result_code=None, error_message=f"Error during B2B request: {str(e)}")

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented for BusinessBuyGoodsAgent yet.")