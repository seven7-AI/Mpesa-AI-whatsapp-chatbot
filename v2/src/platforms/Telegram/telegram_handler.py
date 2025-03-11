from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import datetime
from src.swarm.swarm_config import app as swarm_app, ChatState
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Initialize Telegram Bot
bot = Bot(TELEGRAM_TOKEN)
updater = Updater(TELEGRAM_TOKEN, use_context=True)

def start(update: Update, context: CallbackContext) -> None:
    """Handle the /start command."""
    update.message.reply_text("Welcome to the Mpesa AI Chatbot! Send a message to begin (e.g., 'pay 100 till').")

def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages from Telegram."""
    # Extract user info and message
    user_id = str(update.message.chat_id)  # Telegram chat ID as user_id
    username = update.message.from_user.username or user_id  # Use username if available, else chat_id
    message_text = update.message.text

    # Create ChatState for Telegram
    state = ChatState(
        user_id=user_id,
        username=username,  # Telegram-specific field
        phone_number=None,  # Not applicable for Telegram unless provided
        messages=[HumanMessage(content=message_text)],
        timestamp=datetime.now().isoformat()
    )

    try:
        # Invoke the swarm
        response = swarm_app.invoke(state)
        # Send the last message back to Telegram
        bot_response = response["messages"][-1].content
        update.message.reply_text(bot_response)
    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")

def run_telegram_bot():
    """Start the Telegram bot with polling for terminal testing."""
    dp = updater.dispatcher
    
    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Start polling
    print("Starting Telegram Bot... Type '/start' in Telegram to begin.")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    run_telegram_bot()