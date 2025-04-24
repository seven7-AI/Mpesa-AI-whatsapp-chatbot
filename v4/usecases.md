# M-Pesa Integration Usage Examples 🚀

This document provides detailed examples of how to use the `mpesa-integration` package with the FastAPI web framework for both Till and Paybill payments.

## Usage with FastAPI (Till Payment Example)

Below is a complete example of using `mpesa-integration` with FastAPI to initiate Till payments.

### Example Code (Till)

Create a file named `main_till.py`:

```python
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv
# Assuming mpesa-integration package is installed
from mpesa_integration import MpesaClient, MpesaConfig

app = FastAPI(title="M-Pesa Till Payment API")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Verify environment variables for Till
required_env_vars = [
    "MPESA_CONSUMER_KEY",
    "MPESA_CONSUMER_SECRET",
    "MPESA_PASSKEY",
    "MPESA_SHORTCODE", # Till Number
    "MPESA_CALLBACK_URL"
]
for var in required_env_vars:
    env_var_name = "MPESA_CONSUMER_SECRET" if var == "MPESA_CONSUMER_SECRET" else var
    if not os.getenv(env_var_name):
        logger.error(f"Missing environment variable for Till: {env_var_name}")
        raise EnvironmentError(f"Missing environment variable for Till: {env_var_name}")

# M-Pesa configuration for Till payment
try:
    config = MpesaConfig(
        consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
        consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
        shortcode=os.getenv("MPESA_SHORTCODE"), # Your Till Number
        passkey=os.getenv("MPESA_PASSKEY"),
        callback_url=os.getenv("MPESA_CALLBACK_URL"),
        environment=os.getenv("MPESA_ENVIRONMENT", "sandbox")
    )
    logger.info(f"MpesaConfig initialized for Till in environment: {config.environment}")
except Exception as e:
    logger.error(f"Failed to initialize MpesaConfig for Till: {e}")
    raise

# Initialize M-Pesa client
try:
    client = MpesaClient(config)
    logger.info("MpesaClient initialized successfully for Till.")
except Exception as e:
    logger.error(f"Failed to initialize MpesaClient for Till: {e}")
    raise

# Pydantic model for Till request validation
class TillPaymentRequest(BaseModel):
    phone_number: str
    amount: int
    account_reference: str = "TillPayment" # Default or allow override
    transaction_desc: str = "Payment via Till Number" # Default or allow override

@app.post("/initiate_till_payment")
async def initiate_till_payment_endpoint(payment: TillPaymentRequest):
    logger.info(f"Received Till payment request: phone={payment.phone_number}, amount={payment.amount}")
    try:
        response = client.initiate_payment(
            phone_number=payment.phone_number,
            amount=payment.amount,
            account_reference=payment.account_reference,
            transaction_desc=payment.transaction_desc
        )
        logger.info(f"M-Pesa API Response (Till): {response}")
        if response.get("ResponseCode") != "0":
             logger.error(f"M-Pesa API Error (Till): {response.get('ResponseDescription')}")
             raise HTTPException(status_code=400, detail=response.get('CustomerMessage', 'M-Pesa Till request failed'))
        return response
    except Exception as e:
        logger.exception(f"Till payment initiation failed unexpectedly: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/mpesa/callback")
async def mpesa_callback(request: Request):
    try:
        callback_data = await request.json()
        logger.info(f"Received M-Pesa callback: {callback_data}")
        if not isinstance(callback_data, dict) or "Body" not in callback_data:
            logger.error("Invalid callback format received.")
            raise HTTPException(status_code=400, detail="Invalid callback format")
        stk_callback = callback_data.get("Body", {}).get("stkCallback", {})
        if not stk_callback:
             logger.error("Callback data missing 'stkCallback' field.")
             raise HTTPException(status_code=400, detail="Callback data missing 'stkCallback' field")

        merchant_request_id = stk_callback.get("MerchantRequestID")
        checkout_request_id = stk_callback.get("CheckoutRequestID")
        result_code = stk_callback.get("ResultCode")
        result_desc = stk_callback.get("ResultDesc")
        logger.info(f"Callback details: MerchantReqID={merchant_request_id}, CheckoutReqID={checkout_request_id}, ResultCode={result_code}, Desc={result_desc}")

        if result_code == 0:
            logger.info(f"Payment successful for CheckoutRequestID: {checkout_request_id}")
            # Add Till success logic here
        else:
            logger.error(f"Payment failed/cancelled for CheckoutRequestID: {checkout_request_id}. Reason: {result_desc} (Code: {result_code})")
            # Add Till failure logic here
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    except Exception as e:
        logger.exception(f"Callback processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error processing callback")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Till server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
```

