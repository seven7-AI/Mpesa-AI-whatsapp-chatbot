from src.server.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True) 
    
    
    
# # src/server/app.py
# from flask import Flask
# from src.server.routes import init_routes  # Ensure this matches the filename

# app = Flask(__name__)
# init_routes(app)

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True) 