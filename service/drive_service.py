import os
import re
from dotenv import load_dotenv


load_dotenv()



from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from service.gg_service2 import get_credentials



# Folder trên Google Drive
FOLDER_ID = os.getenv("FOLDER_ID")





# ==========================
# GOOGLE DRIVE SERVICE
# ==========================
def get_drive_service():
    credentials = get_credentials()
    service = build(
        "drive",
        "v3",
        credentials=credentials
    )
    return service



def normalize_folder_name(folder_name):

    folder_name = folder_name.strip()

    folder_name = re.sub(
        r'[\\/*?:"<>|]',
        "_",
        folder_name
    )

    return folder_name


def get_or_create_folder(folder_name,drive_service):

    folder_name = normalize_folder_name(folder_name)

    query = (
        f"'{FOLDER_ID}' in parents and "
        f"name='{folder_name}' and "
        "mimeType='application/vnd.google-apps.folder' and "
        "trashed=false"
    )


    result = drive_service.files().list(
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

    folder = drive_service.files().create(

        body=metadata,

        fields="id"

    ).execute()

    print(f"Created folder: {folder_name}")

    return folder["id"]


# ==========================
# UPLOAD FILE
# ==========================

def upload_cv(file_path, new_filename, folder_name, drive_service):
   
    folder_id = get_or_create_folder(folder_name,drive_service)

    metadata = {
        "name": new_filename,
        "parents": [folder_id]
    }

    media = MediaFileUpload(
        file_path,
        resumable=True
    )

    
    file = drive_service.files().create(
        body=metadata,
        media_body=media,
        fields="id"
    ).execute()

    file_id = file["id"]

    print("Upload thành công:")

    # Public link (Anyone with link can view)
    try:
        drive_service.permissions().create(
            fileId=file_id,
            body={
                "type": "anyone",
                "role": "reader"
            }
        ).execute()

    except Exception as e:
        print("Không thể public file:", e)

    return f"https://drive.google.com/file/d/{file_id}/view"


