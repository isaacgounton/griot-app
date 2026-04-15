"""
JWT-based authentication for web sessions.
Replaces the API key creation on every login with stateless JWT tokens.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from fastapi import HTTPException, Cookie, Response
from pydantic import BaseModel

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("BETTER_AUTH_SECRET", "your-secret-key-change-in-production"))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

class TokenData(BaseModel):
    user_id: int
    username: str
    email: str
    role: str

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: User data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData with user information

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id: int = payload.get("user_id")
        username: str = payload.get("username")
        email: str = payload.get("email")
        role: str = payload.get("role")

        if user_id is None or username is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )

        return TokenData(
            user_id=user_id,
            username=username,
            email=email,
            role=role
        )

    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Could not validate credentials: {str(e)}"
        )

def set_auth_cookie(response: Response, token: str):
    """
    Set JWT token as HTTP-only cookie.

    Args:
        response: FastAPI Response object
        token: JWT token to set
    """
    # Only use secure cookies in production (HTTPS)
    # In development (HTTP), secure must be False for cookies to work
    is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,  # Prevents JavaScript access (XSS protection)
        secure=is_production,  # HTTPS only in production, HTTP allowed in dev
        samesite="lax",  # CSRF protection - allows cookie on navigation
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds (7 days)
        path="/",  # Make cookie available across entire domain
        # Don't set domain - let browser handle it automatically for better compatibility
    )

def get_current_user_from_cookie(
    access_token: Optional[str] = Cookie(None)
) -> TokenData:
    """
    Get current user from JWT cookie.

    Args:
        access_token: JWT token from cookie

    Returns:
        TokenData with user information

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    # Remove "Bearer " prefix if present
    if access_token.startswith("Bearer "):
        access_token = access_token[7:]

    return verify_token(access_token)
