import csv

JOB_FILE = "data/positions.csv"


def load_jobs():

    jobs = []

    with open(
        JOB_FILE,
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        jobs.extend(reader)

    return jobs


def get_job_name(code):

    jobs = load_jobs()

    for job in jobs:

        if job["code"] == str(code):

            return job["position"]

    return None

def get_all_job_names():

    jobs = load_jobs()

    return [
        job["position"]
        for job in jobs
    ]