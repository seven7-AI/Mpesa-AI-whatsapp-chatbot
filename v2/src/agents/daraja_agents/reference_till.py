from flask import Flask, request, jsonify
import requests
import base64
from datetime import datetime
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# M-Pesa sandbox URLs and credentials
MPESA_AUTH_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
MPESA_PROCESS_REQUEST_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
BASIC_AUTH = "Basic WGZQdkVSZGtnalZyZnJQYUVHbjVLbVBneG9JVzZHMjZCV2UxNDc1ZTFUZXdHdlBkOkVxc1pXNTM4cTNhWFByMHVOVkdtT2Zqb3BmM05hUGplcG52VUtKZ251RWVHenJaR3BnTUNrb0ZHTEFCQUdZRlc="
SHORTCODE = "174379"
PASSKEY = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
CALLBACK_URL = "https://your-domain.com/api/mpesa/callback"  # Replace with your actual callback URL

def get_access_token():
    try:
        headers = {"Authorization": BASIC_AUTH}
        logger.debug(f"Requesting access token from {MPESA_AUTH_URL}")
        response = requests.get(MPESA_AUTH_URL, headers=headers, timeout=10)
        logger.debug(f"Access token response: {response.status_code} - {response.text}")
        
        if response.status_code != 200:
            raise Exception(f"Failed to get access token: {response.status_code} - {response.text}")
        
        data = response.json()
        if "access_token" not in data:
            raise Exception(f"No access token in response: {response.text}")
        
        logger.info(f"Access token retrieved: {data['access_token']}")
        return data["access_token"]
    except requests.RequestException as e:
        logger.error(f"Network error getting access token: {str(e)}")
        raise Exception(f"Network error getting access token: {str(e)}")
    except ValueError as e:
        logger.error(f"JSON parsing error in access token response: {str(e)}")
        raise Exception(f"Invalid response format: {str(e)}")

def get_timestamp():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    logger.debug(f"Generated timestamp: {timestamp}")
    return timestamp

def generate_password(timestamp):
    password = base64.b64encode(f"{SHORTCODE}{PASSKEY}{timestamp}".encode()).decode('utf-8')
    logger.debug(f"Generated password: {password}")
    return password

@app.route('/initiate_payment', methods=['POST'])
def initiate_payment():
    logger.info(f"Received request: {request.method} {request.path}")
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received in request")
            return jsonify({"error": "No JSON data provided"}), 400
        
        phone_number = data.get('phoneNumber')
        amount = data.get('amount')

        logger.debug(f"Request data: phoneNumber={phone_number}, amount={amount}")
        
        if not phone_number or not amount:
            logger.error(f"Missing required fields: phoneNumber={phone_number}, amount={amount}")
            return jsonify({"error": "Missing phoneNumber or amount"}), 400

        access_token = get_access_token()
        timestamp = get_timestamp()
        password = generate_password(timestamp)

        payload = {
            "BusinessShortCode": SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerBuyGoodsOnline",
            "Amount": str(amount),
            "PartyA": phone_number,
            "PartyB": SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": CALLBACK_URL,
            "AccountReference": "ParkingLot",
            "TransactionDesc": "Parking Payment"
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        logger.info(f"Initiating payment with payload: {payload}")
        response = requests.post(MPESA_PROCESS_REQUEST_URL, json=payload, headers=headers, timeout=10)
        logger.debug(f"Payment response: {response.status_code} - {response.text}")

        if response.status_code != 200:
            logger.error(f"Payment failed: {response.status_code} - {response.text}")
            raise Exception(f"Payment failed with status {response.status_code}: {response.text}")

        payment_data = response.json()
        logger.info(f"Payment successful: {payment_data}")
        return jsonify(payment_data)

    except requests.RequestException as e:
        logger.error(f"Network error during payment initiation: {str(e)}")
        return jsonify({"error": f"Network error: {str(e)}"}), 500
    except ValueError as e:
        logger.error(f"JSON parsing error in payment response: {str(e)}")
        return jsonify({"error": f"Invalid response format: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000, debug=True)