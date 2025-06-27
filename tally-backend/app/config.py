"""Configuration management using pydantic settings."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    # Database - using asyncpg driver
    DATABASE_URL: str = "postgresql+asyncpg://postgres:f2Kzb3IK4%5EB6FJ%25T@db.tofyxmdctxlagncvqhpg.supabase.co:5432/postgres"

    # API Keys
    REDUCTO_API_KEY: str
    OPENAI_API_KEY: str
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Storage
    DEFAULT_BUCKET_NAME: str = "tally-documents"
    UPLOAD_MAX_SIZE: int = 52428800  # 50MB
    PRESIGNED_URL_EXPIRY: int = 3600  # 1 hour

    # CORS
    ALLOWED_HOSTS: list[str] = ["*"]

    # File Upload Settings
    MAX_FILE_SIZE: int = 52428800  # 50MB
    ALLOWED_FILE_TYPES: list[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "text/csv",
        "application/json",
        "text/plain",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Get application settings."""
    return Settings()

# Export settings instance
settings = get_settings()

# Export commonly used settings as top-level variables
DATABASE_URL = settings.DATABASE_URL
REDUCTO_API_KEY = settings.REDUCTO_API_KEY
ALLOWED_HOSTS = settings.ALLOWED_HOSTS
