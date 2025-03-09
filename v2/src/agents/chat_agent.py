from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from config.env import OPENAI_API_KEY

def run_chat(state):
    llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)  # Replace with your key
    prompt = "You are a chatbot for Mpesa transactions. Interpret the user's intent and respond appropriately."
    messages = [SystemMessage(content=prompt)] + state.messages
    response = llm.invoke(messages)
    return {"messages": state.messages + [response]}