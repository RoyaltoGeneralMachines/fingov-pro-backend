# utils.py
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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# configuration from env
SECRET = os.environ.get("FINGOV_SECRET", "replace_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

WHATSAPP_API_URL = os.environ.get("WHATSAPP_API_URL")
WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN")

EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT")) if os.environ.get("EMAIL_PORT") else None
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_FROM = os.environ.get("EMAIL_FROM", EMAIL_USER or "noreply@easyadvisor.in")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False

def create_refresh_token():
    return str(uuid.uuid4())

def generate_otp(length=6):
    return ''.join(str(random.randint(0,9)) for _ in range(length))

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

def send_email(to_email: str, subject: str, body: str) -> bool:
    if not (EMAIL_HOST and EMAIL_USER and EMAIL_PASSWORD and EMAIL_PORT):
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
