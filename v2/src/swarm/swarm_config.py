from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.messages import AnyMessage
from langgraph.graph import StateGraph, END
from langgraph_swarm import create_handoff_tool
from src.agents.chat_agent import run_chat  # Assuming chat_agent.py exists
from src.agents.daraja_agents.till_agent import TillAgent
from src.agents.daraja_agents.authorization_agent import AuthorizationAgent
from src.memory.langmem_handler import short_term_memory, long_term_memory
from datetime import datetime

class ChatState(BaseModel):
    messages: List[AnyMessage] = []
    user_id: str
    phone_number: Optional[str] = None
    username: Optional[str] = None
    transaction_id: Optional[str] = None
    language: str = "English"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

def run_till_with_token(state: ChatState):
    auth_agent = AuthorizationAgent()
    access_token = auth_agent._run()
    till_agent = TillAgent()
    last_message = state.messages[-1].content.lower()
    amount = float(last_message.split()[1]) if len(last_message.split()) > 1 else 100.0  # Example parsing
    phone_number = state.phone_number or "254719321423"  # Default for testing
    short_code = "YOUR_TILL_SHORTCODE"  # Replace with env var
    return till_agent._run(amount, phone_number, short_code, access_token)

workflow = StateGraph(ChatState)
workflow.add_node("chat", run_chat)
workflow.add_node("till", run_till_with_token)
# Add paybill node when implemented: workflow.add_node("paybill", paybill_agent.run)

workflow.add_edge("chat", "till", condition=lambda state, output: "till" in output.lower())
# workflow.add_edge("chat", "paybill", condition=lambda state, output: "paybill" in output.lower())  # Uncomment when paybill added
workflow.set_entry_point("chat")
app = workflow.compile(checkpointer=short_term_memory, store=long_term_memory)