# server/version_admin_router.py
"""
Admin API to update Fingov Pro Desktop version_info.json
No server redeploy needed.
"""

from fastapi import APIRouter, HTTPException
import json
import os

router = APIRouter(prefix="/admin", tags=["Admin"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(BASE_DIR, "version_info.json")

# Simple admin password protection (change it!)
ADMIN_PASSWORD = "Faqueeha25@#"


@router.post("/update_version")
def update_version(payload: dict, password: str):
    """
    payload must include:
    - latest_version
    - download_url
    - mandatory
    - release_notes
    - sha256
    """

    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")

    required_fields = [
        "latest_version",
        "download_url",
        "mandatory",
        "release_notes",
        "sha256"
    ]

    for f in required_fields:
        if f not in payload:
            raise HTTPException(status_code=400, detail=f"Missing field: {f}")

    with open(VERSION_FILE, "w") as f:
        json.dump(payload, f, indent=4)

    return {"status": "ok", "message": "Version info updated successfully"}
