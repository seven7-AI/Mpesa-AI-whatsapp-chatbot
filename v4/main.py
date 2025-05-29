"""
FastAPI Web Integration for Chat Agent

This module implements a FastAPI web server that integrates:
- Chat agent with M-Pesa Till payment tool
- Telegram integration
"""

import os
import logging
import threading
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our components
from chat_agent import ChatAgent
from telegram_integration import TelegramIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(title="M-Pesa Till Payment Chat Agent API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize chat agent
chat_agent = ChatAgent()

# Initialize Telegram integration in a separate thread
telegram_integration = None
telegram_thread = None

def start_telegram_bot():
    """Start the Telegram bot in a separate thread with a proper event loop."""
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        global telegram_integration
        telegram_integration = TelegramIntegration(chat_agent)
        
        # Use the synchronous method that handles the event loop internally
        logger.info("Starting Telegram bot with new event loop...")
        telegram_integration.run_polling()
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")
        import traceback
        logger.error(traceback.format_exc())

# Start Telegram bot in a separate thread if token is available
if os.getenv("TELEGRAM_BOT_TOKEN"):
    logger.info("Starting Telegram bot in background thread...")
    telegram_thread = threading.Thread(target=start_telegram_bot, daemon=True)
    telegram_thread.start()
    logger.info("Telegram thread started")
else:
    logger.warning("TELEGRAM_BOT_TOKEN not set, Telegram integration disabled")

# Pydantic models for API
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    user_id: str

class ChatResponse(BaseModel):
    """Chat response model."""
    response: str

class ClearHistoryRequest(BaseModel):
    """Clear history request model."""
    user_id: str

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "M-Pesa Till Payment Chat Agent API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint for web interface.
    
    Args:
        request: The chat request
        
    Returns:
        ChatResponse: The chat response
    """
    try:
        logger.info(f"Received chat request from user {request.user_id}: {request.message}")
        
        # Process the message with the chat agent
        response = chat_agent.process_message(request.message, request.user_id)
        
        logger.info(f"Sent response to user {request.user_id}")
        return ChatResponse(response=response)
        
    except Exception as e:
        error_msg = f"Error processing chat request: {str(e)}"
        logger.exception(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/clear_history")
async def clear_history(request: ClearHistoryRequest):
    """
    Clear chat history for a user.
    
    Args:
        request: The clear history request
    """
    try:
        logger.info(f"Clearing chat history for user {request.user_id}")
        chat_agent.clear_user_memory(request.user_id)
        return {"success": True, "message": f"History cleared for user {request.user_id}"}
    except Exception as e:
        error_msg = f"Error clearing chat history: {str(e)}"
        logger.exception(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    status = {
        "status": "healthy",
        "components": {
            "chat_agent": "available",
            "mpesa_till_tool": "available",
            "telegram": "running" if telegram_thread is not None and telegram_thread.is_alive() else "unavailable"
        }
    }
    return status

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 4000))
    logger.info(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
