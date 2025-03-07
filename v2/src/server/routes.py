from flask import request, jsonify
from src.swarm.swarm_config import app as swarm_app
from src.memory.neo4j_store import store_conversation
from src.swarm.swarm_config import ChatState
from langchain_core.messages import HumanMessage
from datetime import datetime

def init_routes(app):
    @app.route("/whatsapp", methods=["POST"])
    def whatsapp():
        try:
            data = request.json
            user_id = data["phone_number"]
            message = data["message"]
            state = ChatState(
                user_id=user_id,
                phone_number=user_id,
                messages=[HumanMessage(content=message)],
                timestamp=datetime.now().isoformat()
            )
            response = swarm_app.invoke(state)
            store_conversation(user_id, response["messages"])
            return jsonify({"response": response["messages"][-1].content})
        except Exception as e:
            return jsonify({"error": str(e)}), 500