import os
from flask_mail import Message
from extensions import mail


def send_reset_otp(email, otp):
    try:
        msg = Message(
            subject="Password Reset OTP",
            sender=os.getenv("MAIL_USER"),
            recipients=[email]
        )

        msg.body = f"""
Xin chào,

Bạn đã sử dụng dịch vụ OTP

Mã OTP của bạn là:

{otp}

Mã có hiệu lực trong 5 phút.

Nếu không phải bạn yêu cầu, hãy bỏ qua email này.
"""

        mail.send(msg)
        return True

    except Exception as e:
        print(f"Send email error: {e}")
        return False
    

import secrets

def generate_otp(length=6):
    """
    Sinh OTP gồm `length` chữ số.
    Mặc định là 6 số.
    """
    max_value = 10 ** length
    return f"{secrets.randbelow(max_value):0{length}d}"