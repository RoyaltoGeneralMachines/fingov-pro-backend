# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .db import init_db
from .auth_router import router as auth_router
from .otp_router import router as otp_router
from .template_router import router as template_router
from .partners_router import router as partners_router
from .sync_router import router as sync_router
from .wa_router import router as wa_router
from .version_admin_router import router as version_admin_router   # ⭐ NEW

app = FastAPI(title="FINGOV PRO CLOUD SERVER", version="2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- INIT DB ----
init_db()

# ---- AUTH HELPERS ----
from .utils import verify_jwt_token

def get_current_user(token: str = Depends(verify_jwt_token)):
    if not token:
        raise HTTPException(401, "Invalid or missing token")
    return token

def require_role(role: str):
    def checker(user = Depends(get_current_user)):
        if user.get("role") != role:
            raise HTTPException(403, "Unauthorized")
        return user
    return checker

# ---- ROUTERS ----
app.include_router(auth_router, prefix="/auth")
app.include_router(otp_router, prefix="/auth")
app.include_router(template_router, prefix="/admin")
app.include_router(partners_router, prefix="/partners")
app.include_router(sync_router, prefix="/sync")
app.include_router(wa_router, prefix="")

# ⭐ NEW VERSION ADMIN ROUTER
app.include_router(version_admin_router, prefix="/version-admin")

@app.get("/")
def root():
    return {"status": "ok", "server": "FINGOV PRO CLOUD 2.0"}


