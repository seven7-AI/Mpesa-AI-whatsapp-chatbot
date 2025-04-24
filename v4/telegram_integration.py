"""
Telegram Integration for Chat Agent

This module implements the Telegram integration for the chat agent
using the python-telegram-bot library.
"""

import os
import logging
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
        self._initialize_telegram()
    
    def _initialize_telegram(self) -> None:
        """Initialize the Telegram bot."""
        try:
            # Check for required Telegram token
            self.token = os.getenv("TELEGRAM_BOT_TOKEN")
            
            if not self.token:
                error_msg = "Missing TELEGRAM_BOT_TOKEN environment variable"
                logger.error(error_msg)
                raise EnvironmentError(error_msg)
            
            # Create the application
            self.application = Application.builder().token(self.token).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self._start_command))
            self.application.add_handler(CommandHandler("help", self._help_command))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
            
            logger.info("Telegram bot initialized successfully.")
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            raise
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle the /start command.
        
        Args:
            update: The update from Telegram
            context: The context from Telegram
        """
        try:
            user = update.effective_user
            welcome_message = (
                f"Hello {user.first_name}! 👋\n\n"
                "I'm your M-Pesa payment assistant. I can help you with:\n"
                "- Processing M-Pesa payments (Till and Paybill)\n"
                "- Answering questions using web search\n\n"
                "Just send me a message to get started!"
            )
            
            await update.message.reply_text(welcome_message)
            logger.info(f"Sent welcome message to user {user.id}")
            
        except Exception as e:
            logger.error(f"Error handling start command: {e}")
            await update.message.reply_text("Sorry, something went wrong. Please try again later.")
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle the /help command.
        
        Args:
            update: The update from Telegram
            context: The context from Telegram
        """
        try:
            help_message = (
                "Here's how you can use me:\n\n"
                "1. For M-Pesa payments, just tell me you want to make a payment\n"
                "2. For web searches, ask me any question\n\n"
                "Commands:\n"
                "/start - Start the bot\n"
                "/help - Show this help message"
            )
            
            await update.message.reply_text(help_message)
            logger.info(f"Sent help message to user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error handling help command: {e}")
            await update.message.reply_text("Sorry, something went wrong. Please try again later.")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle incoming messages.
        
        Args:
            update: The update from Telegram
            context: The context from Telegram
        """
        try:
            user_id = update.effective_user.id
            message_text = update.message.text
            
            logger.info(f"Received message from user {user_id}: {message_text}")
            
            # Process the message with the chat agent
            response = self.chat_agent.process_message(message_text)
            
            # Send the response back to the user
            await update.message.reply_text(response)
            logger.info(f"Sent response to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text("Sorry, I encountered an error processing your message. Please try again.")
    
    def start_polling(self) -> None:
        """Start the Telegram bot polling."""
        try:
            logger.info("Starting Telegram bot polling...")
            self.application.run_polling()
            
        except Exception as e:
            logger.error(f"Error starting Telegram bot polling: {e}")
            raise
