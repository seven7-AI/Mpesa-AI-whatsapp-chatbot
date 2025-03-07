from langgraph_swarm import create_react_agent
from langchain_openai import ChatOpenAI
from src.tools.daraja_tools import till_agent
from src.tools import browsing_tool, sheng_tool, twitter_tool

llm = ChatOpenAI(model="gpt-4o", api_key="YOUR_OPENAI_API_KEY")
tools = [till_agent, browsing_tool, sheng_tool, twitter_tool]

chat_agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt="You are a multilingual chatbot for Mpesa transactions.",
    name="ChatAgent"
)

def run_chat(input_state):
    return chat_agent.run(input_state)