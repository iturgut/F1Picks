"""
Configuration for FastF1 Worker Service
"""
import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Worker service configuration."""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/f1picks"
    
    # FastF1 Configuration
    FASTF1_CACHE_DIR: Path = Path("./cache/fastf1")
    FASTF1_REQUEST_TIMEOUT: int = 30
    FASTF1_MAX_RETRIES: int = 3
    
    # Polling Configuration
    POLL_INTERVAL_MINUTES: int = 30  # Check for new data every 30 minutes
    POST_SESSION_DELAY_MINUTES: int = 30  # Wait 30 min after session ends
    MAX_POLL_ATTEMPTS: int = 10  # Maximum polling attempts per session
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # or "console"
    
    # Worker Configuration
    WORKER_NAME: str = "fastf1-worker"
    ENABLE_SCHEDULER: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Global settings instance
settings = Settings()

# Ensure cache directory exists
settings.FASTF1_CACHE_DIR.mkdir(parents=True, exist_ok=True)
