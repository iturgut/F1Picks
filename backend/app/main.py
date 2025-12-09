import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .routers import events, leagues, picks, results, scores, users

app = FastAPI(
    title="F1 Picks API",
    description="API for F1 prediction game",
    version="1.0.0"
)

# Configure CORS
allowed_origins = [
    "http://localhost:3000",  # Local development
    "https://f1-picks-frontend.vercel.app",  # Production frontend
    "https://f1picks.vercel.app",  # Production frontend (alternate)
]

# Add any additional origins from environment variable
if additional_origins := os.getenv("ADDITIONAL_CORS_ORIGINS"):
    allowed_origins.extend(additional_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel deployments
    allow_origins=["*"],  # Allow all origins temporarily for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Register routers
app.include_router(users.router)
app.include_router(events.router)
app.include_router(picks.router)
app.include_router(results.router)
app.include_router(scores.router)
app.include_router(leagues.router)

@app.get("/")
async def root():
    return {"message": "F1 Picks API is running!"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health/db")
async def health_check_db():
    """Health check endpoint that also verifies database connectivity."""
    try:
        # Test database connectivity without dependency injection
        from app.database import get_db_session
        from sqlalchemy import text
        
        async with get_db_session() as session:
            result = await session.execute(text("SELECT 1"))
            db_status = "connected" if result else "disconnected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "version": "1.0.0"
    }
