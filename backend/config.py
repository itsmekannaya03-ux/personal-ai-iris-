from urllib.parse import quote_plus, unquote
from pydantic_settings import BaseSettings
from pydantic import field_validator


def sanitize_db_url(url: str) -> str:
    """Ensure password special characters (like '@') are URL-encoded in database URLs."""
    if not url:
        return url
    prefix, sep, rest = url.partition("://")
    if not rest or "@" not in rest:
        return url

    # The last '@' separates userinfo from host:port/db
    userinfo, _, host_db = rest.rpartition("@")
    if ":" in userinfo:
        user, _, raw_pwd = userinfo.partition(":")
        safe_pwd = quote_plus(unquote(raw_pwd))
        return f"{prefix}://{user}:{safe_pwd}@{host_db}"
    return url


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/iris_db"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@127.0.0.1:5432/iris_db"
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 15 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days
    REFRESH_SECRET_KEY: str = "change-this-refresh-secret"
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    CORS_ORIGINS: str = "http://localhost:3000"
    BASE_URL: str = "http://localhost:8001"

    @field_validator("DATABASE_URL", "DATABASE_URL_SYNC", mode="before")
    @classmethod
    def sanitize_database_urls(cls, v: str) -> str:
        return sanitize_db_url(v)

    class Config:
        env_file = "backend/.env"


settings = Settings()
