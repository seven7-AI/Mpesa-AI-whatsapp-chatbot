from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import SupabaseVectorStore
from mpesa_integration.mpesa import MpesaClient, MpesaConfig
import json
from datetime import datetime
import redis
from telegram import Update, Bot
from telegram.ext import CommandHandler, MessageHandler, CallbackContext, filters
from telegram.ext import ApplicationBuilder

app = FastAPI(title="M-Pesa Personal Assistant API")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Initialize Redis client
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Initialize OpenAI Embeddings and LangChain
embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
vectorstore = SupabaseVectorStore(supabase, embeddings, table_name="user_interactions")
llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"), temperature=0)
qa = ConversationalRetrievalChain.from_llm(llm, vectorstore.as_retriever())

# M-Pesa configuration
config = MpesaConfig(
    consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
    consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
    shortcode=os.getenv("MPESA_SHORTCODE"),
    business_shortcode=os.getenv("MPESA_BUSINESS_SHORTCODE"),
    passkey=os.getenv("MPESA_PASSKEY"),
    callback_url=os.getenv("MPESA_CALLBACK_URL"),
    environment=os.getenv("MPESA_ENVIRONMENT")
)
client = MpesaClient(config)

# Base prompt for context
base_prompt = """
You are a personal assistant that helps users with various tasks, including initiating M-Pesa payments.
You can handle both Till and Paybill payments. When a user asks to make a payment, ask for the necessary details
such as phone number, amount, account reference, and transaction description. Use the provided information to
initiate the payment through the M-Pesa API.
"""

# Telegram bot token
TELEGRAM_TOKEN = "7951709962:AAGzPzuVPtwL95fRFQIZhrfUvoszAO2Ep4k"

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)

# Pydantic model for payment request validation
class PaymentRequest(BaseModel):
    phone_number: str
    amount: int
    account_reference: str = "Payment"
    transaction_desc: str = "M-Pesa Payment"

# Add this function to get the user ID from request
async def get_current_user_id(request: Request) -> str:
    """
    Extract the user ID from the request.
    This is a simple implementation - in production, you would implement proper authentication.
    """
    # For now, just extract from headers or return a default value
    # In a real app, you'd use proper auth tokens
    headers = request.headers
    user_id = headers.get("X-User-ID", "default_user")
    return user_id

@app.post("/initiate_payment")
async def initiate_payment_endpoint(payment: PaymentRequest, user_id: str = Depends(get_current_user_id)):
    logger.info(f"Received payment request: phone={payment.phone_number}, amount={payment.amount}")
    try:
        response = client.initiate_payment(
            phone_number=payment.phone_number,
            amount=payment.amount,
            account_reference=payment.account_reference,
            transaction_desc=payment.transaction_desc
        )
        logger.info(f"M-Pesa API Response: {response}")
        if response.get("ResponseCode") != "0":
            logger.error(f"M-Pesa API Error: {response.get('ResponseDescription')}")
            raise HTTPException(status_code=400, detail=response.get('CustomerMessage', 'M-Pesa request failed'))

        # Store the payment interaction
        interaction_details = {
            "type": "payment",
            "amount": payment.amount,
            "account_reference": payment.account_reference,
            "transaction_desc": payment.transaction_desc,
            "response": response
        }
        await store_interaction(user_id, interaction_details)

        return response
    except Exception as e:
        logger.exception(f"Payment initiation failed: {str(e)}")
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

        # Update the payment interaction with the callback details
        interaction_details = {
            "type": "payment_callback",
            "merchant_request_id": merchant_request_id,
            "checkout_request_id": checkout_request_id,
            "result_code": result_code,
            "result_desc": result_desc,
            "callback_data": stk_callback
        }
        # Assuming you have a way to get the user_id from the callback data
        user_id = get_user_id_from_callback(callback_data)
        await store_interaction(user_id, interaction_details)

        if result_code == 0:
            logger.info(f"Payment successful for CheckoutRequestID: {checkout_request_id}")
            # Add success logic here
        else:
            logger.error(f"Payment failed/cancelled for CheckoutRequestID: {checkout_request_id}. Reason: {result_desc} (Code: {result_code})")
            # Add failure logic here
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    except Exception as e:
        logger.exception(f"Callback processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error processing callback")

@app.post("/chat")
async def chat_endpoint(request: Request, user_id: str = Depends(get_current_user_id)):
    data = await request.json()
    message = data.get("message")
    chat_history = data.get("chat_history", [])

    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    # Prepend base prompt to the user message
    full_message = f"{base_prompt}\nUser: {message}"

    # Store the chat interaction
    interaction_details = {
        "type": "chat",
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    await store_interaction(user_id, interaction_details)

    # Generate response using LangChain
    result = qa({"question": full_message, "chat_history": chat_history})
    response = result["answer"]
    chat_history.append((message, response))

    return {"response": response, "chat_history": chat_history}

async def store_interaction(user_id: str, interaction_details: dict):
    # Get the embedding for the interaction details
    embedding = embeddings.embed_documents([json.dumps(interaction_details)])[0]

    # Insert the interaction into the user_interactions table
    data = {
        "user_id": user_id,
        "interaction_type": interaction_details["type"],
        "interaction_details": interaction_details,
        "embedding": embedding
    }
    supabase.table("user_interactions").insert(data).execute()

    # Store the interaction in Redis for caching
    redis_key = f"interaction:{user_id}"
    redis_client.rpush(redis_key, json.dumps(interaction_details))

def get_user_id_from_callback(callback_data: dict) -> str:
    # Implement logic to extract user_id from callback_data
    # This is a placeholder implementation
    return callback_data.get("user_id", "")

# Telegram bot handlers
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Hi! I am your personal assistant. How can I help you today?')

async def handle_message(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    message = update.message.text
    chat_history = []

    # Prepend base prompt to the user message
    full_message = f"{base_prompt}\nUser: {message}"

    # Store the chat interaction
    interaction_details = {
        "type": "chat",
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "username": user.username,
        "phone_number": user.phone_number if user.phone_number else ""
    }
    await store_interaction(str(user.id), interaction_details)

    # Generate response using LangChain
    result = qa({"question": full_message, "chat_history": chat_history})
    response = result["answer"]
    chat_history.append((message, response))

    await update.message.reply_text(response)

async def handle_payment(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    message = update.message.text

    # Extract payment details from the message
    try:
        amount = int(message.split()[1])
        account_reference = message.split()[2]
        transaction_desc = message.split()[3]
    except (IndexError, ValueError):
        await update.message.reply_text('Invalid payment details. Please use the format: /pay <amount> <account_reference> <transaction_desc>')
        return

    # Initiate payment
    payment = PaymentRequest(
        phone_number=user.phone_number if user.phone_number else "",
        amount=amount,
        account_reference=account_reference,
        transaction_desc=transaction_desc
    )
    response = await initiate_payment_endpoint(payment, str(user.id))

    await update.message.reply_text(f"Payment initiated: {response}")

def main() -> None:
    # Create the Application and pass it your bot's token.
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pay", handle_payment))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    import uvicorn
    import asyncio
    import threading

    # Run the Telegram bot in a separate thread
    def run_telegram_bot():
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Instead of using run_polling() which is meant for synchronous use,
        # we'll create and run the application differently
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("pay", handle_payment))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Start the bot
        loop.run_until_complete(application.initialize())
        loop.run_until_complete(application.start())
        loop.run_forever()
    
    # Start the Telegram bot in a background thread
    bot_thread = threading.Thread(target=run_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Run the FastAPI server in the main thread
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
