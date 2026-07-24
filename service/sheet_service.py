from datetime import datetime
import os
import gspread
from zoneinfo import ZoneInfo
from service.gg_service2 import get_credentials
from dotenv import load_dotenv


load_dotenv()
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")

def get_sheet():

    credentials = get_credentials()

    client = gspread.authorize(credentials)



    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    
    sheet = spreadsheet.worksheet(WORKSHEET_NAME)

    return sheet


import uuid

def generate_cv_id():
    return "CV" + uuid.uuid4().hex[:12].upper()

def find_by_email(email,sheet):

    
    emails = sheet.col_values(6)

    for index, value in enumerate(emails):

        if value.lower() == email.lower():

            return index + 1

    return None


def append_candidate(candidate,sheet):

    
    row = [

        datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%d/%m/%Y"),

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

        candidate["skills"],

        "", #NOTET

        "", #ID_RECRUITMENT

        candidate["related_emails"], #SHARE_

    ]
    
    sheet.append_row(row)


def update_candidate(row, candidate,sheet):

    
    values = [

        datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%d/%m/%Y"),

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

        candidate["skills"],

        "", #NOTET

        "", #ID_RECRUITMENT

        candidate["related_emails"], #SHARE_

    ]
    
    sheet.update(

        f"A{row}:U{row}",

        [values]

    )
