## Mpesa-AI-WhatsApp-Chatbot


https://github.com/Kevin7744/Mpesa-AI-whatsapp-chatbot/assets/105924200/ee33b4ac-3d5c-403e-b3f4-2e910bc4e749



The Mpesa-AI-WhatsApp-Chatbot is an innovative project that combines the power of OpenAI's language model and [LangChain's](https://python.langchain.com/docs/get_started/introduction/) capabilities to facilitate payments using the [MPESA-Daraja API](https://developer.safaricom.co.ke/). This chatbot aims to streamline the payment process by enabling users to interact with it through WhatsApp, making transactions more convenient and efficient.

### Usage

Follow these steps to set up and run the Mpesa-AI-WhatsApp-Chatbot:

1. **Clone the Repository**: Start by cloning the repository to your local machine using the following command:

    ```bash
    git clone https://github.com/Kevin7744/Mpesa-AI-whatsapp-chatbot.git
    ```

2. **Setup Facebook Developers Account**: Create a [Facebook Developers](https://developers.facebook.com/) account and import the necessary tokens. You can find resources to help you with this [here](https://youtu.be/3YPeh-3AFmM?si=fZh_jG_-2pQFcS-_).

3. **Install Requirements**: Install the required Python packages by running the following command:

    ```bash
    pip install -r requirements.txt
    ```

4. **Set Up Environment Variables**: Create a `.env` file in the project directory and add your OpenAI API key.

5. **Setup Ngrok**: Ngrok is used to expose your local server to the web. Setup Ngrok by following the instructions [here](https://dashboard.ngrok.com/get-started/setup/windows). Run the following commands to start Ngrok and add your authentication token:

    ```bash
    ngrok http 5000 --domain=<domain name>
    ngrok config add-authtoken <your auth token>
    ```

6. **Run the Chatbot**: Start the chatbot by running the `main.py` file:

    ```bash
    python main.py
    ```

### Project Structure

The project is structured as follows:

- **main.py**: Contains the main logic for the chatbot, including handling user messages, generating responses using OpenAI, and processing payments using the MPESA-Daraja API.

- **requirements.txt**: Lists all the required Python packages for the project. Install these packages using `pip install -r requirements.txt`.

- **.env**: Environment file to store sensitive information such as API keys. Create this file and add your OpenAI API key.

### Contributions

Contributions to the Mpesa-AI-WhatsApp-Chatbot project are welcome. If you have any suggestions, improvements, or feature requests, feel free to open an issue or submit a pull request on the GitHub repository.

### License

The Mpesa-AI-WhatsApp-Chatbot project is licensed under the [APACHE LICENSE](LICENSE). Feel free to use, modify, and distribute the code for your own projects.
