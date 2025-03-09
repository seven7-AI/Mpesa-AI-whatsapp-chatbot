# API Endpoints
PROCESS_REQUEST_URL_SANDBOX = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
PROCESS_REQUEST_URL_PRODUCTION = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

# Use sandbox by default for testing; switch to production when ready
PROCESS_REQUEST_URL = PROCESS_REQUEST_URL_SANDBOX

# Transaction Types for Mpesa Daraja API
TRANSACTION_TYPE_BUY_GOODS = "CustomerBuyGoodsOnline"  # For Till Number payments (Buy Goods)
TRANSACTION_TYPE_PAYBILL = "CustomerPayBillOnline"    # For Paybill payments
TRANSACTION_TYPE_B2C = "BusinessPayment"              # Business to Customer (e.g., send money)
TRANSACTION_TYPE_SALARY = "SalaryPayment"             # Salary payments
TRANSACTION_TYPE_PROMOTION = "PromotionPayment"       # Promotional payments