"""
User-related Pydantic schemas.

This module defines request/response schemas for user management,
authentication, and user profile operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from pydantic.types import SecretStr


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    full_name: Optional[str] = Field(None, max_length=200, description="Full name")
    is_active: bool = Field(default=True, description="Whether user is active")
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """Validate username format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v.lower()


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: SecretStr = Field(..., min_length=8, description="User password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @model_validator(mode='after')
    def validate_passwords_match(self):
        """Ensure password and confirm_password match."""
        if self.password and self.confirm_password and self.password.get_secret_value() != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength."""
        password = v.get_secret_value()
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema for user response data."""
    id: UUID = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    is_active: bool = Field(..., description="Whether user is active")
    is_superuser: bool = Field(default=False, description="Whether user is superuser")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str = Field(..., description="Username or email")
    password: SecretStr = Field(..., description="User password")
    remember_me: bool = Field(default=False, description="Remember login session")


class UserProfile(BaseModel):
    """Schema for user profile information."""
    id: UUID = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    location: Optional[str] = Field(None, max_length=100, description="User location")
    website: Optional[str] = Field(None, description="User website")
    social_links: Dict[str, str] = Field(default_factory=dict, description="Social media links")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    created_at: datetime = Field(..., description="Account creation date")
    
    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """Schema for user statistics."""
    total_videos: int = Field(default=0, ge=0, description="Total videos processed")
    total_jobs: int = Field(default=0, ge=0, description="Total jobs created")
    successful_jobs: int = Field(default=0, ge=0, description="Successful jobs")
    failed_jobs: int = Field(default=0, ge=0, description="Failed jobs")
    total_processing_time: float = Field(default=0.0, ge=0, description="Total processing time in seconds")
    storage_used: int = Field(default=0, ge=0, description="Storage used in bytes")
    api_calls_count: int = Field(default=0, ge=0, description="Total API calls made")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    
    class Config:
        from_attributes = True


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str = Field(..., description="Password reset token")
    new_password: SecretStr = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @model_validator(mode='after')
    def validate_passwords_match(self):
        """Ensure password and confirm_password match."""
        if self.new_password and self.confirm_password and self.new_password.get_secret_value() != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserPreferences(BaseModel):
    """Schema for user preferences."""
    default_video_quality: str = Field(default="high", description="Default video quality")
    default_avatar_template: Optional[str] = Field(None, description="Default avatar template")
    auto_publish_platforms: List[str] = Field(default_factory=list, description="Auto-publish platforms")
    notification_settings: Dict[str, bool] = Field(default_factory=dict, description="Notification preferences")
    api_rate_limit: int = Field(default=60, ge=1, le=1000, description="API rate limit per minute")
    storage_limit_gb: int = Field(default=10, ge=1, le=1000, description="Storage limit in GB")
    
    @field_validator("default_video_quality")
    @classmethod
    def validate_video_quality(cls, v):
        allowed_qualities = ["low", "medium", "high", "ultra"]
        if v not in allowed_qualities:
            raise ValueError(f"Video quality must be one of: {', '.join(allowed_qualities)}")
        return v
    
    @field_validator("auto_publish_platforms")
    @classmethod
    def validate_platforms(cls, v):
        allowed_platforms = ["youtube", "tiktok", "instagram", "twitter", "facebook", "linkedin"]
        for platform in v:
            if platform not in allowed_platforms:
                raise ValueError(f"Invalid platform: {platform}")
        return v


class ApiKey(BaseModel):
    """Schema for API key management."""
    id: UUID = Field(..., description="API key ID")
    name: str = Field(..., description="API key name")
    key_prefix: str = Field(..., description="API key prefix (first 8 characters)")
    permissions: List[str] = Field(default_factory=list, description="API key permissions")
    is_active: bool = Field(default=True, description="Whether API key is active")
    expires_at: Optional[datetime] = Field(None, description="API key expiration")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    
    class Config:
        from_attributes = True


class ApiKeyCreate(BaseModel):
    """Schema for creating an API key."""
    name: str = Field(..., min_length=1, max_length=100, description="API key name")
    permissions: List[str] = Field(default_factory=list, description="API key permissions")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Expiration in days")
    
    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v):
        allowed_permissions = [
            "videos:read", "videos:write", "videos:delete",
            "jobs:read", "jobs:write", "jobs:delete",
            "users:read", "users:write", "admin"
        ]
        for permission in v:
            if permission not in allowed_permissions:
                raise ValueError(f"Invalid permission: {permission}")
        return v


class ApiKeyResponse(BaseModel):
    """Schema for API key response."""
    id: UUID = Field(..., description="API key ID")
    name: str = Field(..., description="API key name")
    key_preview: str = Field(..., description="Masked API key for display")
    permissions: List[str] = Field(..., description="API key permissions")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    is_active: bool = Field(..., description="Whether the key is active")
    
    class Config:
        from_attributes = True