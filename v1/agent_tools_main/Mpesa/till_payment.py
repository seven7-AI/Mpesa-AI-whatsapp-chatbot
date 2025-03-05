import requests
from datetime import datetime
import base64
# from access_token import get_access_token, AccessTokenOutput
from pydantic import BaseModel, Field
from typing import Optional



def get_access_token():
    consumer_key = "eiDkD79ICeFRE1FDiHgCbDMiOvXgp3cj"
    consumer_secret = "BfFwVt1uGLt7Mki3"
    access_token_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    headers = {'Content-Type': 'application/json'}
    auth = (consumer_key, consumer_secret)

    try:
        response = requests.get(access_token_url, headers=headers, auth=auth)
        response.raise_for_status()
        result = response.json()
        access_token = result.get('access_token')
        return AccessTokenOutput(access_token=access_token, error_message=None)
    except requests.exceptions.RequestException as e:
        return AccessTokenOutput(access_token=None, error_message=str(e))


class AccessTokenOutput(BaseModel):
    access_token: Optional[str] = Field(description="Generated access token")
    error_message: Optional[str] = Field(description="Error message in case of failure")


class PaymentTillInput(BaseModel):
    amount: float = Field(description="The amount to be paid")
    business_short_code: str = Field(description="The till number to be paid to")
    party_a: str = Field(description="The phone number sending money")
    transaction_type: str = Field(description="Uses 'CustomerBuyGoodsOnline' as transaction_type.")
    account_reference: str = Field(description="Account reference for the transaction")

class PaymentTillOutput(BaseModel):
    checkout_request_id: Optional[str] = Field(description="ID for the initiated initiate payment push request")
    response_code: Optional[str] = Field(description="Response code from the initiate payment push request")
    error_message: Optional[str] = Field(description="Error message in case of failure")


def process_till_payment(amount: float, business_short_code: str, party_a: str, transaction_type: str, account_reference: str):
    
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
            transaction_desc = 'PaymentTill'

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
                response.raise_for_status()  # This will throw an error for non-200 responses
                response_data = response.json()
                checkout_request_id = response_data.get('CheckoutRequestID')
                response_code = response_data.get('ResponseCode')

                if response_code == "0":
                    return PaymentTillOutput(checkout_request_id=checkout_request_id, response_code=response_code, error_message=None)
                else:
                    return PaymentTillOutput(checkout_request_id=None, response_code=None, error_message=f'STK push failed. Response Code: {response_code}')
            except requests.exceptions.RequestException as e:
                return PaymentTillOutput(checkout_request_id=None, response_code=None, error_message=f'Error: {str(e)}')
        else:
            return PaymentTillOutput(checkout_request_id=None, response_code=None, error_message='Access token not found.')
    else:
        return PaymentTillOutput(checkout_request_id=None, response_code=None, error_message='Failed to retrieve access token.')
