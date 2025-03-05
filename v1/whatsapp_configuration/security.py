from functools import wraps
from flask import jsonify, request
import logging
import hashlib
import hmac

from whatsapp_configuration.config import Config


def validate_signature(payload, signature):
    """  
    Use message authentication code (MAC) to guarantee the authenticity of the data sender
    The private key used is the APP_SECRET variable

    Args:
        payload (string): text data received
        signature (string): hash received (MAC) -> should be hash of payload

    Returns:
        boolean: True if the two hashes match, false otherwise
    """
    
    print(Config.APP_SECRET)
    #use the APP_SECRET private key to hash the payload
    expected_signature = hmac.new(
        bytes(Config.APP_SECRET, "latin-1"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    #check if the signature payload matches the expected signature
    return hmac.compare_digest(expected_signature, signature)



def signature_required(f):
    """Decorator using the validate_signature function to check if the payload received
       has a valid signature, before running code for each endpoint

    Args:
        f (function): Function to be executed inside endpoint if validation passes

    Returns:
        function: Error dictionary or output of f (similar to a monad)
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        signature = request.headers.get("X-Hub-Signature-256", "")[7:] #Removing 'sha256='
        if not validate_signature(request.data.decode("utf-8"), signature):
            logging.info("Signature verification failed!")
            return jsonify({"status": "error", "message": "Invalid signature"}), 403
        return f(*args, **kwargs)

    return decorated_function