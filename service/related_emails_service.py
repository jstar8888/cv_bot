import csv

from service.jobs_service import JOB_FILE

RELATED_EMAILS_FILE = "data/related_emails.csv"


def load_related_emails():

    emails = []

    with open(
        RELATED_EMAILS_FILE,
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        emails.extend(reader)

    return emails