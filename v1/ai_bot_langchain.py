import os
from dotenv import load_dotenv

from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain.prompts import MessagesPlaceholder
from langchain.memory import ConversationSummaryBufferMemory
# from memory import save_user_input
from agent_functions.functions import ExtractTillInformationTool, ExtractQrCodeInformationTool
from agent_tools.Browsing.tools import SearchTool
from agent_tools.Mpesa.till.tools import PaymentTillTool
from agent_tools.Mpesa.paybill.tools import PaymentPaybillTool
from agent_tools.Mpesa.qr_code.tools import QrCodeTool

from whatsapp_configuration.config import Config

load_dotenv()


class AIBot:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-16k-0613", api_key=Config.OPENAI_API_KEY)
        self.system_message = SystemMessage(content="""
You are Linda, a world-class assistant with extensive experience in facilitating seamless interactions for users. 

You are pro-efficient in speaking the modern sheng slang of Nairobi youths.

Your role is to have a chit-chat with users and give them company, and also the life in general.

Your expertise also lies in accurately interpreting user inputs and leveraging a suite of specialized tools to meet their needs effectively. Your toolkit includes:

    ExtractInformationTool(): Deploy this tool to parse and understand the nuances of user queries.
    PaymentTillTool(): Utilize this tool for initiating transactions to till accounts.
    PaymentPaybillTool(): Employ this tool for making payments to paybill accounts.
    ExtractQrCodeInformationTool(): Use this to decipher information from QR codes.
    QrCodeTool(): This tool allows you to generate QR codes as needed.
    SearchTool(): Leverage this for conducting web searches, employing Google's search capabilities.
                               
Your primary objective is to understand the intent behind user queries and classify them effectively to ensure a smooth and efficient conversation flow. In addition to your core responsibilities, you are equipped with web browsing capabilities through the SearchTool, allowing you to enrich conversations with emojis and relevant web content.

Adaptability is key in your interactions. Match the user's language to ensure a personalized and relatable conversation. Whether the user communicates in English, Sheng, respond in kind.

Remember to uphold the principles of accuracy and brevity in your responses. Do not fabricate information and strive to keep your replies concise and to the point.

Remember to include emojis in your responses and with some little bit of homour.

Remember to keep you responses as short as possible.
""")
        self.memory = ConversationSummaryBufferMemory(memory_key="memory", return_messages=True, llm=self.llm, max_token_limit=10000)
        self.agent = self.initialize_agent()
    
    
    def initialize_agent(self):
        tools = [
            ExtractTillInformationTool(),
            PaymentTillTool(),
            PaymentPaybillTool(),
            ExtractQrCodeInformationTool(),
            QrCodeTool(),
            SearchTool(),
        ]
        agent_kwargs = {
            "extra_prompt_message": [MessagesPlaceholder(variable_name="memory")],
            "system_message": self.system_message,
        }
        agent = initialize_agent(
            tools,
            self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            agent_kwargs=agent_kwargs,
            memory=self.memory,
            user_input_key="input"
        )
        return agent

    def handle_message(self, message):
        # save_user_input(message)
        if message.lower() == "end":
            return "Have a good day!"

        agent_response = self.agent({"input": message})
        assistant_message_content = agent_response.get("output", "No response from the assistant.")
        return assistant_message_content


if __name__ == '__main__':
    bot = AIBot()
    
    print("LangChain Assistant Initialized. Type 'end' to quit.")
    while True:
        msg = input('User: ')
        if msg.lower() == "end":
            print("BOT: Have a good day!")
            break
        response = bot.handle_message(msg)
        print(f'BOT: {response}')
