# def reverse_transaction():
#     try:
#         # Extract data from the request
#         data = request.json
#         initiator = data.get('Initiator')
#         security_credential = data.get('SecurityCredential')
#         command_id = data.get('CommandID')
#         transaction_id = data.get('TransactionID')
#         amount = data.get('Amount')
#         receiver_party = data.get('ReceiverParty')
#         receiver_identifier_type = data.get('ReceiverIdentifierType')
#         result_url = data.get('ResultURL')
#         queue_timeout_url = data.get('QueueTimeOutURL')
#         remarks = data.get('Remarks')
#         occasion = data.get('Occasion')

#         # Obtain the access token
#         access_token = get_access_token()
        
#         if access_token:
#             # Prepare the request body for the transaction reversal
#             reversal_data = {
#                 "Initiator": initiator,
#                 "SecurityCredential": security_credential,
#                 "CommandID": command_id,
#                 "TransactionID": transaction_id,
#                 "Amount": amount,
#                 "ReceiverParty": receiver_party,
#                 "RecieverIdentifierType": receiver_identifier_type,
#                 "ResultURL": result_url,
#                 "QueueTimeOutURL": queue_timeout_url,
#                 "Remarks": remarks,
#                 "Occasion": occasion
#             }

#             # Make a POST request to the reversal endpoint
#             reversal_url = 'https://sandbox.safaricom.co.ke/mpesa/reversal/v1/request'
#             headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

#             reversal_response = requests.post(reversal_url, json=reversal_data, headers=headers).json()

#             # Return the response from the transaction reversal
#             return jsonify(reversal_response)
#         else:
#             return jsonify({'error': 'Failed to retrieve access token.'}), 500

#     except Exception as e:
#         return json.dumps({'error': f'Error processing request: {str(e)}'})