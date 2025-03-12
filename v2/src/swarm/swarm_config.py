from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.agents.chat_agent import run_chat
from src.agents.daraja_agents.till_agent import TillAgent
from src.agents.daraja_agents.business_buy_goods_agent import BusinessBuyGoodsAgent
from src.agents.daraja_agents.authorization_agent import AuthorizationAgent
from src.agents.daraja_agents.qr_agent import DynamicQRAgent
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

# Helper function to run TillAgent with dynamic short_code
def run_till_with_token(state: ChatState) -> Dict[str, Any]:
    auth_agent = AuthorizationAgent()
    auth_response = auth_agent._run()
    if auth_response.error_message:
        return {"messages": state.messages + [SystemMessage(content=f"Error: {auth_response.error_message}")]}

    access_token = auth_response.access_token
    till_agent = TillAgent()
    last_message = state.messages[-1].content.lower()
    
    # Parse message (e.g., "pay 100 to till 174379")
    parts = last_message.split()
    if len(parts) < 5 or parts[2] != "to" or parts[3] != "till":
        return {"messages": state.messages + [SystemMessage(content="Invalid format. Use: 'pay <amount> to till <short_code>'")]}
    
    amount = float(parts[1]) if parts[1].replace('.', '', 1).isdigit() else 100.0  # Default if invalid
    short_code = parts[4]  # Dynamic short_code from user input
    phone_number = state.phone_number or "254719321423"  # Default if not provided
    account_reference = f"TillPayment_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    till_response = till_agent._run(amount, phone_number, short_code, account_reference, access_token)
    return {
        "messages": state.messages + [SystemMessage(content=f"Till Payment: {till_response.checkout_request_id or till_response.error_message}")]
    }

# Helper function to run BusinessBuyGoodsAgent
def run_business_buy_goods(state: ChatState) -> Dict[str, Any]:
    auth_agent = AuthorizationAgent()
    auth_response = auth_agent._run()
    if auth_response.error_message:
        return {"messages": state.messages + [SystemMessage(content=f"Error: {auth_response.error_message}")]}

    access_token = auth_response.access_token
    b2b_agent = BusinessBuyGoodsAgent()
    last_message = state.messages[-1].content.lower()
    
    # Parse message (e.g., "pay 200 from 123456 to merchant 000000")
    parts = last_message.split()
    if len(parts) < 7 or parts[2] != "from" or parts[4] != "to" or parts[5] != "merchant":
        return {"messages": state.messages + [SystemMessage(content="Invalid format. Use: 'pay <amount> from <sender_short_code> to merchant <receiver_short_code>'")]}
    
    amount = float(parts[1]) if parts[1].replace('.', '', 1).isdigit() else 200.0
    sender_short_code = parts[3]
    receiver_short_code = parts[6]
    account_reference = f"B2BPayment_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    remarks = "Business Buy Goods Payment"
    
    b2b_response = b2b_agent._run(amount, sender_short_code, receiver_short_code, account_reference, remarks, None, access_token)
    return {
        "messages": state.messages + [SystemMessage(content=f"B2B Payment: {b2b_response.transaction_id or b2b_response.error_message}")]
    }
# Helper function to run DynamicQRAgent
def run_dynamic_qr(state: ChatState) -> Dict[str, Any]:
    auth_agent = AuthorizationAgent()
    auth_response = auth_agent._run()
    if auth_response.error_message:
        return {"messages": state.messages + [SystemMessage(content=f"Error: {auth_response.error_message}")]}

    access_token = auth_response.access_token
    qr_agent = DynamicQRAgent()
    last_message = state.messages[-1].content.lower()
    
    # Parse message (e.g., "generate qr for 100 to till 373132")
    parts = last_message.split()
    if len(parts) < 6 or parts[1] != "qr" or parts[2] != "for" or parts[4] != "to" or parts[5] != "till":
        return {"messages": state.messages + [SystemMessage(content="Invalid format. Use: 'generate qr for <amount> to till <short_code>'")]}
    
    amount = float(parts[3]) if parts[3].replace('.', '', 1).isdigit() else 100.0
    short_code = parts[6]
    merchant_name = "TEST-SUPERMARKET"  # Default; could be configurable
    ref_no = f"QR_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    trx_code = "BG"  # Buy Goods by default
    
    qr_response = qr_agent._run(merchant_name, amount, short_code, ref_no, trx_code, "300", access_token)
    return {
        "messages": state.messages + [SystemMessage(content=f"QR Code Generated: {qr_response.request_id or qr_response.error_message}")]
    }

# Intent detection functions
def check_till_intent(state: Dict[str, Any]) -> bool:
    if not state["messages"]:
        return False
    last_message = state["messages"][-1].content.lower()
    return "to till" in last_message and "generate qr" not in last_message

def check_b2b_intent(state: Dict[str, Any]) -> bool:
    if not state["messages"]:
        return False
    last_message = state["messages"][-1].content.lower()
    return "to merchant" in last_message

def check_qr_intent(state: Dict[str, Any]) -> bool:
    if not state["messages"]:
        return False
    last_message = state["messages"][-1].content.lower()
    return "generate qr" in last_message

# Setup the workflow
workflow = StateGraph(ChatState)

# Add nodes
workflow.add_node("chat", run_chat)
workflow.add_node("till", run_till_with_token)
workflow.add_node("b2b", run_business_buy_goods)
workflow.add_node("qr", run_dynamic_qr)

# Define conditional edges
workflow.add_conditional_edges(
    "chat",
    lambda state: "till" if check_till_intent(state) else "b2b" if check_b2b_intent(state) else "qr" if check_qr_intent(state) else "chat",
    {
        "till": "till",
        "b2b": "b2b",
        "qr": "qr",
        "chat": "chat"
    }
)

# Add edges back to chat
workflow.add_edge("till", "chat")
workflow.add_edge("b2b", "chat")
workflow.add_edge("qr", "chat")

# Set entry point
workflow.set_entry_point("chat")

# Compile the graph
app = workflow.compile()