"""
Authentication middleware for FastAPI using Supabase JWT tokens.

This module provides dependencies for validating Supabase JWT tokens
and extracting user information from authenticated requests.
"""

import os
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.repositories.user import UserRepository

# Supabase JWT configuration
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
if not SUPABASE_JWT_SECRET:
    # For local development, you can get this from Supabase dashboard
    # Settings > API > JWT Settings > JWT Secret
    SUPABASE_JWT_SECRET = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# HTTP Bearer token scheme
security = HTTPBearer()


class AuthenticationError(HTTPException):
    """Custom exception for authentication errors."""

    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_jwt_token(token: str) -> dict:
    """
    Verify and decode a Supabase JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload containing user information
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        # Decode and verify the JWT token
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    
    Extracts the JWT token from the Authorization header, verifies it,
    and retrieves the corresponding user from the database.
    
    Args:
        credentials: HTTP Bearer credentials from request header
        db: Database session
        
    Returns:
        User model instance for the authenticated user
        
    Raises:
        AuthenticationError: If authentication fails
        
    Usage:
        @app.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id}
    """
    token = credentials.credentials
    
    # Verify and decode the token
    payload = verify_jwt_token(token)
    
    # Extract user ID from token (Supabase uses 'sub' claim for user ID)
    user_id: str = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token missing user ID")
    
    # Get user from database
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise AuthenticationError("User not found")
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    FastAPI dependency to optionally get the current authenticated user.
    
    Similar to get_current_user, but returns None instead of raising an error
    if no valid authentication is provided. Useful for endpoints that work
    with or without authentication.
    
    Args:
        credentials: Optional HTTP Bearer credentials from request header
        db: Database session
        
    Returns:
        User model instance if authenticated, None otherwise
        
    Usage:
        @app.get("/optional-auth")
        async def optional_route(user: Optional[User] = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello {user.name}"}
            return {"message": "Hello guest"}
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_jwt_token(token)
        user_id: str = payload.get("sub")
        
        if not user_id:
            return None
        
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        return user
    except (AuthenticationError, Exception):
        # If authentication fails, return None instead of raising error
        return None


def get_user_id_from_token(token: str) -> str:
    """
    Extract user ID from a JWT token without database lookup.
    
    Useful for lightweight operations where you only need the user ID.
    
    Args:
        token: JWT token string
        
    Returns:
        User ID (UUID string)
        
    Raises:
        AuthenticationError: If token is invalid
    """
    payload = verify_jwt_token(token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise AuthenticationError("Token missing user ID")
    
    return user_id
