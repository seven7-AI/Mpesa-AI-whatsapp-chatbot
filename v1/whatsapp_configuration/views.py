"""Flask webhook endpoints which get triggered when message from client is received"""

from flask import Blueprint, request, jsonify
import logging
import json 

from whatsapp_configuration.config import Config
from whatsapp_configuration.security import signature_required
from whatsapp_configuration.whatsapp_api import (
    is_valid_whatsapp_message, 
    process_whatsapp_message
)
from ai_bot_langchain import AIBot

webhook_blueprint = Blueprint("webhook", __name__)


#handle POST requests to /webhook
def handle_message():
    """Handle incoming webhook events from the whatsapp API
       The webhook event can be a whatsapp message or a status update
       
       Returns:
        response: Tuple containing server response and status code
    """
    
    body = request.get_json()
    
    #check if event received is a whatsapp status update
    if (
        body.get('entry', [{}])[0]
        .get('changes', [{}])[0]
        .get('value', {})
        .get('statuses')
    ):
        logging.info('Received Whatsapp status update')
        return jsonify({'status': 'ok'}), 200

    
    try:
        #check if the event received is a whatsapp message
        if is_valid_whatsapp_message(body):
            #if it is process the whatsapp message
            process_whatsapp_message(body)
            return jsonify({'status': 'ok'}), 200
        else:
            #event received is not a Whatsapp event, hence return an error=
            return jsonify({'status': 'error', 'message': 'Not a WhatsApp API event'})
    
    except Exception as e:
        logging.error(f'Failed to process event: {e}')
        return jsonify({'status': 'error', 'message': f'Failed to process event: {e}'}), 400
    
        
        
#handle GET requests to /webhook (verification)
def verify():
    #parse request query parameters
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    #check if both a token and mode were send
    if mode and token:
        #check if mode and token sent are correct, to verify the authenticity of the sender
        if mode == 'subscribe' and token == Config.VERIFY_TOKEN:
            logging.info('Webhook verified successfully.')
            return challenge, 200
        else:
            #incorrect token / mode
            logging.info('Webhook verification failed')
            return jsonify({'status': 'error', 'message': 'Verification failed'}), 403
    else:
        #missing paramters
        logging.info('Verification failed')
        return jsonify({'status': 'error', 'message': 'Verification failed'}), 400
        


#attach functions to webhook blueprint
#explanation of flask blueprints: https://realpython.com/flask-blueprint/#:~:text=Each%20Flask%20Blueprint%20is%20an,before%20you%20can%20run%20it.
#(blueprints are a simple feature to embelish code)
@webhook_blueprint.route('/webhooks', methods=['GET'])
def webhook_get():
    return verify()


@webhook_blueprint.route('/webhooks', methods=['POST'])
@signature_required
def webhook_post():
    return handle_message()