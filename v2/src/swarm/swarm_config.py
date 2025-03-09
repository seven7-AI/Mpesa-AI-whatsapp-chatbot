# src/swarm/swarm_config.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Annotated, Union, Literal
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents.chat_agent import run_chat  # We'll create this below
from agents.daraja_agents.till_agent import TillAgent
from agents.daraja_agents.authorization_agent import AuthorizationAgent
from datetime import datetime

# Define ChatState
class ChatState(BaseModel):
    messages: List[AnyMessage] = []
    user_id: str
    phone_number: Optional[str] = None
    username: Optional[str] = None
    transaction_id: Optional[str] = None
    language: str = "English"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# Memory setup (in-memory for testing)
short_term_memory = MemorySaver()

# Helper function to run TillAgent with access token
def run_till_with_token(state: ChatState) -> Dict[str, Any]:
    auth_agent = AuthorizationAgent()
    auth_response = auth_agent._run()
    if auth_response.error_message:
        return {"messages": state.messages + [SystemMessage(content=f"Error: {auth_response.error_message}")]}

    access_token = auth_response.access_token
    till_agent = TillAgent()
    last_message = state.messages[-1].content.lower()
    
    # Simple parsing for testing (e.g., "pay 100 till")
    parts = last_message.split()
    amount = float(parts[1]) if len(parts) > 1 else 100.0  # Default to 100 if parsing fails
    phone_number = state.phone_number
    short_code = "174379"  # Sandbox Till Number test shortcode
    account_reference = "TestTill123"
    
    till_response = till_agent._run(amount, phone_number, short_code, account_reference, access_token)
    return {
        "messages": state.messages + [SystemMessage(content=f"Till Payment: {till_response.checkout_request_id or till_response.error_message}")]
    }

def check_till_intent(state: Dict[str, Any]) -> bool:
    if not state["messages"]:
        return False
    last_message = state["messages"][-1].content.lower()
    return "till" in last_message

# Setup the workflow
workflow = StateGraph(ChatState)

# Add nodes
workflow.add_node("chat", run_chat)
workflow.add_node("till", run_till_with_token)

# Define conditional edges
workflow.add_conditional_edges(
    "chat",
    check_till_intent,
    {
        True: "till",
        False: "chat"
    }
)

# Add edge back to chat from till
workflow.add_edge("till", "chat")

# Set entry point
workflow.set_entry_point("chat")

# Compile the graph
app = workflow.compile()