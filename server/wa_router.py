# wa_router.py
"""
WhatsApp gateway endpoints for FINGOV PRO server.
- /upload_file    : multipart form file upload (returns server file path/id)
- /send_whatsapp  : send message (with optional server file path). Logs each send in wa_logs.
Requires Authorization header (Bearer) for protected operations.
"""

import os
import datetime
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from db import get_conn
from utils import send_whatsapp_message
from dependencies import get_current_user, require_role  # import dependency helpersfrom typing import Optional

router = APIRouter()
BASE_UPLOAD_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "uploads")
os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)

# helper to persist wa log
def insert_wa_log(row: dict):
    try:
        conn = get_conn(); cur = conn.cursor()
        cur.execute("""
            INSERT INTO wa_logs (to_number, message, file_path, template_key, sent_by, sent_by_role, device_id, created_at, result)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            row.get("to_number"),
            row.get("message"),
            row.get("file_path"),
            row.get("template_key"),
            row.get("sent_by"),
            row.get("sent_by_role"),
            row.get("device_id"),
            row.get("created_at"),
            row.get("result")
        ))
        conn.commit(); conn.close()
    except Exception as e:
        print("wa log insert failed:", e)

@router.post("/upload_file")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """
    Upload a file from desktop to server.
    Response: {"ok": True, "file_id": "<server filename>", "file_path": "<abs path to file>"}
    """
    # basic file size check (optional)
    contents = await file.read()
    max_mb = int(os.environ.get("UPLOAD_MAX_MB","15"))
    if len(contents) > max_mb * 1024 * 1024:
        raise HTTPException(413, f"File too large. Max {max_mb} MB allowed.")
    # safe filename
    ext = os.path.splitext(file.filename)[1] or ""
    server_name = f"{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    save_path = os.path.join(BASE_UPLOAD_DIR, server_name)
    try:
        with open(save_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(500, f"Failed to save file: {e}")
    return {"ok": True, "file_id": server_name, "file_path": save_path}

@router.post("/send_whatsapp")
def send_whatsapp(
    to: str = Form(...),
    message: str = Form(...),
    file_id: Optional[str] = Form(None),
    template_key: Optional[str] = Form(None),
    device_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Send WhatsApp via server WA gateway.
    Accepts form fields so desktop can post file-id + message in same request set.
    Logs each attempt into wa_logs.
    """
    if not to or not message:
        raise HTTPException(400, "to and message are required")

    # role-based: allow AGENT, MANAGER, ADMIN to send; additional checks possible
    role = current_user.get("role", "AGENT")
    if role not in ("ADMIN","MANAGER","AGENT"):
        raise HTTPException(403, "Forbidden")

    # find server file path if file_id provided
    file_path = None
    if file_id:
        candidate = os.path.join(BASE_UPLOAD_DIR, file_id)
        if os.path.exists(candidate):
            file_path = candidate
        else:
            # client might pass an absolute path (legacy); accept if exists under uploads
            if os.path.exists(file_id):
                file_path = file_id
            else:
                raise HTTPException(404, "file not found on server")

    # call underlying gateway (utils.send_whatsapp_message handles gateway or mock)
    sent_ok = False
    try:
        sent_ok = send_whatsapp_message(to, message, file_path)
    except Exception as e:
        sent_ok = False
        print("send_whatsapp exception:", e)

    # log the attempt
    row = {
        "to_number": to,
        "message": message[:4000],  # limit
        "file_path": file_path,
        "template_key": template_key or "",
        "sent_by": current_user.get("username"),
        "sent_by_role": role,
        "device_id": device_id or "",
        "created_at": datetime.datetime.utcnow().isoformat(),
        "result": "ok" if sent_ok else "failed"
    }
    insert_wa_log(row)

    if not sent_ok:
        raise HTTPException(500, "Failed to deliver message via gateway")
    return {"status":"ok", "message":"sent", "file_path": file_path}


