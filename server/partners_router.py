# partners_router.py
from fastapi import APIRouter, Depends
from db import get_conn
import datetime

router = APIRouter()

@router.get("/partners")
def list_partners(current_user: dict = Depends(lambda: None)):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM d2na_partners ORDER BY partner_code")
    rows = cur.fetchall(); conn.close()
    return [dict(r) for r in rows]

@router.post("/partners/upsert")
def upsert_partner(payload: dict, current_user: dict = Depends(lambda: None)):
    code = payload.get('partner_code')
    name = payload.get('partner_name')
    login = payload.get('login_id')
    mobile = payload.get('mobile')
    now = datetime.datetime.utcnow().isoformat()
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO d2na_partners(partner_code, partner_name, login_id, mobile, last_update) VALUES(?,?,?,?,?) ON CONFLICT(partner_code) DO UPDATE SET partner_name=excluded.partner_name, login_id=excluded.login_id, mobile=excluded.mobile, last_update=excluded.last_update",
                (code, name, login, mobile, now))
    conn.commit(); conn.close()
    return {"status":"ok"}

