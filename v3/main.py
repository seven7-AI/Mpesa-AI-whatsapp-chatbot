from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import os
import logging
from logging.handlers import RotatingFileHandler
import json
import time
from dotenv import load_dotenv
from mpesa_integration.mpesa import MpesaClient, MpesaConfig
from langgraph.graph import Graph
from langchain_openai import ChatOpenAI
from langchain_neo4j import Neo4jGraph
import re
import traceback

# Configure logging
def setup_logging():
    """Configure and set up logging for the application."""
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    file_handler = RotatingFileHandler(
        "logs/mpesa_app.log", maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    error_handler = RotatingFileHandler(
        "logs/mpesa_errors.log", maxBytes=10*1024*1024, backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(log_format)
    logger.addHandler(error_handler)
    return logger

logger = setup_logging()

# Load environment variables
logger.info("Loading environment variables")
load_dotenv()

# Log environment variables for debugging
logger.info(f"NEO4J_URI: {os.getenv('NEO4J_URI')}")
logger.info(f"NEO4J_USER: {os.getenv('NEO4J_USER')}")
logger.info(f"NEO4J_PASSWORD: {os.getenv('NEO4J_PASSWORD')}")

try:
    # Initialize Neo4jGraph for memory management
    logger.info("Initializing Neo4jGraph")
    neo4j_db = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD")
    )
    neo4j_db.query("CREATE CONSTRAINT user_phone_number IF NOT EXISTS FOR (u:User) REQUIRE u.phone_number IS UNIQUE")
    logger.info("Neo4jGraph initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Neo4jGraph: {str(e)}", exc_info=True)
    raise

try:
    # Initialize M-Pesa client
    logger.info("Initializing M-Pesa client")
    config = MpesaConfig(
        consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
        consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
        shortcode=os.getenv("MPESA_SHORTCODE"),
        passkey=os.getenv("MPESA_PASSKEY"),
        callback_url=os.getenv("MPESA_CALLBACK_URL"),
        environment=os.getenv("MPESA_ENVIRONMENT", "sandbox")
    )
    mpesa_client = MpesaClient(config)
    logger.info("M-Pesa client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize M-Pesa client: {str(e)}", exc_info=True)
    raise

# Define tools for the agent
def get_state(phone_number: str) -> str:
    """Retrieve the current state of a user from Neo4j."""
    try:
        logger.debug(f"Getting state for phone number: {phone_number}")
        result = neo4j_db.query(
            "MATCH (u:User {phone_number: $phone_number}) RETURN u.state AS state",
            params={"phone_number": phone_number}
        )
        state = result[0]["state"] if result and "state" in result[0] else "idle"
        logger.debug(f"State for {phone_number}: {state}")
        return state
    except Exception as e:
        logger.error(f"Error getting state for {phone_number}: {str(e)}", exc_info=True)
        return "idle"

def set_state(phone_number: str, new_state: str):
    """Set the state of a user in Neo4j."""
    try:
        logger.debug(f"Setting state for {phone_number} to: {new_state}")
        neo4j_db.query(
            "MERGE (u:User {phone_number: $phone_number}) SET u.state = $new_state",
            params={"phone_number": phone_number, "new_state": new_state}
        )
        logger.debug(f"State for {phone_number} updated successfully")
    except Exception as e:
        logger.error(f"Error setting state for {phone_number}: {str(e)}", exc_info=True)
        raise

def extract_amount(message: str) -> int | None:
    """Extract a numeric amount from the user's message."""
    try:
        logger.debug(f"Extracting amount from message: {message}")
        match = re.search(r'\b\d+\b', message)
        if match:
            amount = int(match.group())
            logger.debug(f"Extracted amount: {amount}")
            return amount
        logger.debug("No amount found in message")
        return None
    except Exception as e:
        logger.error(f"Error extracting amount from message: {str(e)}", exc_info=True)
        return None

def initiate_payment(phone_number: str, amount: int) -> dict:
    """Initiate a till payment using M-Pesa."""
    try:
        logger.info(f"Initiating payment for {phone_number}, amount: {amount}")
        start_time = time.time()
        response = mpesa_client.initiate_payment(
            phone_number=phone_number,
            amount=amount,
            account_reference="TillPayment",
            transaction_desc="Payment via Till Number"
        )
        elapsed_time = time.time() - start_time
        logger.info(f"Payment initiated in {elapsed_time:.2f}s: {json.dumps(response)}")
        return response
    except Exception as e:
        logger.error(f"Failed to initiate payment: {str(e)}", exc_info=True)
        return {"ResponseCode": "1", "ResponseDescription": f"Error: {str(e)}"}

# Define custom chains for different actions
def ask_for_amount_chain(input_data: dict) -> dict:
    """Chain to request the amount from the user."""
    try:
        phone_number = input_data["phone_number"]
        logger.info(f"Asking for amount from {phone_number}")
        set_state(phone_number, "waiting_for_amount")
        return {"response": "Please provide the amount."}
    except Exception as e:
        logger.error(f"Error in ask_for_amount_chain: {str(e)}", exc_info=True)
        return {"response": "Sorry, there was an error processing your request. Please try again."}

def initiate_payment_chain(input_data: dict) -> dict:
    """Chain to initiate payment if amount is provided."""
    try:
        phone_number = input_data["phone_number"]
        amount = input_data.get("amount")
        logger.info(f"Initiating payment chain for {phone_number}, amount: {amount}")
        if amount is None:
            logger.warning(f"Amount not provided for {phone_number}")
            return {"response": "Amount not provided. Please provide the amount."}
        response = initiate_payment(phone_number, amount)
        if response.get("ResponseCode") == "0":
            checkout_id = response["CheckoutRequestID"]
            set_state(phone_number, "payment_pending")
            neo4j_db.query(
                "MERGE (u:User {phone_number: $phone_number}) SET u.checkout_request_id = $checkout_id",
                params={"phone_number": phone_number, "checkout_id": checkout_id}
            )
            logger.info(f"Payment successfully initiated for {phone_number}, checkout ID: {checkout_id}")
            return {"response": "Payment initiated. Please confirm on your M-Pesa app."}
        else:
            error_msg = response.get("ResponseDescription", "Unknown error")
            logger.error(f"Failed to initiate payment: {error_msg}")
            return {"response": f"Failed to initiate payment: {error_msg}"}
    except Exception as e:
        logger.error(f"Error in initiate_payment_chain: {str(e)}", exc_info=True)
        return {"response": "Sorry, there was an error processing your payment. Please try again later."}

def provide_status_chain(input_data: dict) -> dict:
    """Chain to provide payment status based on current state."""
    try:
        phone_number = input_data.get("phone_number", "unknown")
        state = input_data.get("state")
        logger.info(f"Providing status for {phone_number}, state: {state}")
        if state == "payment_pending":
            return {"response": "Your payment is still pending."}
        elif state == "payment_success":
            return {"response": "Your payment was successful."}
        elif state == "payment_failed":
            return {"response": "Your payment failed."}
        else:
            return {"response": "I'm not sure about your payment status."}
    except Exception as e:
        logger.error(f"Error in provide_status_chain: {str(e)}", exc_info=True)
        return {"response": "Sorry, there was an error checking your payment status."}

# Define the LangGraph
logger.info("Setting up LangGraph")
try:
    graph = Graph()
    input_node = graph.add_input_node()
    get_state_node = graph.add_tool_node(get_state)
    extract_amount_node = graph.add_tool_node(extract_amount)
    router_node = graph.add_llm_router_node(
        llm=ChatOpenAI(),
        prompt="""
        Current state: {state}
        User said: {message}
        Extracted amount: {amount}
        What should be the next action? Choose from: ask_for_amount, initiate_payment, provide_status
        """,
        output_variable="choice"
    )
    ask_for_amount_node = graph.add_custom_node(ask_for_amount_chain)
    initiate_payment_node = graph.add_custom_node(initiate_payment_chain)
    provide_status_node = graph.add_custom_node(provide_status_chain)
    graph.add_edge(input_node, get_state_node)
    graph.add_edge(get_state_node, extract_amount_node)
    graph.add_edge(extract_amount_node, router_node)
    graph.add_edge(router_node, ask_for_amount_node, condition=lambda x: x["choice"] == "ask_for_amount")
    graph.add_edge(router_node, initiate_payment_node, condition=lambda x: x["choice"] == "initiate_payment")
    graph.add_edge(router_node, provide_status_node, condition=lambda x: x["choice"] == "provide_status")
    logger.info("LangGraph setup complete")
except Exception as e:
    logger.critical(f"Failed to set up LangGraph: {str(e)}", exc_info=True)
    raise

# FastAPI application
app = FastAPI()

class MessageRequest(BaseModel):
    phone_number: str
    message: str

@app.post("/message")
async def handle_message(request: MessageRequest):
    """Handle user messages by running the LangGraph agent."""
    request_id = f"req_{int(time.time()*1000)}"
    logger.info(f"[{request_id}] Received message request from {request.phone_number}: {request.message}")
    try:
        input_data = {
            "phone_number": request.phone_number,
            "message": request.message
        }
        start_time = time.time()
        output = graph.invoke(input_data)
        elapsed_time = time.time() - start_time
        logger.info(f"[{request_id}] Graph processing completed in {elapsed_time:.2f}s")
        logger.debug(f"[{request_id}] Graph output: {json.dumps(output)}")
        return {"response": output["response"]}
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"[{request_id}] Error processing message: {str(e)}\n{error_trace}")
        return {"response": "Sorry, I encountered an error while processing your request. Please try again later."}

