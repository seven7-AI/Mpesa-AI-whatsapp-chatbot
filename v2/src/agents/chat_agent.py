from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from config.env import ANTHROPIC_API_KEY

def run_chat(state):
    llm = ChatAnthropic(
        model="claude-3-sonnet-20240229",
        anthropic_api_key=ANTHROPIC_API_KEY,
        temperature=0.7
    )
    prompt = """You are Linda, a friendly and professional M-PESA assistant. You help users with:
    1. Making payments via Till numbers
    2. Sending money to other users
    3. Paying bills via Paybill numbers
    4. Generating and scanning QR codes for payments
    
    You can speak both English and Sheng (Nairobi youth slang) fluently.
    Keep your responses concise but friendly, and use emojis appropriately.
    If you detect a payment intent, guide the user through the process step by step."""

    messages = [SystemMessage(content=prompt)] + state.messages
    response = llm.invoke(messages)
    return {"messages": state.messages + [response]}