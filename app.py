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
from zoneinfo import ZoneInfo
from service.gg_service2 import (get_credentials, handle_google_callback, get_authorization_url) 
from extensions import mail
from auth2 import (
    authenticate_user,
    load_hr,
    add_hr,
    delete_hr,
    update_hr,
    load_shared_email,
    add_shared_email,
    delete_shared_email,
    update_shared_email,
    get_user_by_email,
    update_user_password,
    save_reset_otp,
    verify_reset_otp,
    delete_reset_otp
)
from service.mail_service import (send_reset_otp, generate_otp)


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USER")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

mail.init_app(app)

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
        otp = generate_otp()

        save_reset_otp(email, otp)

        if not send_reset_otp(email, otp):
            return render_template(
                "login.html",
                error="Không thể gửi OTP. Vui lòng thử lại."
            )
        

        session["email"] = user["email"]

        if user["role"] == "admin":
            session["role"] = "admin"
            
        else:
            session["role"] = "hr"
        

        return render_template(
            "verify_otp.html",
            email=email,
            purpose="login"
    )

    return render_template(
        "login.html",
        error="Sai tài khoản hoặc mật khẩu!"
    )

@app.route("/forgot-password")
def forgot_password_page():
    return render_template("forgot_password.html")

@app.route("/forgot-password", methods=["POST"])
def forgot_password():

    email = request.form["email"]

    user = get_user_by_email(email)

    if not user:
        return render_template(
            "forgot_password.html",
            error="Email không tồn tại."
        )

    otp = generate_otp()

    save_reset_otp(email, otp)

    if not send_reset_otp(email, otp):
        return render_template(
            "forgot_password.html",
            error="Không thể gửi OTP. Vui lòng thử lại."
        )

    return render_template(
        "verify_otp.html",
        email=email,
        purpose="reset"
    )

@app.route("/verify-otp", methods=["POST"])
def verify_otp():

    purpose = request.form["purpose"]
    email = request.form["email"]
    otp = request.form["otp"]

    if not verify_reset_otp(email, otp):
        return render_template(
            "verify_otp.html",
            email=email,
            purpose=purpose,
            error="OTP không đúng."
        )

    if purpose == "reset":

        session["reset_email"] = email

        return render_template(
            "reset_password.html",
            email=email
        )

    elif purpose == "login":
        print(session["role"])
        if session["role"] == "admin":
            return redirect("/admin")

        return redirect("/")
    
@app.route("/reset-password", methods=["POST"])
def reset_password():

    email = session.get("reset_email")

    if not email:
        return redirect("/login")

    password = request.form["password"]
    confirm_password = request.form["confirm_password"]

    if password != confirm_password:
        return render_template(
            "reset_password.html",
            error="Mật khẩu xác nhận không khớp."
        )

    update_user_password(email, password)

    delete_reset_otp(email)

    session.pop("reset_email", None)

    return redirect("/login")

@app.route("/resend-otp", methods=["POST"])
def resend_otp():

    email = request.form["email"]

    if not get_user_by_email(email):
        return render_template(
            "forgot_password.html",
            error="Email không tồn tại."
        )

    otp = generate_otp()

    save_reset_otp(email, otp)

    if not send_reset_otp(email, otp):
        return render_template(
            "verify_otp.html",
            email=email,
            error="Không thể gửi OTP."
        )

    return render_template(
        "verify_otp.html",
        email=email,
        error="OTP mới đã được gửi."
    )

@app.route("/")
def index():

    creds = get_credentials()
    if not creds:
        redirect_uri = request.url_root.rstrip("/") + "/google/callback"
        authorization_url, session["code_verifier"] = get_authorization_url(redirect_uri)
        return redirect(authorization_url)

    if "email" not in session:

        return redirect("/login")
    
    related_emails = load_shared_email()
    job_names = get_all_job_names()

    return render_template(

        "index.html",

        email=session["email"],

        related_emails=related_emails,

        job_names=job_names

    )

@app.route("/google/callback")
def google_callback():

    redirect_uri = request.url_root.rstrip("/") + "/google/callback"

    handle_google_callback(
        authorization_response_url=request.url,
        redirect_uri=redirect_uri,
        session=session
    )

    return redirect("/login")

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

    email = request.form["email"]
    password = request.form["password"]

    add_hr(email, password)

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

    old_email = request.form.get("old_email") or request.form.get("email")
    new_email = request.form.get("new_email") or request.form.get("email")
    password = request.form["password"]

    update_hr(old_email, new_email, password)

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

            timestamp = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y-%m-%d %H:%M:%S")

            extension = os.path.splitext(filename)[1]

            new_filename = f"{position}_{name}_{timestamp}{extension}"

            drive_link = upload_cv(
                save_path,
                new_filename,
                position
            )

            candidate["drive_link"] = drive_link

            candidate["uploader_email"] = session["email"]

            all_related_emails = related_emails.copy()

            if session["email"] not in all_related_emails:
                all_related_emails.append(session["email"])

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