import requests
from datetime import datetime
import base64
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from agent_tools.Mpesa.acess_token.tools import get_access_token, AccessTokenOutput

load_dotenv()


class PaymentPaybillInput(BaseModel):
    amount: float = Field(description="The amount to be paid to the paybill account number")
    business_short_code: str = Field(description="The account number to be paid to")
    transaction_type: str = Field(description=" Uses 'CustomerPayBillOnline' as transaction type.")
    account_reference: str = Field(description="Account reference for the transaction")

class PaymentPaybillOutput(BaseModel):
    checkout_request_id: Optional[str] = Field(description="ID for the initiated initiate payment push request")
    response_code: Optional[str] = Field(description="Response code from the initiate payment push request")
    error_message: Optional[str] = Field(description="Error message in case of failure")

def initiate_paybill_payment(amount: float, business_short_code: str, transaction_type: str, account_reference: str):
    access_token_response = get_access_token()

    if isinstance(access_token_response, AccessTokenOutput):
        access_token = access_token_response.access_token
        if access_token:
            process_request_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
            callback_url = 'http://yourcustomurl.local/'
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
            password = base64.b64encode((str(business_short_code) + passkey + timestamp).encode()).decode()
            party_b = business_short_code
            transaction_desc = 'PaymentTill test'
            party_a = '254719321423'

            stk_push_headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + access_token
            }

            stk_push_payload = {
                'BusinessShortCode': business_short_code,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': transaction_type,
                'Amount': amount,
                'PartyA': party_a,
                'PartyB': party_b,
                'PhoneNumber': party_a,
                'CallBackURL': callback_url,
                'AccountReference': account_reference,
                'TransactionDesc': transaction_desc
            }

            try:
                response = requests.post(process_request_url, headers=stk_push_headers, json=stk_push_payload)
                response.raise_for_status()
                response_data = response.json()
                checkout_request_id = response_data.get('CheckoutRequestID')
                response_code = response_data.get('ResponseCode')

                if response_code == "0":
                    return PaymentPaybillOutput(checkout_request_id=checkout_request_id, response_code=response_code, error_message=None)
                else:
                    return PaymentPaybillOutput(checkout_request_id=None, response_code=None, error_message=f'STK push failed. Response Code: {response_code}')
            except requests.exceptions.RequestException as e:
                return PaymentPaybillOutput(checkout_request_id=None, response_code=None, error_message=f'Error: {str(e)}')
        else:
            return PaymentPaybillOutput(checkout_request_id=None, response_code=None, error_message='Access token not found.')
    else:
        return PaymentPaybillOutput(checkout_request_id=None, response_code=None, error_message='Failed to retrieve access token.')
    
class PaymentPaybillTool(BaseTool):
    name = "initiate_payment"
    description = "Use this to initiate a paybill payment: takes ,phone_number, amount, account number/business_short_code and account reference as parameters"
    args_schema: Type[BaseModel] = PaymentPaybillInput

    def _run(self, amount: float, business_short_code: str, transaction_type: str, account_reference: str):
        return initiate_paybill_payment(amount, business_short_code, transaction_type, account_reference)
    