import os
import datetime
import uuid
import json
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from passlib.context import CryptContext
import bcrypt
import secrets
import string

# ============================================================
# Configuration and Constants
# ============================================================

# environment or fallback defaults
SECRET = os.environ.get("FINGOV_SECRET", "your-secret-key")
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

WHATSAPP_API_URL = os.environ.get("WHATSAPP_API_URL")
WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN")

EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT")) if os.environ.get("EMAIL_PORT") else None
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_FROM = os.environ.get("EMAIL_FROM", EMAIL_USER or "noreply@easyadvisor.in")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============================================================
# Security Utilities
# ============================================================

def hash_password(password: str) -> str:
    """
    Secure password hashing using bcrypt.
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its hashed version.
    """
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False

def create_refresh_token(length: int = 64) -> str:
    """
    Generate a random secure refresh token.
    """
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

def generate_otp(length=6) -> str:
    """
    Generate a numeric OTP (default length = 6).
    """
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

# ============================================================
# WhatsApp Messaging
# ============================================================

def send_whatsapp_message(to_number: str, message: str, file_path: str = None) -> bool:
    if not to_number:
        return False
    if WHATSAPP_API_URL:
        try:
            headers = {'Content-Type': 'application/json'}
            if WHATSAPP_API_TOKEN:
                headers['Authorization'] = f'Bearer {WHATSAPP_API_TOKEN}' 
            payload = {'to': to_number, 'message': message}
            if file_path:
                payload['file_path'] = file_path
            r = requests.post(WHATSAPP_API_URL, json=payload, headers=headers, timeout=12)
            r.raise_for_status()
            return True
        except Exception as e:
            print("WA send failed:", e)
            return False
    # fallback: print to logs
    print(f"[WA MOCK] to={to_number} message={message} file={file_path}")
    return True

# ============================================================
# Email Sending
# ============================================================

def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send an email via configured SMTP credentials.
    """
    if not (EMAIL_HOST and EMAIL_USER and EMAIL_PASSWORD and EMAIL_PORT):
        print("Email configuration missing.")
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        s = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
        s.starttls()
        s.login(EMAIL_USER, EMAIL_PASSWORD)
        s.sendmail(EMAIL_FROM, [to_email], msg.as_string())
        s.quit()
        return True
    except Exception as e:
        print("Email send failed:", e)
        return False
