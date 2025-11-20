# server/dependencies.py

def require_role(role: str):
    def checker(user=Depends(get_current_user)):
        if user.get("role") != role:
            raise HTTPException(403, "Unauthorized")
        return user
    return checker

from fastapi import Header, HTTPException, Depends
from jose import jwt, JWTError
from .config import settings


def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGO])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


