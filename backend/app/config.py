"""
Application configuration using Pydantic Settings.
"""

from typing import Literal, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres",
        env="DATABASE_URL",
        description="Database connection URL"
    )
    echo: bool = Field(
        default=False,
        env="DATABASE_ECHO",
        description="Enable SQL query logging"
    )
    pool_size: int = Field(
        default=5,
        env="DATABASE_POOL_SIZE",
        description="Database connection pool size"
    )
    max_overflow: int = Field(
        default=10,
        env="DATABASE_MAX_OVERFLOW",
        description="Maximum overflow connections"
    )
    pool_timeout: int = Field(
        default=30,
        env="DATABASE_POOL_TIMEOUT",
        description="Connection pool timeout in seconds"
    )
    pool_recycle: int = Field(
        default=3600,
        env="DATABASE_POOL_RECYCLE",
        description="Connection recycle time in seconds"
    )

    @validator("url")
    def validate_database_url(cls, v):
        """Ensure database URL uses asyncpg driver."""
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v

    class Config:
        env_prefix = "DATABASE_"


class AppSettings(BaseSettings):
    """Application configuration settings."""

    name: str = Field(default="F1 Picks API", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")
    description: str = Field(
        default="F1 Picks - Fantasy Formula 1 Prediction Game",
        description="Application description"
    )
    debug: bool = Field(default=False, env="DEBUG", description="Debug mode")
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        env="ENVIRONMENT",
        description="Application environment"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )

    # API Configuration
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    docs_url: Optional[str] = Field(default="/docs", description="API docs URL")
    redoc_url: Optional[str] = Field(default="/redoc", description="ReDoc URL")

    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="CORS_ORIGINS",
        description="Allowed CORS origins"
    )

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class AuthSettings(BaseSettings):
    """Authentication and security settings."""

    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY",
        description="Secret key for JWT tokens"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        env="REFRESH_TOKEN_EXPIRE_DAYS",
        description="Refresh token expiration in days"
    )

    # Supabase Configuration
    supabase_url: Optional[str] = Field(
        default=None,
        env="SUPABASE_URL",
        description="Supabase project URL"
    )
    supabase_anon_key: Optional[str] = Field(
        default=None,
        env="SUPABASE_ANON_KEY",
        description="Supabase anonymous key"
    )
    supabase_service_key: Optional[str] = Field(
        default=None,
        env="SUPABASE_SERVICE_ROLE_KEY",
        description="Supabase service role key"
    )

    class Config:
        env_prefix = "AUTH_"


class ExternalAPISettings(BaseSettings):
    """External API configuration settings."""

    # FastF1 Configuration
    fastf1_cache_enabled: bool = Field(
        default=True,
        env="FASTF1_CACHE_ENABLED",
        description="Enable FastF1 caching"
    )
    fastf1_cache_dir: str = Field(
        default="./cache/fastf1",
        env="FASTF1_CACHE_DIR",
        description="FastF1 cache directory"
    )

    # Rate limiting
    api_rate_limit: int = Field(
        default=100,
        env="API_RATE_LIMIT",
        description="API rate limit per minute"
    )

    class Config:
        env_prefix = "EXTERNAL_"


class Settings(BaseSettings):
    """Main application settings."""

    app: AppSettings = AppSettings()
    database: DatabaseSettings = DatabaseSettings()
    auth: AuthSettings = AuthSettings()
    external: ExternalAPISettings = ExternalAPISettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
