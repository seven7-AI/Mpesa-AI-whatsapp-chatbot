"""
Telegram Integration for Chat Agent

This module implements the Telegram integration for the chat agent
using the python-telegram-bot library.
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Import our chat agent
from chat_agent import ChatAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TelegramIntegration:
    """Telegram integration for the chat agent."""
    
    def __init__(self, chat_agent: ChatAgent):
        """
        Initialize the Telegram integration.
        
        Args:
            chat_agent: The chat agent to use for processing messages
        """
        self.chat_agent = chat_agent
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if not self.token:
            error_msg = "Missing TELEGRAM_BOT_TOKEN environment variable"
            logger.error(error_msg)
            raise EnvironmentError(error_msg)
        
        # Initialize the Telegram application
        self.application = Application.builder().token(self.token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("clear", self.clear_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("Telegram integration initialized")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command."""
        user = update.effective_user
        user_id = self._get_user_id(update)
        logger.info(f"Start command from user {user_id}")
        
        await update.message.reply_text(
            f"Hello {user.first_name}! I'm Seven, your M-Pesa payment assistant. "
            "I can help you make Till payments. Just let me know how I can assist you."
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /help command."""
        user_id = self._get_user_id(update)
        logger.info(f"Help command from user {user_id}")
        
        await update.message.reply_text(
            "Here's how I can help you:\n\n"
            "1. Make Till payments through M-Pesa\n"
            "2. Answer questions about M-Pesa services\n\n"
            "To make a payment, simply tell me you want to pay, and I'll guide you through the process.\n\n"
            "Commands:\n"
            "/start - Start the conversation\n"
            "/help - Show this help message\n"
            "/clear - Clear your conversation history"
        )
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /clear command to reset conversation history."""
        user_id = self._get_user_id(update)
        logger.info(f"Clear command from user {user_id}")
        
        self.chat_agent.clear_user_memory(user_id)
        await update.message.reply_text("Your conversation history has been cleared.")
    
    def _get_user_id(self, update: Update) -> str:
        """
        Get a unique identifier for the user.
        
        Args:
            update: The Telegram update
            
        Returns:
            str: Unique user identifier (username or ID)
        """
        user = update.effective_user
        # Prefer username if available, otherwise use user ID
        return f"telegram_{user.username}" if user.username else f"telegram_{user.id}"
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle user messages."""
        user_id = self._get_user_id(update)
        message = update.message.text
        logger.info(f"Message from user {user_id}: {message}")
        
        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        # Process the message
        response = self.chat_agent.process_message(message, user_id)
        
        # Reply to the user
        await update.message.reply_text(response)
        logger.info(f"Replied to user {user_id}")
    
    def run_polling(self):
        """Run the polling using the Application.run_polling method."""
        logger.info("Starting Telegram polling...")
        # This is a blocking call that will run forever
        # It will use the event loop that should be created in the thread
        current_loop = asyncio.get_event_loop()
        logger.info(f"Using event loop: {current_loop}")
        
        # Proper way to run the application
        self.application.run_polling(
            drop_pending_updates=True,
            close_loop=False  # Don't close the loop when finished
        )
