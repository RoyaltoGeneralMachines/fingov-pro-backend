# admin_router.py
from fastapi import APIRouter, Depends, Request, HTTPException
from db import get_conn
import json
import datetime

router = APIRouter()

def log_admin_action(actor_username: str, action: str, target: str = '', details: str = '', ip: str = None):
    try:
        conn = get_conn(); cur = conn.cursor()
        now = datetime.datetime.utcnow().isoformat()
        cur.execute("INSERT INTO admin_audit(actor_username, action, target, details, ip_address, created_at) VALUES (?,?,?,?,?,?)",
                    (actor_username, action, target, details or '', ip or 'unknown', now))
        conn.commit(); conn.close()
    except Exception as e:
        print("audit log failed:", e)

@router.get("/admin/users")
def list_users(current_user: Dict = Depends(lambda: None)):
    # current_user enforced at mount
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id,username,full_name,role,partner_code,email,created_at,last_login FROM users ORDER BY id")
    rows = cur.fetchall(); conn.close()
    return [dict(r) for r in rows]

@router.post("/admin/create_user")
def create_user(payload: Dict = None, request: Request=None, current_user: Dict = Depends(lambda: None)):
    data = payload or {}
    username = data.get('username'); password = data.get('password'); role = data.get('role','AGENT')
    if not username or not password:
        raise HTTPException(400, "username & password required")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO users(username,password_hash,full_name,role,created_at) VALUES(?,?,?,?,?)",
                (username, payload.get('password_hash') or payload.get('password'), username, role, datetime.datetime.utcnow().isoformat()))
    conn.commit(); conn.close()
    try:
        log_admin_action(current_user['username'], 'create_user', username, details=json.dumps({'role': role}), ip=(request.client.host if request else None))
    except:
        pass
    return {"status":"ok"}
