# otp_router.py
import datetime
from fastapi import APIRouter, HTTPException, Request
from models import OTPSendRequest, OTPVerifyRequest
from db import get_conn
from utils import generate_otp, hash_password, send_whatsapp_message, send_email, hash_password as hp, verify_password
from passlib.context import CryptContext

pwdctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()

# in-memory counters
from collections import defaultdict
_phone_counters = defaultdict(lambda: {'hour': [], 'day': []})

OTP_EXPIRE_MINUTES = int(__import__("os").environ.get("OTP_EXPIRE_MINUTES", "10"))
OTP_MAX_PER_HOUR = int(__import__("os").environ.get("OTP_MAX_PER_HOUR", "3"))
OTP_MAX_PER_DAY = int(__import__("os").environ.get("OTP_MAX_PER_DAY", "6"))

def _now():
    return datetime.datetime.utcnow().isoformat()

def _cleanup(phone):
    now = datetime.datetime.utcnow()
    hour_cut = now - datetime.timedelta(hours=1)
    day_cut = now - datetime.timedelta(days=1)
    cnt = _phone_counters.get(phone)
    if not cnt: return
    cnt['hour'] = [t for t in cnt['hour'] if datetime.datetime.fromisoformat(t) > hour_cut]
    cnt['day'] = [t for t in cnt['day'] if datetime.datetime.fromisoformat(t) > day_cut]

def _record(phone):
    t = _now()
    _phone_counters[phone]['hour'].append(t)
    _phone_counters[phone]['day'].append(t)

@router.post("/auth/send_otp")
def send_otp(payload: OTPSendRequest, request: Request=None):
    username = payload.username; phone = payload.phone
    if not username or not phone:
        raise HTTPException(400, "username & phone required")
    _cleanup(phone)
    cnt = _phone_counters[phone]
    if len(cnt['hour']) >= OTP_MAX_PER_HOUR or len(cnt['day']) >= OTP_MAX_PER_DAY:
        raise HTTPException(429, "OTP rate limit exceeded")
    raw = generate_otp(6)
    hashed = pwdctx.hash(raw)
    now = _now()
    expires = (datetime.datetime.utcnow() + datetime.timedelta(minutes=OTP_EXPIRE_MINUTES)).isoformat()
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO password_otps(username, phone, otp_hash, device_id, tries, created_at, expires_at) VALUES(?,?,?,?,?,?,?)",
                (username, phone, hashed, payload.device_id or '', 0, now, expires))
    conn.commit(); conn.close()
    _record(phone)
    # render simple message
    tpl = f"Dear {username} ji,\n\nYour OTP is: {raw}\n\nValid for {OTP_EXPIRE_MINUTES} minutes.\n— EasyAdvisor™"
    sent = send_whatsapp_message(phone, tpl)
    if sent:
        return {"status":"ok", "message":"OTP sent via WhatsApp if reachable."}
    # email fallback
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT email FROM users WHERE username = ?", (username,))
    row = cur.fetchone(); conn.close()
    if row and row['email']:
        send_email(row['email'], "FINGOV OTP", tpl)
        return {"status":"ok", "message":"OTP sent via email fallback."}
    raise HTTPException(500, "Failed to deliver OTP")

@router.post("/auth/verify_otp")
def verify_otp(payload: OTPVerifyRequest, request: Request=None):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM password_otps WHERE username = ? AND phone = ? ORDER BY id DESC LIMIT 1", (payload.username, payload.phone))
    row = cur.fetchone()
    if not row:
        raise HTTPException(400, "Invalid OTP or expired")
    if row['expires_at'] < _now():
        raise HTTPException(400, "OTP expired")
    if not pwdctx.verify(payload.otp, row['otp_hash']):
        cur.execute("UPDATE password_otps SET tries = tries + 1, last_attempt_ts = ? WHERE id = ?", (_now(), row['id']))
        conn.commit(); conn.close()
        raise HTTPException(400, "Invalid OTP")
    # set new password
    ph = hp(payload.new_password)
    cur.execute("UPDATE users SET password_hash = ? WHERE username = ?", (ph, payload.username))
    cur.execute("DELETE FROM password_otps WHERE username = ? AND phone = ?", (payload.username, payload.phone))
    conn.commit(); conn.close()
    return {"status":"ok", "message":"Password reset successful"}

