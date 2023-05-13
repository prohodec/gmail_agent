import os
import base64
import re

from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import googleapiclient.discovery
from email.mime.text import MIMEText


CLIENT_SECRETS_FILE = "credentials.json"
CLIENT_TOKEN = "token.json"

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", 'https://www.googleapis.com/auth/gmail.send']
API_SERVICE_NAME = 'gmail'
API_VERSION = 'v1'

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


def send_message(message_id, subject, message):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

    gmail = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    message_encoded = gmail.users().messages().get(userId='me', id=message_id).execute()

    sender = get_message_body(message_encoded)
    sender = sender["sender"]

    message = MIMEText(message)
    message['to'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        message = gmail.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        print(f'Message Id: {message["id"]}')
    except HttpError as error:
        print(f'An error occurred: {error}')
    return


def open_gmail_message(message_id):
    url = "https://mail.google.com/mail/u/0/#inbox/" + message_id
    return url
