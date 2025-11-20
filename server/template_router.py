# template_router.py
from fastapi import APIRouter, HTTPException, Depends, Request
from .models import TemplateGenericPayload
from .db import get_conn
from .utils import *
import json
import datetime
from typing import Dict

router = APIRouter()

# helper wrappers for app_settings table
def get_app_setting_value(key: str):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    if not row: return None
    try:
        return json.loads(row['value'])
    except Exception:
        return row['value']

def set_app_setting_value(key: str, value: str):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO app_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
    conn.commit(); conn.close()

def bump_version(prev_ver: str) -> str:
    try:
        major, minor = prev_ver.split('.')
        minor = int(minor) + 1
        return f"{major}.{minor}"
    except Exception:
        return prev_ver + ".1"

# existing otp template endpoints (simple)
@router.get("/admin/get_template")
def get_otp_template(lang: str = 'en'):
    key = f"otp_template_whatsapp_{lang}"
    v = get_app_setting_value(key)
    if not v:
        default = DEFAULT_OTP_TEMPLATE_EN if lang.startswith('en') else DEFAULT_OTP_TEMPLATE_HI
        return {"lang": lang, "template": default}
    return {"lang": lang, "template": v}

@router.post("/admin/set_template")
def set_otp_template(payload: Dict[str,str], request: Request=None, current_user: Dict = Depends(lambda: None)):
    # This route is protected at the router mount point in main (so current_user should be provided).
    if not payload.get("lang") or not payload.get("template"):
        raise HTTPException(400, "lang & template required")
    key = f"otp_template_whatsapp_{payload['lang']}"
    set_app_setting_value(key, payload['template'])
    return {"status":"ok"}

# Generic versioned templates
@router.get("/admin/get_template_generic")
def get_template_generic(key: str, current_user: Dict = Depends(lambda: None)):
    storage_key = f"template_generic_{key}"
    v = get_app_setting_value(storage_key)
    if not v:
        return {"key": key, "template": "", "version": "0.0", "found": False}
    return {"key": key, "template": v.get("template", ""), "version": v.get("version", "1.0"), "updated_at": v.get("updated_at"), "updated_by": v.get("updated_by"), "found": True}

@router.post("/admin/set_template_generic")
def set_template_generic(payload: TemplateGenericPayload, request: Request=None, current_user: Dict = Depends(lambda: None)):
    # current_user must be ADMIN - enforcement done in main mount (Depends)
    key = payload.key.strip()
    tpl = payload.template
    if not key:
        raise HTTPException(400, "key required")
    storage_key = f"template_generic_{key}"
    prev = get_app_setting_value(storage_key)
    if isinstance(prev, dict):
        prev_ver = prev.get("version", "1.0")
        new_ver = bump_version(prev_ver)
    else:
        new_ver = "1.0"
    now = datetime.datetime.utcnow().isoformat()
    value = {"template": tpl, "version": new_ver, "updated_at": now, "updated_by": current_user.get("username") if current_user else "admin"}
    set_app_setting_value(storage_key, json.dumps(value))
    return {"status":"ok", "key": key, "version": new_ver, "updated_at": now}

