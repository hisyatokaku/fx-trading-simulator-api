"""Application configuration settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql+asyncpg://fxtrade:fxtrade@localhost:5432/fxtrade"
    database_url_sync: str = "postgresql://fxtrade:fxtrade@localhost:5432/fxtrade"

    # Application
    app_env: str = "development"
    debug: bool = True

    # API
    api_prefix: str = "/api"

    # Default trading settings
    default_initial_balance: float = 1000000.0
    default_time_interval_seconds: int = 86400  # 1 day

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
