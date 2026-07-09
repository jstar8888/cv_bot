import json
import os
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from database import supabase

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Đọc cấu hình client từ biến môi trường JSON
CLIENT_SECRET_FILE = json.loads(os.environ["CLIENT_SECRET_FILE"])


def get_google_oauth():
    try:
        response = (
            supabase.table("secrets")
            .select("payload")
            .eq("key", "google_oauth")
            .single()
            .execute()
        )
        return response.data.get("payload") if response.data else None
    except Exception:
        # Trả về None nếu chưa có bản ghi nào trong Database
        return None


def update_google_oauth(creds):
    # Dùng upsert để nếu chưa có key "google_oauth" thì tạo mới, có rồi thì cập nhật
    supabase.table("secrets").upsert({
        "key": "google_oauth",
        "payload": json.loads(creds.to_json())
    }).execute()


def get_authorization_url(redirect_uri):
    
    flow = Flow.from_client_config(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    
    # access_type='offline' và prompt='consent' để ép Google luôn trả về Refresh Token
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes="true",
        prompt='consent'
    )
    
    return authorization_url, flow.code_verifier  # Trả về cả code_verifier để dùng trong bước callback


def handle_google_callback(authorization_response_url, redirect_uri, session):
    
    flow = Flow.from_client_config(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    flow.code_verifier = session["code_verifier"]
    
    # Đổi mã code lấy Credentials
    flow.fetch_token(authorization_response=authorization_response_url)

    creds = flow.credentials
    
    # Lưu credentials này vào Supabase
    update_google_oauth(creds)
    
    return creds


def get_credentials():
    
    data = get_google_oauth()
    if not data:
        return None  # Hệ thống cần bắt user đăng nhập qua link từ hàm get_authorization_url

    creds = Credentials.from_authorized_user_info(data, SCOPES)

    # Nếu token hết hạn, tự động dùng Refresh Token để lấy Access Token mới
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            update_google_oauth(creds)  # Lưu lại token mới vào DB
        except Exception:
            # Nếu Refresh token cũng bị hủy hoặc lỗi, coi như không hợp lệ
            return None

    # Xóa bỏ hoàn toàn InstalledAppFlow và việc ghi file cục bộ (TOKEN_FILE)
    if not creds or not creds.valid:
        return None

    return creds