import os
import secrets

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or secrets.token_urlsafe(32)
    JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY") or secrets.token_urlsafe(32)
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///blood_supply_dev.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    JWT_ACCESS_EXPIRES_SECONDS = int(os.getenv("JWT_ACCESS_EXPIRES_SECONDS", "900"))
    JWT_REFRESH_EXPIRES_SECONDS = int(os.getenv("JWT_REFRESH_EXPIRES_SECONDS", "604800"))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    RATE_LIMIT_LOGIN = int(os.getenv("RATE_LIMIT_LOGIN", "5"))
    RATE_LIMIT_REGISTER = int(os.getenv("RATE_LIMIT_REGISTER", "3"))
    RATE_LIMIT_REFRESH = int(os.getenv("RATE_LIMIT_REFRESH", "10"))
