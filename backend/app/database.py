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
    DATABASE_URL = "postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres"

# Use psycopg (async) driver instead of asyncpg for better pgbouncer compatibility
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)

# Create async engine with pgbouncer compatibility
# psycopg handles pgbouncer better than asyncpg
connect_args = {}
if "pooler.supabase.com" in DATABASE_URL:
    # Disable prepared statements for pgbouncer compatibility
    connect_args = {
        "prepare_threshold": None,  # Disable prepared statements
    }

engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Use NullPool for serverless environments
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",  # Enable SQL logging in dev
    future=True,
    connect_args=connect_args,
    pool_pre_ping=True,  # Verify connections before using them
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
