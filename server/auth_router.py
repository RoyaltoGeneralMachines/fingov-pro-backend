# auth_router.py
import datetime
import jwt
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict
from .models import LoginPayload, RefreshPayload
from .db import get_conn
from .utils import hash_password, verify_password, create_refresh_token, SECRET, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from psycopg2.extras import RealDictCursor

router = APIRouter()
def create_access_token(data: Dict, expires_minutes: int = None):
    now = datetime.datetime.utcnow()
    expire = now + datetime.timedelta(minutes=(expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = data.copy()
    to_encode.update({"iat": now.timestamp(), "exp": expire.timestamp()})
    token = jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)
    return token

@router.post("/register")
def register(payload: LoginPayload, request: Request=None):
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT COUNT(*) as c FROM users"); c = cur.fetchone()['c']
    if C== 0:    
        allow = True    if not allow:
        raise HTTPException(403, "Registration disabled")
    if cur.execute("SELECT id FROM users WHERE username = ?", (payload.username,)).fetchone():
        raise HTTPException(400, "User exists")
    ph = hash_password(payload.password)
    now = datetime.datetime.utcnow().isoformat()
    role = "ADMIN" if c==0 else "AGENT"
    cur.execute("INSERT INTO users(username,password_hash,full_name,role,created_at) VALUES(?,?,?,?,?)",
                (payload.username, ph, payload.username, role, now))
    conn.commit(); conn.close()
    return {"status":"ok", "username": payload.username}

@router.post("/login")
def login(payload: LoginPayload, request: Request=None):
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE username = ?", (payload.username,))
        row = cur.fetchone()if not row or not verify_password(payload.password, row['password_hash']):
        raise HTTPException(401, "Invalid credentials")
    user = dict(row)
    user_data = {"sub": user['username'], "role": user['role'], "user_id": user['id']}
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token()
    issued = datetime.datetime.utcnow().isoformat()
    exp = (datetime.datetime.utcnow() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()
    cur.execute("INSERT INTO refresh_tokens(user_id, token, issued_at, expires_at, device_id) VALUES(?,?,?,?,?)",
                (user['id'], refresh_token, issued, exp, payload.device_id or ''))
    cur.execute("UPDATE users SET last_login = ? WHERE id = ?", (issued, user['id']))
    conn.commit(); conn.close()
    return {"access_token": access_token, "refresh_token": refresh_token, "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES*60}

@router.post("/refresh")
def refresh_token(payload: RefreshPayload):
    token = payload.refresh_token
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM refresh_tokens WHERE token = ? AND revoked = False", (token,))    r = cur.fetchone()
    if not r:
        raise HTTPException(401, "Invalid refresh token")
    if r['expires_at'] < datetime.datetime.utcnow().isoformat():
        raise HTTPException(401, "Refresh token expired")
    cur.execute("SELECT * FROM users WHERE id = ?", (r['user_id'],))
    u = cur.fetchone()
    if not u:
        raise HTTPException(401, "User not found")
    user = dict(u)
    user_data = {"sub": user['username'], "role": user['role'], "user_id": user['id']}
    access_token = create_access_token(user_data)
    conn.close()
    return {"access_token": access_token, "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES*60}

@router.post("/logout")
def logout(payload: RefreshPayload):
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("UPDATE refresh_tokens SET revoked = 1 WHERE token = ?", (token,))
        conn.commit(); conn.close()return {"status":"ok"}







