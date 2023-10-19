import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/admin.directory.user.readonly']

# Load your credentials
def get_credentials():
    creds = None
    # The token.json is the file that contains your user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')

    # If there are no (valid) credentials available, prompt the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
    return creds

def stop_channel(channel_id, resource_id):
    creds = get_credentials()
    service = build('admin', 'directory_v1', credentials=creds)

    channel_to_stop = {
        "id": channel_id,
        "resourceId": resource_id
    }

    # Stop the channel
    try:
        service.channels().stop(body=channel_to_stop).execute()
        print(f"Channel {channel_id} stopped successfully!")
    except Exception as e:
        print(f"Error stopping channel: {e}")

if __name__ == "__main__":
    channel_id_input = "test"
    resource_id_input = "gnXQnBYCn-9L_6zVIqvzcy1rSXg"
    
    stop_channel(channel_id_input, resource_id_input)
