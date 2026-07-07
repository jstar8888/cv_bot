import os
import json
from flask import Flask, session
from flask import render_template
from flask import request
from flask import redirect
from werkzeug.utils import secure_filename
from parser.extractor import extract_text
from parser.ai_extract import extract_cv
from service.sheet_service import *
from service.drive_service import upload_cv
from service.jobs_service import get_all_job_names
from datetime import datetime
from auth2 import (
    authenticate_user,
    load_hr,
    add_hr,
    delete_hr,
    update_hr,
    load_shared_email,
    add_shared_email,
    delete_shared_email,
    update_shared_email
)


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


import re
import unicodedata


def normalize_filename(text):

    text = unicodedata.normalize(
        "NFD",
        text
    )

    text = text.encode(
        "ascii",
        "ignore"
    ).decode()

    text = re.sub(
        r"[^A-Za-z0-9 ]",
        "",
        text
    )

    text = text.title()

    return text.replace(
        " ",
        ""
    )

@app.route("/login")
def login_page():

    return render_template("login.html")

@app.route("/login", methods=["POST"])
def do_login():

    email = request.form["email"]
    password = request.form["password"]

    user = authenticate_user(email, password)

    if user:

        session["email"] = user["email"]
        session["name"] = user["name"]

        if user["role"] == "admin":
            session["role"] = "admin"
            return redirect("/admin")

        session["role"] = "hr"
        return redirect("/")

    return render_template(
        "login.html",
        error="Sai tài khoản hoặc mật khẩu!"
    )

@app.route("/")
def index():

    if "email" not in session:

        return redirect("/login")
    
    related_emails = load_shared_email()
    job_names = get_all_job_names()

    return render_template(

        "index.html",

        email=session["email"],

        name=session["name"],

        related_emails=related_emails,

        job_names=job_names

    )

@app.route("/admin")
def admin():

    if "email" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Permission Denied"

    users = load_hr()
    shared_emails = load_shared_email()

    return render_template(
        "admin.html",
        users=users,
        shared_emails=shared_emails
    )

@app.route("/admin/hr/add", methods=["POST"])
def admin_hr_add():

    if session.get("role") != "admin":
        return "Permission Denied"

    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    add_hr(email, password, name)

    return redirect("/admin")


@app.route("/admin/hr/delete/<email>")
def admin_hr_delete(email):

    if session.get("role") != "admin":
        return "Permission Denied"

    delete_hr(email)

    return redirect("/admin")


@app.route("/admin/hr/edit/<email>")
def admin_hr_edit(email):

    if session.get("role") != "admin":
        return "Permission Denied"

    users = load_hr()

    user = None

    for hr in users:
        if hr["email"] == email:
            user = hr
            break

    return render_template(
        "edit_hr.html",
        user=user
    )


@app.route("/admin/hr/update", methods=["POST"])
def admin_hr_update():

    if session.get("role") != "admin":
        return "Permission Denied"

    email = request.form["email"]
    name = request.form["name"]
    password = request.form["password"]

    update_hr(email, password, name)

    return redirect("/admin")

@app.route("/admin/email/add", methods=["POST"])
def admin_email_add():

    if session.get("role") != "admin":
        return "Permission Denied"

    email = request.form["email"]

    add_shared_email(email)

    return redirect("/admin")


@app.route("/admin/email/delete/<email>")
def admin_email_delete(email):

    if session.get("role") != "admin":
        return "Permission Denied"

    delete_shared_email(email)

    return redirect("/admin")


@app.route("/admin/email/edit/<email>")
def admin_email_edit(email):

    if session.get("role") != "admin":
        return "Permission Denied"

    emails = load_shared_email()

    item = None

    for e in emails:
        if e["email"] == email:
            item = e
            break

    return render_template(
        "edit_email.html",
        item=item
    )


@app.route("/admin/email/update", methods=["POST"])
def admin_email_update():

    if session.get("role") != "admin":
        return "Permission Denied"

    old_email = request.form["old_email"]
    new_email = request.form["new_email"]

    update_shared_email(
        old_email,
        new_email
    )

    return redirect("/admin")

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

@app.route("/upload", methods=["POST"])
def upload():

    files = request.files.getlist("cv_files")
    related_emails = request.form.getlist("related_emails")
    selected_job = request.form.get("job_name")

    success_count = 0
    failed_files = []

    for file in files:

        try:

            filename = secure_filename(file.filename)

            save_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            file.save(save_path)

            text = extract_text(save_path)

            candidate = extract_cv(text, selected_job)

            if selected_job == "Auto Detect":
                position = candidate["job_name"]
            else:
                position = selected_job

            candidate["job_name"] = position

            name = normalize_filename(candidate["full_name"])

            position = normalize_filename(position)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            extension = os.path.splitext(filename)[1]

            new_filename = f"{position}_{name}_{timestamp}{extension}"

            drive_link = upload_cv(
                save_path,
                new_filename,
                position
            )

            candidate["drive_link"] = drive_link

            candidate["uploader_email"] = session["email"]

            candidate["related_emails"] = "\n".join(
                related_emails
            )

            row = find_by_email(candidate["email"])

            if row is None:
                append_candidate(candidate)
            else:
                update_candidate(row, candidate)

            success_count += 1

        except Exception as e:

            print(e)

            failed_files.append(
                f"{file.filename}: {str(e)}"
            )

    if not failed_files:

        return f"""
        <script>
        alert('Upload thành công {success_count} file!');
        window.location.href='/';
        </script>
        """

    message = (
        f"Upload thành công {success_count} file.\\n\\n"
        f"Lỗi {len(failed_files)} file:\\n\\n"
        + "\\n".join(failed_files)
    )

    return f"""
    <script>
    alert({message!r});
    window.location.href='/';
    </script>
    """

if __name__ == "__main__":
    app.run(debug=True)


#if __name__ == "__main__":
  #  app.run(host='0.0.0.0', port=5000,debug=True)