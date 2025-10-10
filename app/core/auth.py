"""
JWT token utilities for authentication.

This module provides JWT token generation, validation,
and user authentication functions.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from uuid import UUID

from app.core.config import settings


SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT access token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def create_user_token(user_id: UUID, email: str) -> str:
    """
    Create a JWT token for a user.
    
    Args:
        user_id: User's unique ID
        email: User's email address
        
    Returns:
        JWT token string
    """
    token_data = {
        "sub": str(user_id),
        "email": email,
        "type": "access"
    }
    return create_access_token(token_data)


def get_user_from_token(token: str) -> Optional[Dict[str, str]]:
    """
    Extract user information from a JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        User data dict or None if invalid
    """
    payload = verify_access_token(token)
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    email = payload.get("email")
    
    if user_id is None or email is None:
        return None
    
    return {"user_id": user_id, "email": email}