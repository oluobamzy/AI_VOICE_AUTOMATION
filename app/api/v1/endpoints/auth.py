"""
Authentication endpoints for user registration, login, and management.

This module provides endpoints for user authentication including
registration, login, logout, and user profile management.
"""

from datetime import timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.auth import create_user_token, get_user_from_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.password import get_password_hash, verify_password
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, Token, UserUpdate, UserProfile
)

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        db: Database session
        
    Returns:
        Current user instance
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user info from token
    user_data = get_user_from_token(credentials.credentials)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_query = select(User).where(User.id == user_data["user_id"])
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Register a new user account.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Authentication token and user information
        
    Raises:
        HTTPException: If email or username already exists
    """
    try:
        # Hash the password - check length first
        password_str = user_data.password.get_secret_value()
        if len(password_str.encode('utf-8')) > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is too long. Please use a shorter password."
            )
        
        hashed_password = get_password_hash(password_str)
        
        # Create new user
        user = User(
            id=uuid4(),
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            first_name=user_data.full_name.split()[0] if user_data.full_name else None,
            last_name=" ".join(user_data.full_name.split()[1:]) if user_data.full_name and len(user_data.full_name.split()) > 1 else None,
            is_active=user_data.is_active,
            is_verified=False  # Email verification can be added later
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Create access token
        access_token = create_user_token(user.id, user.email)
        
        # Create user response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login_at
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
        
    except IntegrityError as e:
        await db.rollback()
        if "email" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        elif "username" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User registration failed"
            )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Authenticate user and return access token.
    
    Args:
        login_data: User login credentials
        db: Database session
        
    Returns:
        Authentication token and user information
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by username or email
    user_query = select(User).where(
        (User.username == login_data.username) | (User.email == login_data.username)
    )
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify password
    password_str = login_data.password.get_secret_value()
    if len(password_str.encode('utf-8')) > 72:
        password_str = password_str.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    
    if not verify_password(password_str, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is disabled"
        )
    
    # Update last login time
    from datetime import datetime
    user.last_login_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    
    # Create access token
    access_token = create_user_token(user.id, user.email)
    
    # Create user response
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login_at
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_response
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login=current_user.last_login_at
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Update current authenticated user information.
    
    Args:
        user_update: User update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user information
    """
    # Update user fields
    if user_update.email is not None:
        current_user.email = user_update.email
    if user_update.full_name is not None:
        if user_update.full_name:
            name_parts = user_update.full_name.split()
            current_user.first_name = name_parts[0]
            current_user.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else None
        else:
            current_user.first_name = None
            current_user.last_name = None
    if user_update.is_active is not None:
        current_user.is_active = user_update.is_active
    
    try:
        await db.commit()
        await db.refresh(current_user)
        
        return UserResponse(
            id=current_user.id,
            email=current_user.email,
            username=current_user.username,
            full_name=current_user.full_name,
            is_active=current_user.is_active,
            is_superuser=current_user.is_superuser,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
            last_login=current_user.last_login_at
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )


@router.post("/logout")
async def logout_user():
    """
    Logout user (client should discard the token).
    
    Returns:
        Success message
    """
    # In a JWT implementation, logout is handled client-side by discarding the token
    # For more security, you could implement token blacklisting
    return {"message": "Successfully logged out"}