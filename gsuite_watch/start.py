import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Setup the Admin SDK API
SCOPES = ['https://www.googleapis.com/auth/admin.directory.user.readonly']

def get_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    try:
        creds = Credentials.from_authorized_user_file('token.json')
    except IOError:
        # If there are no (valid) credentials available, prompt the user to log in.
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def watch_users():
    credentials = get_credentials()
    service = build('admin', 'directory_v1', credentials=credentials)

    # Assume 'your_domain.com' is the domain you're querying. 
    # You'd replace this with your actual domain or use 'my_customer' for your own domain
    domain_name = 'brig.gs'

    try:
        # Set up a channel for notifications
        channel = {
            "id": "site",  # Unique identifier
            "type": "web_hook",  # The type of delivery mechanism
            "address": "https://webhook.site/5fcc1723-68e9-442a-8a63-b99b76d64727"  # Your webhook URL to get notifications
        }

        results = service.users().watch(
            domain=domain_name, 
            body=channel,
        ).execute()

        print(results)
    
        
        
    except HttpError as error:
        print(f'An error occurred: {error}')

if __name__ == '__main__':
    watch_users()
