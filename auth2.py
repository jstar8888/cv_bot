from database import supabase
from datetime import datetime, timedelta

def authenticate_user(email, password):
    response = (
        supabase.table("users")
        .select("*")
        .eq("email", email)
        .eq("password", password)
        .limit(1)
        .execute()
    )

    if response.data:
        user = response.data[0]
        # ensure role exists (default to 'user' if not set)
        user["role"] = user.get("role", "user")
        return user

    return None




def get_user_by_email(email):
    response = (
        supabase.table("users")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


def update_user_password(email, new_password):
    response = (
        supabase.table("users")
        .update({"password": new_password})
        .eq("email", email)
        .execute()
    )

    return len(response.data) > 0



from datetime import datetime, timedelta, UTC

def save_reset_otp(email, otp):
    expire_at = datetime.now(UTC) + timedelta(minutes=5)

    payload = {
        "email": email,
        "otp": otp,
        "expire_at": expire_at.isoformat(),
    }

    response = (
        supabase.table("password_reset_otp")
        .upsert(payload, on_conflict="email")
        .execute()
    )

    return bool(response.data)



def verify_reset_otp(email, otp):
    response = (
        supabase.table("password_reset_otp")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )

    if not response.data:
        return False

    data = response.data[0]

    if data["otp"] != otp:
        return False

    expire = datetime.fromisoformat(
        data["expire_at"].replace("Z", "+00:00")
    )

    if expire < datetime.now(expire.tzinfo):
        return False

    return True

def delete_reset_otp(email):
    response = (
        supabase.table("password_reset_otp")
        .delete()
        .eq("email", email)
        .execute()
    )

    return len(response.data) > 0

def add_hr(email, password):
    # insert into unified `user` table and set role to 'hr'
    (
        supabase.table("users")
        .insert({
            "email": email,
            "password": password,
            "role": "hr"
        })
        .execute()
    )


def load_hr():
    response = (
        supabase.table("users")
        .select("*")
        .eq("role", "hr")
        .execute()
    )

    return response.data

def delete_hr(email):
    (
        supabase.table("users")
        .delete()
        .eq("email", email)
        .eq("role", "hr")
        .execute()
    )

def update_hr(old_email, new_email, password):
    # update email and password for hr in unified `user` table
    (
        supabase.table("users")
        .update({
            "email": new_email,
            "password": password
        })
        .eq("email", old_email)
        .eq("role", "hr")
        .execute()
    )

def add_shared_email(email):

    (
        supabase.table("shared_email")
        .insert({
            "email": email
        })
        .execute()
    )

def load_shared_email():

    response = (
        supabase.table("shared_email")
        .select("*")
        .execute()
    )

    return response.data

def delete_shared_email(email):

    (
        supabase.table("shared_email")
        .delete()
        .eq("email", email)
        .execute()
    )

def update_shared_email(old_email, new_email):

    (
        supabase.table("shared_email")
        .update({
            "email": new_email
        })
        .eq("email", old_email)
        .execute()
    )





def save_cv_log(
    uploader_email,
    candidate_name,
    job_position,
    status
):

    data = {

        "uploader_email": uploader_email,

        "candidate_name": candidate_name,

        "job_position": job_position,

        "status": status

    }


    supabase.table(
        "cv_upload_logs"
    ).insert(
        data
    ).execute()


from datetime import datetime, time
from zoneinfo import ZoneInfo


def get_today_logs(email):

    timezone = ZoneInfo(
        "Asia/Ho_Chi_Minh"
    )

    utc = ZoneInfo(
        "UTC"
    )


    today = datetime.now(timezone).date()


    # 00:00:00 giờ Việt Nam
    start_time = datetime.combine(
        today,
        time.min,
        tzinfo=timezone
    )


    # 23:59:59 giờ Việt Nam
    end_time = datetime.combine(
        today,
        time.max,
        tzinfo=timezone
    )


    # đổi sang UTC trước khi query Supabase

    start_utc = start_time.astimezone(utc)

    end_utc = end_time.astimezone(utc)


    result = supabase.table(
        "cv_upload_logs"
    )\
    .select("*")\
    .eq(
        "uploader_email",
        email
    )\
    .gte(
        "created_at",
        start_utc.isoformat()
    )\
    .lte(
        "created_at",
        end_utc.isoformat()
    )\
    .order(
        "created_at",
        desc=True
    )\
    .execute()


    return result.data
