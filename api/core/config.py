from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/igris"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/igris"
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    CORS_ORIGINS: str = "http://localhost:3000"
    BASE_URL: str = "http://localhost:8000"

    class Config:
        env_file = "api/.env"


settings = Settings()