@app.post("/mpesa/callback")
async def handle_callback(request: Request):
    """Handle M-Pesa callbacks to update payment status."""
    request_id = f"callback_{int(time.time()*1000)}"
    logger.info(f"[{request_id}] Received M-Pesa callback")
    try:
        callback_data = await request.json()
        logger.debug(f"[{request_id}] Callback data: {json.dumps(callback_data)}")
        checkout_id = callback_data["Body"]["stkCallback"]["CheckoutRequestID"]
        result_code = callback_data["Body"]["stkCallback"]["ResultCode"]
        logger.info(f"[{request_id}] Processing callback for checkout ID: {checkout_id}, result code: {result_code}")
        result = neo4j_db.query(
            "MATCH (u:User) WHERE u.checkout_request_id = $checkout_id RETURN u.phone_number AS phone_number",
            params={"checkout_id": checkout_id}
        )
        if result:
            phone_number = result[0]["phone_number"]
            logger.info(f"[{request_id}] Found user {phone_number} for checkout ID {checkout_id}")
            new_state = "payment_success" if result_code == 0 else "payment_failed"
            logger.info(f"[{request_id}] Payment {'successful' if result_code == 0 else 'failed'} for {phone_number}")
            set_state(phone_number, new_state)
            neo4j_db.query(
                "MATCH (u:User {phone_number: $phone_number}) REMOVE u.checkout_request_id",
                params={"phone_number": phone_number}
            )
            logger.info(f"[{request_id}] Updated state to {new_state} for {phone_number}")
        else:
            logger.warning(f"[{request_id}] No user found for checkout ID: {checkout_id}")
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"[{request_id}] Error processing callback: {str(e)}\n{error_trace}")
        return {"ResultCode": 0, "ResultDesc": "Accepted despite error"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {"status": "healthy", "timestamp": time.time()}

if __name__ == "__main__":
    logger.info("Starting application")
    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.critical(f"Failed to start application: {str(e)}", exc_info=True)