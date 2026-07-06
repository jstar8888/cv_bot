from database import supabase


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