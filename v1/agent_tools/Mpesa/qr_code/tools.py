import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import base64
from agent_tools.Mpesa.acess_token.tools import get_access_token, AccessTokenOutput

load_dotenv()

   
class QrCodeInput(BaseModel):
    merchant_name: str = Field(description="Name of the Company/M-Pesa Merchant Name")
    ref_no: str = Field(description="Transaction Reference")
    amount: float = Field(description="The total amount for the sale/transaction")
    trx_code: str = Field(description="Transaction Type", enum=["BG", "WA", "PB", "SM", "SB"])
    cpi: str = Field(description="Credit Party Identifier. Can be a Mobile Number, Business Number, Agent Till, Paybill or Business number, or Merchant Buy Goods")
    size: str = Field(description="Size of the QR code image in pixels. QR code image will always be a square image")


class QrCodeOutput(BaseModel):
    response_code: str = Field(description="Used to return the Transaction Type")
    request_id: str = Field(description="An alpha-numeric string of fewer than 20 characters")
    response_description: str = Field(description="This is a response describing the status of the transaction")
    qr_code: str = Field(description="QR Code Image/Data/String")

def generate_dynamic_qr(data):
    access_token_response = get_access_token()
    if 'access_token' in access_token_response:
        access_token = access_token_response['access_token']
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        dynamic_qr_url = 'https://sandbox.safaricom.co.ke/mpesa/qrcode/v1/generate'
        response = requests.post(dynamic_qr_url, json=data, headers=headers)
        # Check if the request was successful
        if response.status_code == 200:
            # Encode the image data as base64
            image_data = base64.b64encode(response.content).decode('utf-8')
            # Return the base64 encoded image data
            return image_data
        else:
            # Handle the error
            return f"Failed to generate QR code: {response.status_code}"
    else:
        return access_token_response

class QrCodeTool(BaseTool):
    name = "generate_dynamic_qr"
    description = "Tool for generating dynamic QR code"
    args_schema = QrCodeInput
    result_schema = QrCodeOutput

    def _run(self, data: QrCodeInput):
        image_data = generate_dynamic_qr(data)
        return image_data