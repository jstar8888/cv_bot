from database import supabase
from datetime import datetime, timedelta

def authenticate_user(email, password):

    admin = (
        supabase.table("admin")
        .select("*")
        .eq("email", email)
        .eq("password", password)
        .execute()
    )

    if admin.data:

        user = admin.data[0]
        user["role"] = "admin"

        return user

    hr = (
        supabase.table("hr")
        .select("*")
        .eq("email", email)
        .eq("password", password)
        .execute()
    )

    if hr.data:

        user = hr.data[0]
        user["role"] = "hr"

        return user

    return None

def get_admin_by_email(email):
    response = (
        supabase.table("admin")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None

def update_admin_password(email, new_password):
    response = (
        supabase.table("admin")
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

def add_hr(email, password, name):

    (
        supabase.table("hr")
        .insert({
            "email": email,
            "password": password,
            "name": name
        })
        .execute()
    )


def load_hr():

    response = (
        supabase.table("hr")
        .select("*")
        .execute()
    )

    return response.data

def delete_hr(email):

    (
        supabase.table("hr")
        .delete()
        .eq("email", email)
        .execute()
    )

def update_hr(email, password, name):

    (
        supabase.table("hr")
        .update({
            "password": password,
            "name": name
        })
        .eq("email", email)
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