### Steps to Run (Till) 🏃‍♀️

1.  **Set up your environment:**
    *   Create a `.env` file with the Till credentials (see `README.md` Configuration section).
    *   Ensure your Till Number is correctly set in `MPESA_SHORTCODE`.
2.  **Install dependencies:**
    ```bash
    pip install mpesa-integration fastapi uvicorn python-dotenv
    ```
3.  **Run the FastAPI server:**
    ```bash
    uvicorn main_till:app --host 0.0.0.0 --port 8000
    ```
4.  **Test the payment endpoint:**
    *   Send a POST request to `http://localhost:8000/initiate_till_payment` with a JSON body:
        ```json
        {
            "phone_number": "2547xxxxxxxx",
            "amount": 1
        }
        ```
    *   Use `curl`, Postman, or the FastAPI Swagger UI (`http://localhost:8000/docs`).
5.  **Handle callbacks:**
    *   Ensure your `MPESA_CALLBACK_URL` is publicly accessible (use ngrok: `ngrok http 8000`). Update `.env` and the Safaricom Developer Portal.
    *   The `/mpesa/callback` endpoint will receive confirmations.

---

## Usage with FastAPI (Paybill Payment Example)

Below is a complete example of using `mpesa-integration` with FastAPI to initiate Paybill payments.

### Example Code (Paybill)

Create a file named `main_paybill.py`:

```python
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv
# Assuming mpesa-integration package is installed
from mpesa_integration import MpesaClient, MpesaConfig

app = FastAPI(title="M-Pesa Paybill Payment API")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Verify environment variables for Paybill
required_env_vars = [
    "MPESA_CONSUMER_KEY",
    "MPESA_CONSUMER_SECRET",
    "MPESA_PASSKEY",
    "MPESA_SHORTCODE", # Paybill Number
    "MPESA_BUSINESS_SHORTCODE", # Paybill Number (same as SHORTCODE)
    "MPESA_CALLBACK_URL"
]
for var in required_env_vars:
    env_var_name = "MPESA_CONSUMER_SECRET" if var == "MPESA_CONSUMER_SECRET" else var
    if not os.getenv(env_var_name):
        logger.error(f"Missing environment variable for Paybill: {env_var_name}")
        raise EnvironmentError(f"Missing environment variable for Paybill: {env_var_name}")

# M-Pesa configuration for Paybill payment
try:
    config = MpesaConfig(
        consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
        consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
        shortcode=os.getenv("MPESA_SHORTCODE"), # Your Paybill Number
        business_shortcode=os.getenv("MPESA_BUSINESS_SHORTCODE"), # Your Paybill Number again
        passkey=os.getenv("MPESA_PASSKEY"),
        callback_url=os.getenv("MPESA_CALLBACK_URL"),
        environment=os.getenv("MPESA_ENVIRONMENT", "sandbox")
    )
    logger.info(f"MpesaConfig initialized for Paybill in environment: {config.environment}")
except Exception as e:
    logger.error(f"Failed to initialize MpesaConfig for Paybill: {e}")
    raise

# Initialize M-Pesa client
try:
    client = MpesaClient(config)
    logger.info("MpesaClient initialized successfully for Paybill.")
except Exception as e:
    logger.error(f"Failed to initialize MpesaClient for Paybill: {e}")
    raise

# Pydantic model for Paybill request validation
class PaybillPaymentRequest(BaseModel):
    phone_number: str
    amount: int
    account_reference: str # e.g., Invoice number, Customer ID
    transaction_desc: str = "Payment via Paybill" # Default or allow override

@app.post("/initiate_paybill_payment")
async def initiate_paybill_payment_endpoint(payment: PaybillPaymentRequest):
    logger.info(f"Received Paybill payment request: phone={payment.phone_number}, amount={payment.amount}, account_ref={payment.account_reference}")
    try:
        response = client.initiate_payment(
            phone_number=payment.phone_number,
            amount=payment.amount,
            account_reference=payment.account_reference, # Crucial for Paybill reconciliation
            transaction_desc=payment.transaction_desc
        )
        logger.info(f"M-Pesa API Response (Paybill): {response}")
        if response.get("ResponseCode") != "0":
             logger.error(f"M-Pesa API Error (Paybill): {response.get('ResponseDescription')}")
             raise HTTPException(status_code=400, detail=response.get('CustomerMessage', 'M-Pesa Paybill request failed'))
        return response
    except Exception as e:
        logger.exception(f"Paybill payment initiation failed unexpectedly: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Callback endpoint can be shared or separate
@app.post("/mpesa/callback")
async def mpesa_callback(request: Request):
    try:
        callback_data = await request.json()
        logger.info(f"Received M-Pesa callback (Paybill): {callback_data}")
        if not isinstance(callback_data, dict) or "Body" not in callback_data:
            logger.error("Invalid callback format received.")
            raise HTTPException(status_code=400, detail="Invalid callback format")
        stk_callback = callback_data.get("Body", {}).get("stkCallback", {})
        if not stk_callback:
             logger.error("Callback data missing 'stkCallback' field.")
             raise HTTPException(status_code=400, detail="Callback data missing 'stkCallback' field")

        merchant_request_id = stk_callback.get("MerchantRequestID")
        checkout_request_id = stk_callback.get("CheckoutRequestID")
        result_code = stk_callback.get("ResultCode")
        result_desc = stk_callback.get("ResultDesc")
        logger.info(f"Callback details: MerchantReqID={merchant_request_id}, CheckoutReqID={checkout_request_id}, ResultCode={result_code}, Desc={result_desc}")

        if result_code == 0:
            logger.info(f"Payment successful for CheckoutRequestID: {checkout_request_id}")
            # Add Paybill success logic (e.g., update invoice status based on account_reference)
        else:
            logger.error(f"Payment failed/cancelled for CheckoutRequestID: {checkout_request_id}. Reason: {result_desc} (Code: {result_code})")
            # Add Paybill failure logic
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    except Exception as e:
        logger.exception(f"Callback processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error processing callback")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001)) # Use a different port maybe
    logger.info(f"Starting Paybill server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
```

