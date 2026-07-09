from google.oauth2.credentials import Credentials
import os
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from database import supabase
import json
from dotenv import load_dotenv

load_dotenv()



SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CLIENT_SECRET_FILE = json.loads(
    os.environ["CLIENT_SECRET_FILE"]
)
TOKEN_FILE = "credentials/token.json"


def get_google_oauth():

    response = (
        supabase.table("secrets")
        .select("payload")
        .eq("key", "google_oauth")
        .execute()
    )

    if response.data:
        return response.data[0].get("payload")
    else:
        return None



def update_google_oauth(creds):
    (
        supabase.table("secrets")
        .upsert({
            "key": "google_oauth",
            "payload": json.loads(creds.to_json())
        })
        .execute()
    )

def get_credentials():
    data = get_google_oauth()

    if data:
        creds = Credentials.from_authorized_user_info(data, SCOPES)

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            update_google_oauth(creds)

        return creds

    # Không có dữ liệu OAuth -> đăng nhập lần đầu
    flow = InstalledAppFlow.from_client_config(
        CLIENT_SECRET_FILE,
        SCOPES
    )

    creds = flow.run_local_server(port=0)
    update_google_oauth(creds)
    return creds