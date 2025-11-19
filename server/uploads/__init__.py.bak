# server/uploads/__init__.py
"""
Uploads package - ensures uploads directory exists and provides simple helpers.
"""

import os
import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR)  # this file is inside server/uploads so BASE_DIR is server/uploads

# If for some reason BASE_DIR is wrong, fallback to parent/server/uploads
if not os.path.exists(UPLOADS_DIR):
    # attempt create
    try:
        os.makedirs(UPLOADS_DIR, exist_ok=True)
    except Exception:
        UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
        os.makedirs(UPLOADS_DIR, exist_ok=True)

def ensure_uploads_dir():
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    return UPLOADS_DIR

def make_upload_filename(orig_name: str):
    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe = orig_name.replace(" ", "_")
    return f"{ts}_{safe}"

def cleanup_older_than(days: int = 30):
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    removed = []
    for fn in os.listdir(UPLOADS_DIR):
        path = os.path.join(UPLOADS_DIR, fn)
        try:
            mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(path))
            if mtime < cutoff:
                os.remove(path)
                removed.append(fn)
        except Exception:
            pass
    return removed

# ensure folder exists on import
ensure_uploads_dir()
