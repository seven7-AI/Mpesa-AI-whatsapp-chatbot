from src.swarm.swarm_config import app as swarm_app, ChatState
from langchain_core.messages import HumanMessage
from datetime import datetime
from src.platforms.telegram.telegram_handler import set_telegram_webhook
from src.server.app import app as flask_app

def run_terminal_test():
    print("Mpesa AI Chatbot Terminal Test")
    print("Type 'exit' to quit")
    user_id = "254719321423"
    
    while True:
        message = input("You: ")
        if message.lower() == "exit":
            break
        state = ChatState(
            user_id=user_id,
            phone_number=user_id,
            messages=[HumanMessage(content=message)],
            timestamp=datetime.now().isoformat()
        )
        try:
            response = swarm_app.invoke(state)
            print(f"Bot: {response['messages'][-1].content}")
        except Exception as e:
            print(f"Error: {str(e)}")

def run_webhook_test():
    print("Starting Flask server for webhook testing...")
    webhook_url = input("Enter your public URL (e.g., Ngrok URL) for Telegram webhook (e.g., https://your-ngrok-url.ngrok-free.app/telegram): ")
    if set_telegram_webhook(webhook_url):
        flask_app.run(host="0.0.0.0", port=5000, debug=True)
    else:
        print("Webhook setup failed. Exiting.")

def main():
    print("Choose test mode: 1) Terminal, 2) Telegram Webhook")
    choice = input("Enter 1 or 2: ")
    if choice == "1":
        run_terminal_test()
    elif choice == "2":
        run_webhook_test()
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()