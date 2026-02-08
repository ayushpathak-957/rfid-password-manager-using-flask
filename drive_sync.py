import os

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


# ---- CONFIG ----
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_FILE = "token.json"
FILE_ID_STORE = "drive_file_id.txt"
LOCAL_FILE = "password.txt"


def _get_drive_service():
    """
    Handles authentication and returns a Google Drive service object.
    """

    creds = None

    # Load saved token if it exists
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid credentials, login or refresh
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for future runs
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def sync_password_file():
    """
    Uploads password.txt to Google Drive once.
    Updates the same file on later calls.
    """

    service = _get_drive_service()
    media = MediaFileUpload(LOCAL_FILE)

    try:
        # ---- UPDATE EXISTING FILE ----
        if os.path.exists(FILE_ID_STORE):
            with open(FILE_ID_STORE, "r") as f:
                file_id = f.read().strip()

            service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()

            print("🔄 password.txt updated on Google Drive")

        # ---- FIRST TIME UPLOAD ----
        else:
            file_metadata = {"name": LOCAL_FILE}

            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id"
            ).execute()

            with open(FILE_ID_STORE, "w") as f:
                f.write(file["id"])

            print("☁️ password.txt uploaded to Google Drive (first time)")

    except HttpError as error:
        print("❌ Google Drive error:")
        print(error)
