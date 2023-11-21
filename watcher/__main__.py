import argparse
import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Setup the Admin SDK API
SCOPES = ["https://www.googleapis.com/auth/admin.directory.user.readonly"]


def get_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    try:
        creds = Credentials.from_authorized_user_file("token.json")
    except IOError:
        # If there are no (valid) credentials available, prompt the user to log in.
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def watch_users(domain: str, channel_id: str, webhook_address: str):
    credentials = get_credentials()
    service = build("admin", "directory_v1", credentials=credentials)

    # Assume 'your_domain.com' is the domain you're querying.
    # You'd replace this with your actual domain or use 'my_customer' for your own domain
    domain_name = domain

    try:
        # Set up a channel for notifications
        channel = {
            "id": channel_id,  # Unique identifier
            "type": "web_hook",  # The type of delivery mechanism
            "address": webhook_address,  # Your webhook URL to get notifications
        }

        results = (
            service.users()
            .watch(
                domain=domain_name,
                body=channel,
            )
            .execute()
        )

        print("Channel created successfully!")
        print("Channel ID: " + results["id"])
        print("Resource ID: " + results["resourceId"])
        print("Destination: " + webhook_address)

    except HttpError as error:
        print(f"An error occurred: {error}")


def stop_channel(channel_id, resource_id):
    creds = get_credentials()
    service = build("admin", "directory_v1", credentials=creds)

    channel_to_stop = {"id": channel_id, "resourceId": resource_id}

    # Stop the channel
    try:
        service.channels().stop(body=channel_to_stop).execute()
        print(f"Channel {channel_id}  with ID {resource_id} stopped successfully!")
    except Exception as e:
        print(f"Error stopping channel: {e}")


def main():
    parser = argparse.ArgumentParser(description="Script with start and stop commands.")

    subparsers = parser.add_subparsers(title="commands", dest="command")

    start_parser = subparsers.add_parser("start", help="start action")
    start_parser.add_argument(
        "--domain", required=True, help="Domain name to operate on"
    )
    start_parser.add_argument(
        "--channel-id", required=True, help="The channel ID to create"
    )
    start_parser.add_argument(
        "--address", required=True, help="The webhook address to send notifications to"
    )

    stop_parser = subparsers.add_parser("stop", help="stop action")
    stop_parser.add_argument(
        "--channel-id", required=True, help="The channel ID to stop"
    )

    stop_parser.add_argument(
        "--resource-id", required=True, help="The resource id to stop"
    )

    args = parser.parse_args()

    if args.command == "start":
        watch_users(args.domain, args.channel_id, args.address)
    elif args.command == "stop":
        stop_channel(args.channel_id, args.resource_id)
    else:
        print("Please provide a valid command (start or stop).")
        parser.print_help()


if __name__ == "__main__":
    main()