### Steps to Run (Paybill) 🏃‍♀️

1.  **Set up your environment:**
    *   Create/Update your `.env` file with the Paybill credentials (see `README.md` Configuration section).
    *   Ensure `MPESA_SHORTCODE` and `MPESA_BUSINESS_SHORTCODE` are set to your Paybill Number.
2.  **Install dependencies:** (If not already done)
    ```bash
    pip install mpesa-integration fastapi uvicorn python-dotenv
    ```
3.  **Run the FastAPI server:**
    ```bash
    uvicorn main_paybill:app --host 0.0.0.0 --port 8001 # Or your chosen port
    ```
4.  **Test the payment endpoint:**
    *   Send a POST request to `http://localhost:8001/initiate_paybill_payment` with a JSON body:
        ```json
        {
            "phone_number": "2547xxxxxxxx",
            "amount": 1,
            "account_reference": "INV12345" // Example Account Reference
        }
        ```
    *   Use `curl`, Postman, or the FastAPI Swagger UI (`http://localhost:8001/docs`).
5.  **Handle callbacks:**
    *   Ensure your `MPESA_CALLBACK_URL` is publicly accessible (use ngrok: `ngrok http 8001`). Update `.env` and the Safaricom Developer Portal.
    *   The `/mpesa/callback` endpoint will receive confirmations.

---

### Common Elements (Response & Callback Handling)

#### Example Response ✅

On successful payment initiation (applies to both Till and Paybill):

```json
{
    "CheckoutRequestID": "ws_CO_XXXXXXXXXXXXXXXXX",
    "ResponseCode": "0",
    "ResponseDescription": "Success. Request accepted for processing",
    "MerchantRequestID": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
    "CustomerMessage": "Success. Request accepted for processing"
}
```

#### Callback Handling 📞

The `/mpesa/callback` endpoint receives payment status updates from M-Pesa. The callback data structure is similar for both Till and Paybill:

*   `ResultCode`: `0` for success, non-zero for failure.
*   `ResultDesc`: Description of the result.
*   `CheckoutRequestID`: Unique ID to match the payment initiation request.
*   `MerchantRequestID`: Your internal request ID.
*   (Optional) `CallbackMetadata`: Contains details like Amount, MpesaReceiptNumber, PhoneNumber, etc., on success.

You should extend the callback handler to:

*   Update your database with payment status. 💾
*   Notify users of payment success or failure. 📧
*   Log transactions for auditing. 📊

Example successful callback payload:

```json
{
    "Body": {
        "stkCallback": {
            "MerchantRequestID": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
            "CheckoutRequestID": "ws_CO_XXXXXXXXXXXXXXXXX",
            "ResultCode": 0,
            "ResultDesc": "The service request is processed successfully.",
            "CallbackMetadata": {
                "Item": [
                    {"Name": "Amount", "Value": 1.00},
                    {"Name": "MpesaReceiptNumber", "Value": "SJKABCDEF1"},
                    {"Name": "TransactionDate", "Value": 20241014123500},
                    {"Name": "PhoneNumber", "Value": 2547xxxxxxxx}
                ]
            }
        }
    }
}
``` 