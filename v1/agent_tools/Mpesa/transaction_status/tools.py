
# def check_transaction_status():
#     try:
#         # Get data from the request
#         data = request.json

#         # Update the URL for checking transaction status
#         transaction_status_url = 'https://sandbox.safaricom.co.ke/mpesa/transactionstatus/v1/query'

#         # Get the access token
#         access_token_response = get_access_token()
#         if isinstance(access_token_response, dict):
#             access_token = access_token_response.get('access_token')
#             if access_token:
#                 # Update headers with the access token
#                 headers = {
#                     'Content-Type': 'application/json',
#                     'Authorization': 'Bearer ' + access_token
#                 }

#                 # Send a POST request to check transaction status
#                 transaction_status_response = requests.post(transaction_status_url, json=data, headers=headers).json()

#                 # Print the response from checking transaction status
#                 print(transaction_status_response)

#                 # Return the response from checking transaction status
#                 return jsonify(transaction_status_response)
#             else:
#                 return jsonify({'error': 'Access token not found.'}), 500
#         else:
#             return jsonify({'error': 'Failed to retrieve access token.'}), 500

#     except Exception as e:
#         return json.dumps({'error': f'Error processing request: {str(e)}'})