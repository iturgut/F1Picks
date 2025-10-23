from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="F1 Picks API",
    description="API for F1 prediction game",
    version="1.0.0"
)

# Configure CORS
allowed_origins = [
    "http://localhost:3000",  # Local development
    "https://f1picks.vercel.app",  # Production frontend (update with your actual domain)
]

# Add any additional origins from environment variable
if additional_origins := os.getenv("ADDITIONAL_CORS_ORIGINS"):
    allowed_origins.extend(additional_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "F1 Picks API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
