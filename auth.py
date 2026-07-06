import csv
import email

HR_FILE = "data/hr.csv"
ADMIN_FILE = "data/admin.csv"
SHARED_EMAIL_FILE = "data/related_email.csv"


def authenticate_user(email, password):

    admins = read_users(ADMIN_FILE)
    
    print(email, password)


    print(admins)

    for admin in admins:

        if admin["email"] == email and admin["password"] == password:

            admin["role"] = "admin"

            return admin

    hrs = read_users(HR_FILE)

    for hr in hrs:

        if hr["email"] == email and hr["password"] == password:

            hr["role"] = "hr"

            return hr

    return None

def read_users(file_path):

    users = []

    with open(file_path, encoding="utf-8") as file:

        reader = csv.DictReader(file)

        users.extend(reader)

    return users

def add_hr(email, password, name):

    with open(
        HR_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            email,
            password,
            name
        ])

def load_hr():

    return read_users(HR_FILE)

def delete_hr(email):

    users = load_hr()

    users = [
        u for u in users
        if u["email"] != email
    ]

    with open(
        HR_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "email",
            "password",
            "name"
        ])

        for u in users:

            writer.writerow([
                u["email"],
                u["password"],
                u["name"]
            ])

def update_hr(email, password, name):

    users = load_hr()

    for u in users:

        if u["email"] == email:

            u["password"] = password
            u["name"] = name

    with open(
        HR_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "email",
            "password",
            "name"
        ])

        for u in users:

            writer.writerow([
                u["email"],
                u["password"],
                u["name"]
            ])

def add_shared_email(email):

    with open(
        SHARED_EMAIL_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            email
        ])

def load_shared_email():

    return read_users(SHARED_EMAIL_FILE)

def delete_shared_email(email):

    emails = load_shared_email()

    emails = [
        e for e in emails
        if e["email"] != email
    ]

    with open(
        SHARED_EMAIL_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "email"
        ])

        for e in emails:

            writer.writerow([
                e["email"]
            ])

def update_shared_email(old_email, new_email):

    emails = load_shared_email()

    for e in emails:

        if e["email"] == old_email:

            e["email"] = new_email

    with open(
        SHARED_EMAIL_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "email"
        ])

        for e in emails:

            writer.writerow([
                e["email"]
            ])

