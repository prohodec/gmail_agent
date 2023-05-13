import os
import base64
import flask
import re
import json

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import googleapiclient.discovery

CLIENT_SECRETS_FILE = "credentials.json"
CLIENT_TOKEN = "token.json"

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", 'https://www.googleapis.com/auth/gmail.send']
API_SERVICE_NAME = 'gmail'
API_VERSION = 'v1'

# app = flask.Flask(__name__)
# app.secret_key = 'sdfjkgjks23432kldglsdg'


def get_message_body(message):
    message_payload = message['payload']
    headers = message_payload['headers']
    sender = ''
    subject = ''

    # Получаем тему сообщения
    for header in headers:
        if header['name'] == 'Subject':
            subject = header['value']
            break

    # Получаем отправителя
    for header in headers:
        if header['name'] == 'From':
            sender = re.search(r'<(.+)>', header['value']).group(1)
            break

    # Получаем основной текст сообщения
    if 'parts' in message_payload:
        parts = message_payload['parts']
        data = None
        for part in parts:
            if part['body'].get('data'):
                data = part['body']['data']
                break
        if data:
            text = base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            text = ''
    else:
        if message_payload['body'].get('data'):
            text = base64.urlsafe_b64decode(message_payload['body']['data']).decode('utf-8')
        else:
            text = ''

    text = text.replace('\r\n', ' ')
    return {"sender": sender, "text": text, "subject": subject}


def webhook_init():

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
    else:
        # Runs only when there is no token (before deployment, you need to generate a token once)
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=5050)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

    gmail = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=creds)

    # Subscribe to the push from Google, in order to fully test you need a public https
    request = {
        'labelIds': ['INBOX'],
        'topicName': 'projects/mailing-filter-with-ai/topics/id_for_mailing'
     }

    gmail.users().watch(userId='me', body=request).execute()

    return 'Subscription created'


def messages_handler():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

    gmail = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=creds)

    message_list = gmail.users().messages().list(userId='me', maxResults=1, q='label:INBOX').execute()
    message_list = message_list.get('messages', [])

    if not message_list:
        print('No messages found.')

    message_encoded = gmail.users().messages().get(userId='me', id=message_list[0]['id']).execute()
    message_decode = get_message_body(message_encoded)
    message_id = {"id": message_list[0]['id']}
    message_decode.update(message_id)


    # process_message(message_decode["id"], message_decode["subject"], message_decode["text"], message_decode["sender"])

    return message_decode


# @app.route('/webhooks', methods=["POST"])
# def new_messages_webhooks():
#     if flask.request.method == 'POST':
#         body = flask.request.get_json()
#         message_data = body['message']['data']
#         message_data_decoded = base64.urlsafe_b64decode(message_data.encode('UTF-8')).decode('UTF-8')
#         message_data_dict = json.loads(message_data_decoded)
#
#         email = message_data_dict['emailAddress']
#         print("Pub/sub push, new message at:", email)
#         messages_handler()
#
#     return {'success': True, 'message': 'Watch request executed successfully.'}, 200
#

if __name__ == '__main__':
    pass


    # os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    #
    # # Specify a hostname and port that are set as a valid redirect URI
    # # for your API project in the Google API Console.
    # app.run('127.0.0.1', 5000, debug=True, ssl_context="adhoc")



