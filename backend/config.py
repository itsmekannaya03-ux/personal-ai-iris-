from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/igris"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/igris"
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

    class Config:
        env_file = "backend/.env"


settings = Settings()
