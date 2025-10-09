"""
User database models.

This module defines SQLAlchemy models for user management,
authentication, preferences, and API key management.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Boolean, DateTime, String, Text, Integer, Float, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from app.db.types import ArrayType, UUIDType, get_timestamp_server_default
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import Base


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # Authentication
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Profile information
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Contact information
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    
    # Account management
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Subscription and limits
    subscription_tier: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    monthly_credits: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    credits_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=get_timestamp_server_default(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=get_timestamp_server_default(), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    preferences: Mapped["UserPreferences"] = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    api_keys: Mapped[List["ApiKey"]] = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    videos: Mapped[List["Video"]] = relationship("Video", back_populates="user", cascade="all, delete-orphan")
    avatars: Mapped[List["Avatar"]] = relationship("Avatar", back_populates="user", cascade="all, delete-orphan")
    scripts: Mapped[List["Script"]] = relationship("Script", back_populates="user", cascade="all, delete-orphan")
    publishing_profiles: Mapped[List["PublishingProfile"]] = relationship("PublishingProfile", back_populates="user", cascade="all, delete-orphan")
    platform_credentials: Mapped[List["PlatformCredentials"]] = relationship("PlatformCredentials", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_users_email_active", "email", "is_active"),
        Index("idx_users_username_active", "username", "is_active"),
        Index("idx_users_subscription", "subscription_tier", "subscription_expires_at"),
        Index("idx_users_created_at", "created_at"),
        CheckConstraint("credits_used >= 0", name="check_credits_non_negative"),
        CheckConstraint("monthly_credits >= 0", name="check_monthly_credits_non_negative"),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username
    
    @property
    def is_premium(self) -> bool:
        """Check if user has premium subscription."""
        return (
            self.subscription_tier in ["premium", "enterprise"] and
            (self.subscription_expires_at is None or self.subscription_expires_at > datetime.utcnow())
        )
    
    @property
    def credits_remaining(self) -> int:
        """Get remaining credits for the month."""
        return max(0, self.monthly_credits - self.credits_used)
    
    def can_use_credits(self, amount: int) -> bool:
        """Check if user has enough credits."""
        return self.credits_remaining >= amount
    
    def use_credits(self, amount: int) -> bool:
        """Use credits if available."""
        if self.can_use_credits(amount):
            self.credits_used += amount
            return True
        return False


class UserPreferences(Base):
    """User preferences and settings."""
    
    __tablename__ = "user_preferences"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Notification preferences
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    job_completion_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    marketing_emails: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Default settings
    default_video_quality: Mapped[str] = mapped_column(String(20), default="high", nullable=False)
    default_avatar_style: Mapped[str] = mapped_column(String(50), default="realistic", nullable=False)
    default_voice_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    auto_publish: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # AI preferences
    content_style: Mapped[str] = mapped_column(String(50), default="engaging", nullable=False)
    target_audience: Mapped[str] = mapped_column(String(50), default="general", nullable=False)
    tone_preference: Mapped[str] = mapped_column(String(50), default="friendly", nullable=False)
    
    # Privacy settings
    profile_visibility: Mapped[str] = mapped_column(String(20), default="private", nullable=False)
    analytics_sharing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    data_retention_days: Mapped[int] = mapped_column(Integer, default=365, nullable=False)
    
    # Custom settings (JSON field for extensibility)
    custom_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=get_timestamp_server_default(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=get_timestamp_server_default(), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="preferences")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_preferences_user_id", "user_id"),
        CheckConstraint("data_retention_days > 0", name="check_retention_positive"),
    )
    
    def __repr__(self) -> str:
        return f"<UserPreferences(user_id={self.user_id})>"


class ApiKey(Base):
    """API key model for external integrations."""
    
    __tablename__ = "api_keys"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Key information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    prefix: Mapped[str] = mapped_column(String(10), nullable=False)  # For display purposes
    
    # Permissions and scope
    scopes: Mapped[List[str]] = mapped_column(ArrayType(), nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rate_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Requests per hour
    
    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=get_timestamp_server_default(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=get_timestamp_server_default(), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")
    
    # Indexes
    __table_args__ = (
        Index("idx_api_keys_user_id", "user_id"),
        Index("idx_api_keys_prefix", "prefix"),
        Index("idx_api_keys_active", "is_active", "expires_at"),
        CheckConstraint("usage_count >= 0", name="check_usage_count_non_negative"),
        CheckConstraint("rate_limit > 0", name="check_rate_limit_positive"),
    )
    
    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, name={self.name}, prefix={self.prefix})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if API key is expired."""
        return self.expires_at is not None and self.expires_at < datetime.utcnow()
    
    @property
    def is_valid(self) -> bool:
        """Check if API key is valid for use."""
        return self.is_active and not self.is_expired
    
    def increment_usage(self):
        """Increment usage counter and update last used timestamp."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()


class PasswordReset(Base):
    """Password reset token model."""
    
    __tablename__ = "password_resets"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Token information
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Usage tracking
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # Supports IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=get_timestamp_server_default(), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index("idx_password_resets_user_id", "user_id"),
        Index("idx_password_resets_token", "token_hash", "is_used", "expires_at"),
        Index("idx_password_resets_expires", "expires_at", "is_used"),
    )
    
    def __repr__(self) -> str:
        return f"<PasswordReset(id={self.id}, user_id={self.user_id}, is_used={self.is_used})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if reset token is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if reset token is valid for use."""
        return not self.is_used and not self.is_expired
    
    def mark_used(self, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """Mark token as used."""
        self.is_used = True
        self.used_at = datetime.utcnow()
        self.ip_address = ip_address
        self.user_agent = user_agent


class UserSession(Base):
    """User session tracking for security and analytics."""
    
    __tablename__ = "user_sessions"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Session information
    session_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    device_fingerprint: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Session state
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=get_timestamp_server_default(), nullable=False)
    
    # Geographic information
    country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)  # ISO country code
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=get_timestamp_server_default(), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_sessions_user_id", "user_id"),
        Index("idx_user_sessions_token", "session_token", "is_active"),
        Index("idx_user_sessions_activity", "last_activity_at", "is_active"),
        Index("idx_user_sessions_expires", "expires_at", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if session is valid for use."""
        return self.is_active and not self.is_expired
    
    def extend_session(self, hours: int = 24):
        """Extend session expiration."""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_activity_at = datetime.utcnow()
    
    def end_session(self):
        """End the session."""
        self.is_active = False
        self.ended_at = datetime.utcnow()