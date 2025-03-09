# platform

# from flask import Flask
# import logging

# from whatsapp_configuration.views import webhook_blueprint
# from whatsapp_configuration.config import Config
# from ai_bot_langchain import AIBot


# def create_app():
#     #app set up function
#     app = Flask(__name__)
#     Config.configure_logging()
    
#     app.register_blueprint(webhook_blueprint)
    
#     #create a separate bot instance for each phone number,
#     #this allows different users to have separate conversations with the chatbot
#     #it also allows different users to use different google callendar APIs
#     app.bot_instance = AIBot()
    
#     return app


# if __name__ == '__main__':
#     app = create_app()
    
#     logging.info('Flask app started')
#     app.run(host='0.0.0.0', port=5000)   


# Console test
# main.py
from src.swarm.swarm_config import app as swarm_app, ChatState
from langchain_core.messages import HumanMessage
from datetime import datetime

def run_terminal_test():
    print("Mpesa AI Chatbot Terminal Test")
    print("Type 'exit' to quit")
    
    # Simulate a user (replace with your test phone number)
    user_id = "254719321423"  # WhatsApp-style phone number for testing
    
    while True:
        # Get user input from terminal
        message = input("You: ")
        if message.lower() == "exit":
            break
        
        # Create initial state with user input
        state = ChatState(
            user_id=user_id,
            phone_number=user_id,
            messages=[HumanMessage(content=message)],
            timestamp=datetime.now().isoformat()
        )
        
        # Invoke the swarm
        try:
            response = swarm_app.invoke(state)
            # Print the last message from the response
            print(f"Bot: {response['messages'][-1].content}")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    run_terminal_test()