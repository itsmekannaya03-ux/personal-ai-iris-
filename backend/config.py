import os
from urllib.parse import quote_plus, unquote, urlparse, parse_qs, urlencode, urlunparse
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


def sanitize_async_db_url(url: str) -> str:
    """Ensure asyncpg URL has postgresql+asyncpg scheme, safe password encoding,

    and unsupported libpq query parameters (sslmode, channel_binding) stripped.
    """
    if not url:
        return url

    # Strip quotes and whitespace that may come from .env
    url = url.strip().strip("'\"")

    prefix, sep, rest = url.partition("://")
    if not rest:
        return url

    # Enforce postgresql+asyncpg driver
    if prefix in ("postgresql", "postgres", "postgresql+asyncpg"):
        clean_prefix = "postgresql+asyncpg"
    else:
        clean_prefix = prefix

    # Safely URL-encode special characters in password
    if "@" in rest:
        userinfo, _, host_db = rest.rpartition("@")
        if ":" in userinfo:
            user, _, raw_pwd = userinfo.partition(":")
            safe_pwd = quote_plus(unquote(raw_pwd))
            userinfo = f"{user}:{safe_pwd}"
        rest = f"{userinfo}@{host_db}"

    rebuilt = f"{clean_prefix}://{rest}"
    parsed = urlparse(rebuilt)

    # Strip libpq-only parameters that asyncpg.connect() rejects as invalid keyword arguments
    # (e.g. sslmode, channel_binding, target_session_attrs)
    query_params = parse_qs(parsed.query)
    clean_params = {}
    for k, v in query_params.items():
        if k.lower() in ("sslmode", "channel_binding", "target_session_attrs"):
            continue
        clean_params[k] = v[0]

    parts = list(parsed)
    parts[4] = urlencode(clean_params)
    return urlunparse(parts)


def sanitize_sync_db_url(url: str) -> str:
    """Ensure synchronous database URL has standard postgresql:// scheme."""
    if not url:
        return url

    url = url.strip().strip("'\"")
    prefix, sep, rest = url.partition("://")
    if not rest:
        return url

    if prefix in ("postgresql+asyncpg", "postgres"):
        clean_prefix = "postgresql"
    else:
        clean_prefix = prefix

    if "@" in rest:
        userinfo, _, host_db = rest.rpartition("@")
        if ":" in userinfo:
            user, _, raw_pwd = userinfo.partition(":")
            safe_pwd = quote_plus(unquote(raw_pwd))
            userinfo = f"{user}:{safe_pwd}"
        rest = f"{userinfo}@{host_db}"

    return f"{clean_prefix}://{rest}"


def sanitize_cors_origins(origins_input: str) -> str:
    """Trim whitespace, quotes, and trailing slashes from comma-separated CORS origins,

    and ensure the production frontend origin and local dev origins are always included.
    """
    cleaned_list: list[str] = [
        "https://personal-ai-iris.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    if origins_input:
        for item in str(origins_input).split(","):
            cleaned = item.strip().strip("'\"").rstrip("/")
            if cleaned and cleaned not in cleaned_list:
                cleaned_list.append(cleaned)

    return ",".join(cleaned_list)


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
    CORS_ORIGINS: str = "https://personal-ai-iris.vercel.app,http://localhost:3000,http://127.0.0.1:3000"
    BASE_URL: str = "http://localhost:8001"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_async_db_url(cls, v: str) -> str:
        return sanitize_async_db_url(v)

    @field_validator("DATABASE_URL_SYNC", mode="before")
    @classmethod
    def validate_sync_db_url(cls, v: str) -> str:
        return sanitize_sync_db_url(v)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        return sanitize_cors_origins(v)

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip().strip("'\"").rstrip("/")
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
