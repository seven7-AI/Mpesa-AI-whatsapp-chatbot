import json
import requests
import logging
from whatsapp_configuration.config import Config
from flask import current_app as app


def log_http_response(response):
    """Utility function to log http response

    Args:
        response (requests.Response): HTTP response received
    """
    
    logging.info(f'Status: {response.status_code}')
    logging.info(f'Content-type: {response.headers.get("content-type")}')
    logging.info(f'Body: {response.text}')


def is_valid_whatsapp_message(body):
    """Check if the webhook event's body has the format of a valid Whatsapp message

    Args:
        body (dict): body object received from the webhook

    Returns:
        boolean: True if the format is valid, False otherwise
    """
    
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )


def create_text_message(recipient: str, text: str):
    """Create request body for whatsapp message with custom text

    Args:
        recipient (str): Recipient WAID
        text (str): Text to send to recipient

    Returns:
        str: JSONified string with payload
    """ 
    return json.dumps({
        'messaging_product': 'whatsapp', 
        'recipient_type': 'individual', 
        'to': recipient, 
        'type': 'text', 
        'text': {'preview_url': False, 'body': text}
    })


def send_message(data):
    """Function to send message to user using Graph API

    Args:
        data (string): JSON string with the message information
    
    Returns:
        dict: dictionary with status of the response
    """
    headers = {
        'Content-type': 'application/json',
        'Authorization': f'Bearer {Config.ACCESS_TOKEN}'
    }
    
    url = f'https://graph.facebook.com/{Config.VERSION}/{Config.PHONE_NUMBER_ID}/messages'
    
    try:
        response = requests.post(url, 
                                 data=data, 
                                 headers=headers, 
                                 timeout=20) #timeout after 20 seconds without reply from server
        response.raise_for_status() #raises exception if HTTP request is not successful
    except requests.Timeout:
        logging.error('Timeout occurred while sending message')
        return {'status': 'error', 'message': 'Request timed out'}
    except requests.RequestException as e:
        logging.error(f'Request failed: {e}')
        return {'status': 'error', 'message': 'Failed to send message'}
    
    #no errors so return success dictionary
    log_http_response(response)
    return {'status': 'success', 'message': 'Failed to send message'}


def process_whatsapp_message(body):
    """Function to process a Whatsapp message received from the user and send reply

    Args:
        body (dict): Dictionary with the message information
    """
    
    user_waid = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    user_name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"]
    
    #use AI chatbot to generate the response to the user
    resp = app.bot_instance.handle_message(message_body)
    
    # resp = message_body + '-> resp'
    #send the response back to the user
    msg_payload = create_text_message(user_waid, resp)
    send_message(msg_payload)