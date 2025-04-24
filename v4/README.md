# M-Pesa Chat Agent

A versatile chat agent that integrates M-Pesa payment capabilities and web search functionality, with support for WhatsApp and Telegram messaging platforms.

## Features

- **M-Pesa Integration**: Process both Till and Paybill payments
- **Web Search**: Search the web for information using Google Search API
- **Multi-Platform Support**: Integrations with WhatsApp and Telegram
- **Extensible Architecture**: Easily add new tools and capabilities
- **FastAPI Backend**: Modern, high-performance web framework

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mpesa-chat-agent
```

2. Install dependencies:
```bash
pip install mpesa-integration langchain langchain-openai openai python-dotenv fastapi uvicorn google-api-python-client google-search-results python-telegram-bot twilio pydantic
```

3. Set up environment variables:
Create a `.env` file in the project root with the following variables:

```
# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# M-Pesa Till Configuration
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_PASSKEY=your_passkey
MPESA_SHORTCODE=your_till_number
MPESA_CALLBACK_URL=https://your-domain.com/whatsapp/webhook
MPESA_ENVIRONMENT=sandbox  # or "production"

# M-Pesa Paybill Configuration (if using Paybill)
MPESA_BUSINESS_SHORTCODE=your_paybill_number

# Google Search API
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_custom_search_engine_id

# Alternative: SerpAPI (if not using Google API)
SERPAPI_API_KEY=your_serpapi_key

# WhatsApp via Twilio
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=your_twilio_whatsapp_number

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

## Usage

### Running the Server

Start the FastAPI server:

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### API Endpoints

- **Web Chat**: `POST /chat`
  - Request body: `{"message": "your message", "user_id": "unique_user_id"}`
  - Response: `{"response": "agent response"}`

- **WhatsApp Webhook**: `POST /whatsapp/webhook`
  - Handles incoming WhatsApp messages via Twilio

- **Health Check**: `GET /health`
  - Returns the status of all components

### Testing

Run the test script to verify all components are working correctly:

```bash
python test_agent.py
```

## Architecture

The system consists of the following components:

1. **Chat Agent** (`chat_agent.py`): Core agent that processes messages using LangChain and OpenAI
2. **M-Pesa Tools** (`mpesa_tool.py`): Tools for processing Till and Paybill payments
3. **Search Tool** (`search_tool.py`): Tool for web searches using Google Search API
4. **WhatsApp Integration** (`whatsapp_integration.py`): Integration with WhatsApp via Twilio
5. **Telegram Integration** (`telegram_integration.py`): Integration with Telegram Bot API
6. **Main Application** (`main.py`): FastAPI application that ties everything together

## Extending the Agent

### Adding New Tools

To add a new tool to the agent:

1. Create a new tool class that extends `BaseTool` from LangChain
2. Implement the `_run` method to define the tool's functionality
3. Add the tool to the agent using the `add_tool` method:

```python
from chat_agent import ChatAgent
from my_custom_tool import MyCustomTool

# Initialize the chat agent
chat_agent = ChatAgent()

# Create and add the custom tool
custom_tool = MyCustomTool()
chat_agent.add_tool(custom_tool)
```

### Adding New Messaging Platforms

To add a new messaging platform:

1. Create a new integration class similar to `WhatsAppIntegration` or `TelegramIntegration`
2. Initialize the integration with the chat agent
3. Add the necessary endpoints to the FastAPI application in `main.py`

## Production Deployment

For production deployment:

1. Set `MPESA_ENVIRONMENT=production` in your `.env` file
2. Ensure your callback URL is publicly accessible and properly configured in the Safaricom Developer Portal
3. Use a production-ready server like Gunicorn:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   ```
4. Consider using a process manager like Supervisor or PM2
5. Set up proper logging and monitoring

## License

[MIT License](LICENSE)
