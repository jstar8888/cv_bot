from datetime import datetime
import os
import gspread
from zoneinfo import ZoneInfo
from service.google_service import get_credentials
from dotenv import load_dotenv


load_dotenv()


credentials = get_credentials()

client = gspread.authorize(credentials)

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")

sheet = client.open_by_key(
    SPREADSHEET_ID
).sheet1


import uuid

def generate_cv_id():
    return "CV" + uuid.uuid4().hex[:12].upper()

def find_by_email(email):

    emails = sheet.col_values(6)

    for index, value in enumerate(emails):

        if value.lower() == email.lower():

            return index + 1

    return None


def append_candidate(candidate):

    row = [

        datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y-%m-%d %H:%M:%S"),

        generate_cv_id(),

        candidate["full_name"],

        candidate["gender"],

        "", #DOB

        candidate["email"],

        candidate["phone"],

        candidate["city"],

        candidate["job_name"],

        "", #JOB_LEVEL

        candidate["exp"],

        candidate["exp_bank"],

        candidate["drive_link"], #LINK_CV

        "", #STATUS

        "", #RANKING

        "", #SOURCE

        candidate["uploader_email"], #HR_USER

        "", #NOTET

        candidate["skills"],

        "", #ID_RECRUITMENT

        candidate["related_emails"], #SHARE_

    ]

    sheet.append_row(row)


def update_candidate(row, candidate):

    values = [

        datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y-%m-%d %H:%M:%S"),

        sheet.cell(row,2).value,

        candidate["full_name"],

        candidate["gender"],

        "", #DOB

        candidate["email"],

        candidate["phone"],

        candidate["city"],

        candidate["job_name"],

        "", #JOB_LEVEL

        candidate["exp"],

        candidate["exp_bank"],

        candidate["drive_link"], #LINK_CV

        "", #STATUS

        "", #RANKING

        "", #SOURCE

        candidate["uploader_email"], #HR_USER

        "", #NOTET

        candidate["skills"],

        "", #ID_RECRUITMENT

        candidate["related_emails"], #SHARE_

    ]

    sheet.update(

        f"A{row}:U{row}",

        [values]

    )
