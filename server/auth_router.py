import datetime
import jwt
from fastapi import APIRouter, HTTPException, Request
from typing import Dict
from psycopg2.extras import RealDictCursor
from psycopg2 import DatabaseError

from .models import LoginPayload, RefreshPayload
from .db import get_conn
from .utils import (
    hash_password,
    verify_password,
    create_refresh_token,
    SECRET,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

router = APIRouter()


# ---------------- JWT CREATION ----------------
def create_access_token(data: Dict, expires_minutes: int = None) -> str:
    """
    Create a signed JWT access token.
    """
    now = datetime.datetime.utcnow()
    expire = now + datetime.timedelta(
        minutes=(expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = data.copy()
    payload.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    })
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


# ---------------- REGISTER ----------------
@router.post("/register")
def register(payload: LoginPayload, request: Request = None):
    """
    Create first user if table is empty; otherwise registration disabled.
    """
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("SELECT COUNT(*) AS c FROM users")
        c = cur.fetchone()["c"]
        allow = (c == 0)
        if not allow:
            raise HTTPException(status_code=403, detail="Registration disabled")

        cur.execute("SELECT id FROM users WHERE username = %s", (payload.username,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")

        password_hash = hash_password(payload.password)
        cur.execute(
            """
            INSERT INTO users (username, password_hash, full_name, role, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                payload.username,
                password_hash,
                payload.username,
                "user",
                datetime.datetime.utcnow(),
            ),
        )
        conn.commit()
        return {"status": "ok", "username": payload.username}

    except DatabaseError as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        cur.close()
        conn.close()


# ---------------- LOGIN ----------------
@router.post("/login")
def login(payload: LoginPayload, request: Request = None):
    """
    Authenticate user and issue tokens.
    """
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("SELECT * FROM users WHERE username = %s", (payload.username,))
        user = cur.fetchone()

        if not user or not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create tokens
        user_data = {
            "sub": user["username"],
            "role": user["role"],
            "user_id": user["id"],
        }
        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token()

        issued_at = datetime.datetime.utcnow()
        expires_at = issued_at + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        # Insert refresh token
        cur.execute(
            """
            INSERT INTO refresh_tokens (user_id, token, issued_at, expires_at, device_id)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                user["id"],
                refresh_token,
                issued_at,
                expires_at,
                getattr(payload, "device_id", "") or "",
            ),
        )

        # Update user last login
        cur.execute(
            "UPDATE users SET last_login = %s WHERE id = %s",
            (issued_at, user["id"]),
        )

        conn.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    except DatabaseError as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        cur.close()
        conn.close()


# ---------------- REFRESH ----------------
@router.post("/refresh")
def refresh_token(payload: RefreshPayload):
    """
    Validate refresh token and issue new access token.
    """
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            "SELECT * FROM refresh_tokens WHERE token = %s AND revoked = FALSE",
            (payload.refresh_token,),
        )
        token_row = cur.fetchone()
        if not token_row:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Compare expiry correctly as datetime
        if token_row["expires_at"] < datetime.datetime.utcnow():
            raise HTTPException(status_code=401, detail="Refresh token expired")

        cur.execute("SELECT * FROM users WHERE id = %s", (token_row["user_id"],))
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        user_data = {
            "sub": user["username"],
            "role": user["role"],
            "user_id": user["id"],
        }
        new_access_token = create_access_token(user_data)

        return {
            "access_token": new_access_token,
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        cur.close()
        conn.close()


# ---------------- LOGOUT ----------------
@router.post("/logout")
def logout(payload: RefreshPayload):
    """
    Revoke a refresh token.
    """
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            "UPDATE refresh_tokens SET revoked = TRUE WHERE token = %s",
            (payload.refresh_token,),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Token not found")
        conn.commit()
        return {"status": "ok"}

    except DatabaseError as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        cur.close()
        conn.close()
