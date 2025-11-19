# server/models.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List


# -------------------------
# AUTH MODELS
# -------------------------

class LoginPayload(BaseModel):
    username: str
    password: str


class RefreshPayload(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


# -------------------------
# OTP MODELS
# -------------------------

class OTPSendRequest(BaseModel):
    mobile: str


class OTPVerifyRequest(BaseModel):
    mobile: str
    otp: str


class OTPStatusResponse(BaseModel):
    success: bool
    message: str


# -------------------------
# PARTNERS MODELS
# -------------------------

class PartnerCreate(BaseModel):
    name: str
    mobile: str
    email: Optional[EmailStr]
    address: Optional[str]


class PartnerResponse(BaseModel):
    id: int
    name: str
    mobile: str
    email: Optional[EmailStr]
    address: Optional[str]


# -------------------------
# TEMPLATE MODELS
# -------------------------

class TemplatePayload(BaseModel):
    template_name: str
    variables: Optional[dict]

class TemplateGenericPayload(BaseModel):
        data: Optional[dict]


# -------------------------
# SYNC MODELS
# -------------------------

class SyncClientPayload(BaseModel):
    client_id: str
    version: Optional[str]
    data: Optional[dict]

class SyncPushPayload(BaseModel):
        data: Optional[dict]

class SyncPullPayload(BaseModel):
        data: Optional[dict]


class SyncResponse(BaseModel):
    status: str
    message: str
    payload: Optional[dict]


# -------------------------
# WHATSAPP MODELS
# -------------------------

class WhatsAppMessagePayload(BaseModel):
    mobile: str
    message: str


class WhatsAppTemplatePayload(BaseModel):
    template_id: str
    parameters: List[str]


