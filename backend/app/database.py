import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Default to local Supabase instance
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres"

# Ensure we're using asyncpg driver
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# Create async engine with pgbouncer compatibility
# Supabase uses pgbouncer which requires special configuration for asyncpg
# We must disable prepared statements completely
engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Use NullPool for serverless/pgbouncer environments
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",  # Enable SQL logging in dev
    future=True,
    connect_args={
        "statement_cache_size": 0,  # CRITICAL: Disable prepared statements for pgbouncer
        "prepared_statement_cache_size": 0,  # Also disable this cache
        "server_settings": {
            "jit": "off",  # Disable JIT compilation for pgbouncer compatibility
        }
    },
    # Also disable SQLAlchemy's query cache
    query_cache_size=0,
    # Disable connection pool pre-ping (not compatible with NullPool anyway)
    pool_pre_ping=False,
)

# Create session factory with execution options for pgbouncer
AsyncSessionLocal = async_sessionmaker(
    engine.execution_options(compiled_cache=None),
    class_=AsyncSession,
    expire_on_commit=False,
)

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.
    
    Usage:
        async with get_db_session() as session:
            # Use session here
            pass
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database session.
    
    Usage in FastAPI routes:
        @app.get("/")
        async def route(db: AsyncSession = Depends(get_db)):
            # Use db here
            pass
    """
    async with get_db_session() as session:
        yield session
