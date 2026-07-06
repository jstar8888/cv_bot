import os
import re
from dotenv import load_dotenv


load_dotenv()



from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from service.google_service import get_credentials



# Folder trên Google Drive
FOLDER_ID = os.getenv("FOLDER_ID")





# ==========================
# GOOGLE DRIVE SERVICE
# ==========================

credentials = get_credentials()

service = build(
    "drive",
    "v3",
    credentials=credentials
)


def normalize_folder_name(folder_name):

    folder_name = folder_name.strip()

    folder_name = re.sub(
        r'[\\/*?:"<>|]',
        "_",
        folder_name
    )

    return folder_name


def get_or_create_folder(folder_name):

    folder_name = normalize_folder_name(folder_name)

    query = (
        f"'{FOLDER_ID}' in parents and "
        f"name='{folder_name}' and "
        "mimeType='application/vnd.google-apps.folder' and "
        "trashed=false"
    )

    result = service.files().list(
        q=query,
        fields="files(id,name)"
    ).execute()

    folders = result.get("files", [])

    if folders:

        return folders[0]["id"]

    metadata = {

        "name": folder_name,

        "mimeType": "application/vnd.google-apps.folder",

        "parents": [FOLDER_ID]

    }

    folder = service.files().create(

        body=metadata,

        fields="id"

    ).execute()

    print(f"Created folder: {folder_name}")

    return folder["id"]


# ==========================
# UPLOAD FILE
# ==========================

def upload_cv(file_path, new_filename, folder_name):
   
    folder_id = get_or_create_folder(folder_name)

    metadata = {
        "name": new_filename,
        "parents": [folder_id]
    }

    media = MediaFileUpload(
        file_path,
        resumable=True
    )

    file = service.files().create(
        body=metadata,
        media_body=media,
        fields="id"
    ).execute()

    file_id = file["id"]

    print(f"Upload thành công: {file_id}")

    # Public link (Anyone with link can view)
    try:
        service.permissions().create(
            fileId=file_id,
            body={
                "type": "anyone",
                "role": "reader"
            }
        ).execute()

    except Exception as e:
        print("Không thể public file:", e)

    return f"https://drive.google.com/file/d/{file_id}/view"


