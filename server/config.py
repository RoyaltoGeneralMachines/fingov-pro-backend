# server/config.py
from pydantic import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "FINGOV PRO Backend"

    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET: str
    JWT_ALGO: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # OTP Provider
    OTP_API_KEY: str = ""
    OTP_SENDER_ID: str = ""

    # WhatsApp Provider
    WA_API_URL: str = ""
    WA_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
