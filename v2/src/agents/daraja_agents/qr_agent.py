from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, ClassVar
from src.config.env import MPESA_CALLBACK_URL 
import requests

class DynamicQRInput(BaseModel):
    merchant_name: str = Field(description="Name of the company or M-Pesa merchant")
    amount: float = Field(description="The total amount for the transaction")
    short_code: str = Field(description="The Till Number or short code (CPI) to receive the payment")
    ref_no: str = Field(description="Transaction reference, e.g., invoice number")
    trx_code: str = Field(description="Transaction type (e.g., 'BG' for Buy Goods, 'PB' for Paybill)", regex="^(BG|WA|PB|SM|SB)$")
    size: str = Field(default="300", description="Size of the QR code image in pixels (default: 300)")

class DynamicQROutput(BaseModel):
    qr_code: Optional[str] = Field(description="Base64-encoded QR code image data")
    request_id: Optional[str] = Field(description="ID of the QR code generation request")
    error_message: Optional[str] = Field(description="Error message if the request fails")

class DynamicQRAgent(BaseTool):
    name: ClassVar[str] = "generate_dynamic_qr"
    description: ClassVar[str] = "Generates a dynamic M-Pesa QR code for payments."
    args_schema: Type[BaseModel] = DynamicQRInput

    def _run(self, merchant_name: str, amount: float, short_code: str, ref_no: str, trx_code: str, size: str, access_token: str) -> DynamicQROutput:
        url = "https://sandbox.safaricom.co.ke/mpesa/qrcode/v1/generate"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "MerchantName": merchant_name,
            "RefNo": ref_no,
            "Amount": str(amount),
            "TrxCode": trx_code,
            "CPI": short_code,  # Credit Party Identifier (e.g., Till Number)
            "Size": size
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            qr_code = response_data.get("QRCode")  # Base64-encoded image
            request_id = response_data.get("RequestID")
            if qr_code:
                return DynamicQROutput(qr_code=qr_code, request_id=request_id, error_message=None)
            else:
                return DynamicQROutput(qr_code=None, request_id=None, error_message="QR code generation failed: No QRCode in response")
        except requests.exceptions.RequestException as e:
            return DynamicQROutput(qr_code=None, request_id=None, error_message=f"Error generating QR code: {str(e)}")

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented for DynamicQRAgent yet.")