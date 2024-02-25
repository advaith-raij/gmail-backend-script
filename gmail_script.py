import os
import json
import sqlite3
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from tqdm import tqdm

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def authenticate():
    """
    Authenticate to Gmail API using OAuth.
    """
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def list_labels(service):
    """
    List all labels in the user's Gmail account.
    """
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(f'- {label["name"]} (ID: {label["id"]})')

def fetch_all_messages(service):
    """
    Fetch all messages from Gmail.
    """
    results = service.users().messages().list(userId='me').execute()
    messages = results.get('messages', [])
    return messages

    # messages = []
    # page_token = None
    # while True:
    #     results = service.users().messages().list(userId='me', pageToken=page_token).execute()
    #     messages.extend(results.get('messages', []))
    #     page_token = results.get('nextPageToken')
    #     if not page_token:
    #         break
    # return messages

def create_database():
    """
    Create SQLite database to store emails.
    """
    conn = sqlite3.connect('emails.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS emails
                 (id TEXT PRIMARY KEY, from_email TEXT, subject TEXT, message TEXT, received DATETIME)''')
    conn.commit()
    conn.close()

def store_emails(service):
    """
    Store fetched emails in SQLite database.
    """
    messages = fetch_all_messages(service)
    conn = sqlite3.connect('emails.db')
    c = conn.cursor()
    for message in tqdm(messages, desc="Storing Emails"):
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        id = msg['id']
        headers = msg['payload']['headers']
        from_email = next((header['value'] for header in headers if header['name'] == 'From'), '')
        subject = next((header['value'] for header in headers if header['name'] == 'Subject'), '')
        message_body = msg['snippet']
        received_time = datetime.datetime.fromtimestamp(int(msg['internalDate'])/1000)
        c.execute("INSERT OR REPLACE INTO emails (id, from_email, subject, message, received) VALUES (?, ?, ?, ?, ?)",
                  (id, from_email, subject, message_body, received_time))
    conn.commit()
    conn.close()

def load_rules(filename):
    """
    Load rules from JSON file.
    """
    with open(filename) as f:
        rules = json.load(f)
    return rules

def apply_rule(rule, email):
    """
    Apply rule to email.
    """
    conditions = rule['conditions']
    predicate = rule['predicate']
    if predicate == 'All':
        return all(condition_matches(condition, email) for condition in conditions)
    elif predicate == 'Any':
        return any(condition_matches(condition, email) for condition in conditions)

def condition_matches(condition, email):
    """
    Check if condition matches email.
    """
    field = condition['field']
    predicate = condition['predicate']
    value = condition['value']
    if field == 'From':
        if predicate == 'Contains':
            return value in email['from_email']
        elif predicate == 'Does not Contain':
            return value not in email['from_email']
        elif predicate == 'Equals':
            return value == email['from_email']
    elif field == 'Subject':
        if predicate == 'Contains':
            return value in email['subject']
        elif predicate == 'Does not Contain':
            return value not in email['subject']
        elif predicate == 'Equals':
            return value == email['subject']
    elif field == 'Message':
        if predicate == 'Contains':
            return value in email['message']
        elif predicate == 'Does not Contain':
            return value not in email['message']
        elif predicate == 'Equals':
            return value == email['message']
    elif field == 'Received Date/Time':
        received_time = email['received']
        if predicate == 'Less than':
            return received_time < datetime.datetime.now() - datetime.timedelta(days=value)
        elif predicate == 'Greater than':
            return received_time > datetime.datetime.now() - datetime.timedelta(days=value)
    return False

def process_emails(service, rules):
    """
    Process emails based on rules and take actions.
    """
    conn = sqlite3.connect('emails.db')
    c = conn.cursor()
    c.execute("SELECT * FROM emails")
    rows = c.fetchall()
    for row in tqdm(rows, desc="Processing Emails"):
        email = {
            'from_email': row[1],
            'subject': row[2],
            'message': row[3],
            'received': row[4]
        }
        for rule in rules:
            if apply_rule(rule, email):
                print("Email matching rule:", email)
                perform_actions(rule, row[0], service)
                break
    conn.close()

def perform_actions(rule, email_id, service):
    """
    Perform actions on email based on rule.
    """
    actions = rule['actions']
    for action in actions:
        if action == 'Mark as read':
            service.users().messages().modify(userId='me', id=email_id, body={'removeLabelIds': ['UNREAD']}).execute()
        elif action == 'Mark as unread':
            service.users().messages().modify(userId='me', id=email_id, body={'addLabelIds': ['UNREAD']}).execute()
        elif action.startswith('Move Message:'):
            label = action.split(':')[1].strip()
            move_message(service, email_id, label)

def move_message(service, email_id, label_name):
    """
    Move message to the specified label.
    """
    label_id = get_label_id(service, label_name)
    if label_id:
        print(f"Label ID for '{label_name}': {label_id}")
        try:
            service.users().messages().modify(userId='me', id=email_id, body={'addLabelIds': [label_id]}).execute()
            print("Message moved successfully.")
        except Exception as e:
            print(f"Error moving message: {e}")
    else:
        print(f"Label '{label_name}' not found.")

def get_label_id(service, label_name):
    """
    Get the label ID for the given label name.
    """
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    for label in labels:
        if label['name'] == label_name:
            return label['id']
    return None

def main():
    creds = authenticate()
    service = build('gmail', 'v1', credentials=creds)
    list_labels(service)
    create_database()
    store_emails(service)
    rules = load_rules('rules.json')
    process_emails(service, rules)

if __name__ == '__main__':
    main()