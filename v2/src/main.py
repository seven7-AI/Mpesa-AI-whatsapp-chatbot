# from src.server.app import app

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True) 
    
    
    
# # # src/server/app.py
# # from flask import Flask
# # from src.server.routes import init_routes  # Ensure this matches the filename

# # app = Flask(__name__)
# # init_routes(app)

# # if __name__ == "__main__":
# #     app.run(host="0.0.0.0", port=5000, debug=True) 



# main.py
from swarm.swarm_config import app as swarm_app, ChatState
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