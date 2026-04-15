"""
Database configuration and models for the Griot web application.
"""
import os
import uuid
import re
from datetime import datetime, timezone
from typing import Optional, AsyncGenerator
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Enum as SQLEnum,
    JSON,
    Integer,
    Boolean,
    Float,
    ForeignKey,
    text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.engine.url import make_url
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from app.models import JobStatus
import enum
from loguru import logger

def utcnow():
    """Get current UTC time as timezone-naive datetime for database storage."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_db_url() -> str:
    """Get the sync database URL for Agno agents (PgVector, etc.)."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Convert async URL to sync URL for Agno compatibility
        if database_url.startswith("postgresql+asyncpg://"):
            return database_url.replace("postgresql+asyncpg://", "postgresql://")
        return database_url
    else:
        # Fallback to environment variables
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_pass = os.getenv("POSTGRES_PASSWORD", "")
        db_host = os.getenv("POSTGRES_HOST", "localhost")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB", "griot")

        if db_pass:
            return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        else:
            return f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"


def get_async_db_url() -> str:
    """Get the async database URL (postgresql+asyncpg://) for Agno agent storage."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return database_url
    else:
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_pass = os.getenv("POSTGRES_PASSWORD", "")
        db_host = os.getenv("POSTGRES_HOST", "localhost")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB", "griot")

        if db_pass:
            return f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        else:
            return f"postgresql+asyncpg://{db_user}@{db_host}:{db_port}/{db_name}"

class Base(DeclarativeBase):
    pass

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

class APIKeyStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"

class EndpointCategory(enum.Enum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MEDIA = "media"
    UTILITY = "utility"

# MediaType and MediaCategory enums are defined later in the file (lines 205-237)
# to avoid conflicts with the updated definitions

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Nullable for OAuth users
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    verification_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # Stripe subscription fields
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subscription_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    api_keys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="user")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="owner")
    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")

class OAuthAccount(Base):
    """OAuth provider accounts linked to users."""
    __tablename__ = "oauth_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # 'google', 'github', 'discord'
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)  # OAuth provider's user ID
    provider_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_avatar: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    access_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Encrypted in production
    refresh_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Encrypted in production
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")

    # Unique constraint: one provider account per user
    __table_args__ = (
        # Unique constraint on (user_id, provider) combination
        # A user can only link each OAuth provider once
        # e.g., one Google account, one GitHub account per user
        Index('idx_oauth_user_provider', 'user_id', 'provider', unique=True),
        # Index on provider_user_id for fast lookups during OAuth callback
        Index('idx_oauth_provider_user_id', 'provider', 'provider_user_id'),
    )

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)  # Public key identifier
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # Hashed actual key
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # User-friendly name
    status: Mapped[APIKeyStatus] = mapped_column(SQLEnum(APIKeyStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=APIKeyStatus.ACTIVE)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Usage limits
    rate_limit_per_hour: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    monthly_quota: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Tracking
    total_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")
    usage_logs: Mapped[list["APIUsage"]] = relationship("APIUsage", back_populates="api_key")

class Project(Base):
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="projects")
    jobs: Mapped[list["JobRecord"]] = relationship("JobRecord", back_populates="project")

class APIEndpoint(Base):
    __tablename__ = "api_endpoints"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)  # GET, POST, etc.
    category: Mapped[EndpointCategory] = mapped_column(SQLEnum(EndpointCategory, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requires_auth: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Usage statistics
    total_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_response_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    success_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    
    # Relationships
    usage_logs: Mapped[list["APIUsage"]] = relationship("APIUsage", back_populates="endpoint")

class APIUsage(Base):
    __tablename__ = "api_usage"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    api_key_id: Mapped[int] = mapped_column(ForeignKey("api_keys.id"), nullable=False)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("api_endpoints.id"), nullable=False)
    
    # Request details
    request_method: Mapped[str] = mapped_column(String(10), nullable=False)
    request_path: Mapped[str] = mapped_column(String(255), nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Tracking
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 support
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    
    # Job reference if applicable
    job_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Relationships
    api_key: Mapped["APIKey"] = relationship("APIKey", back_populates="usage_logs")
    endpoint: Mapped["APIEndpoint"] = relationship("APIEndpoint", back_populates="usage_logs")

class JobRecord(Base):
    __tablename__ = "jobs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    operation: Mapped[str] = mapped_column(String(100), nullable=False)
    params: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[JobStatus] = mapped_column(SQLEnum(JobStatus, name="jobstatus", native_enum=True, create_constraint=False, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=JobStatus.PENDING)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Enhanced fields for web app
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    api_key_id: Mapped[Optional[int]] = mapped_column(ForeignKey("api_keys.id"), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0=normal, 1=high, -1=low
    
    # Progress tracking
    progress_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_completion: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Resource usage
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_used_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    
    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="jobs")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    last_activity: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

class VideoType(enum.Enum):
    FOOTAGE_TO_VIDEO = "footage_to_video"
    AIIMAGE_TO_VIDEO = "aiimage_to_video" 
    SCENES_TO_VIDEO = "scenes_to_video"
    SHORT_VIDEO_CREATION = "short_video_creation"
    IMAGE_TO_VIDEO = "image_to_video"
    OTHER = "other"

class MediaType(enum.Enum):
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"
    OTHER = "other"

class MediaCategory(enum.Enum):
    # Video categories
    FOOTAGE_TO_VIDEO = "footage_to_video"
    AIIMAGE_TO_VIDEO = "aiimage_to_video"
    SCENES_TO_VIDEO = "scenes_to_video"
    SHORT_VIDEO_CREATION = "short_video_creation"
    IMAGE_TO_VIDEO = "image_to_video"
    VIDEO_GENERATION = "video_generation"  # For VideoGeneratorTab general video generation
    VIDEO_FROM_IMAGE = "video_from_image"  # For VideoGeneratorTab image-to-video generation
    
    # Audio categories
    TEXT_TO_SPEECH = "text_to_speech"
    MUSIC_GENERATION = "music_generation"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    VOICE_CLONING = "voice_cloning"
    
    # Image categories
    IMAGE_GENERATION = "image_generation"
    IMAGE_EDITING = "image_editing"
    IMAGE_UPSCALING = "image_upscaling"
    
    # Media processing categories
    MEDIA_DOWNLOAD = "media_download"
    MEDIA_CONVERSION = "media_conversion"
    METADATA_EXTRACTION = "metadata_extraction"
    YOUTUBE_TRANSCRIPT = "youtube_transcript"
    
    OTHER = "other"

class VideoRecord(Base):
    __tablename__ = "videos"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # Same as job_id
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    video_type: Mapped[VideoType] = mapped_column(SQLEnum(VideoType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    
    # Video file URLs (S3 storage)
    final_video_url: Mapped[str] = mapped_column(String(500), nullable=False)
    video_with_audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    srt_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Video metadata
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # e.g., "1080x1920"
    file_size_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    segments_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Generation metadata
    script_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    voice_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    voice_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Processing metadata
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    background_videos_used: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    generation_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Organization
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    api_key_id: Mapped[Optional[int]] = mapped_column(ForeignKey("api_keys.id"), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # User-defined tags
    
    # Status and tracking
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    download_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    
    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates=None)
    api_key: Mapped[Optional["APIKey"]] = relationship("APIKey", back_populates=None)

class MediaRecord(Base):
    """Unified media library for all generated content (videos, audio, images, documents)."""
    __tablename__ = "media_library"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # Same as job_id
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_type: Mapped[MediaType] = mapped_column(SQLEnum(MediaType, name="mediatype", native_enum=True, create_constraint=False, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    category: Mapped[MediaCategory] = mapped_column(SQLEnum(MediaCategory, name="mediacategory", native_enum=True, create_constraint=False, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    
    # Primary file URL (main output)
    primary_url: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Additional file URLs (related outputs)
    secondary_urls: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"audio": "url", "srt": "url", etc.}
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Media metadata
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # For video/audio
    dimensions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"width": 1080, "height": 1920}
    file_size_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    format: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # mp4, mp3, png, etc.
    
    # Content metadata
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Script, transcript, etc.
    
    # Generation metadata
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Original prompt/input
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Processing metadata
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    generation_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Organization
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    api_key_id: Mapped[Optional[int]] = mapped_column(ForeignKey("api_keys.id"), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # User-defined tags
    
    # Status and tracking
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    download_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    
    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates=None)
    api_key: Mapped[Optional["APIKey"]] = relationship("APIKey", back_populates=None)


class AgentSessionStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AgentMessageRole(enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AgentDocumentStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentSessionRecord(Base):
    """Persistent storage for agent chat sessions."""

    __tablename__ = "agent_sessions"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_hash: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    agent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[AgentSessionStatus] = mapped_column(
        SQLEnum(
            AgentSessionStatus,
            name="agent_session_status",
            native_enum=True,
            create_constraint=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=AgentSessionStatus.ACTIVE,
    )
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)

    messages: Mapped[list["AgentMessageRecord"]] = relationship(
        "AgentMessageRecord",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AgentMessageRecord(Base):
    """Persistent storage for agent conversation messages."""

    __tablename__ = "agent_messages"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("agent_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[AgentMessageRole] = mapped_column(
        SQLEnum(
            AgentMessageRole,
            name="agent_message_role",
            native_enum=True,
            create_constraint=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)

    session: Mapped["AgentSessionRecord"] = relationship("AgentSessionRecord", back_populates="messages")


class AgentKnowledgeBaseRecord(Base):
    """Represents a vector-backed knowledge base for an agent."""

    __tablename__ = "agent_knowledge_bases"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_hash: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vector_table: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    contents_table: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    chunk_overlap: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    document_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    documents: Mapped[list["AgentKnowledgeDocumentRecord"]] = relationship(
        "AgentKnowledgeDocumentRecord",
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AgentKnowledgeDocumentRecord(Base):
    """Represents a document uploaded into a knowledge base."""

    __tablename__ = "agent_knowledge_documents"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agent_knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    storage_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[AgentDocumentStatus] = mapped_column(
        SQLEnum(
            AgentDocumentStatus,
            name="agent_document_status",
            native_enum=True,
            create_constraint=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=AgentDocumentStatus.PENDING,
    )
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    knowledge_base: Mapped["AgentKnowledgeBaseRecord"] = relationship("AgentKnowledgeBaseRecord", back_populates="documents")


class AgentUserPreferenceRecord(Base):
    """Stores per-user agent preference and configuration data."""

    __tablename__ = "agent_user_preferences"
    __table_args__ = (
        UniqueConstraint("owner_hash", name="uq_agent_user_preferences_owner"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class S3URLCacheRecord(Base):
    """Persistent cache for S3 URLs to avoid repeated uploads."""

    __tablename__ = "s3_url_cache"
    __table_args__ = (
        UniqueConstraint("file_path", name="uq_s3_url_cache_file_path"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)  # e.g., "music/filename.mp3"
    s3_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # MD5 or SHA256 for change detection
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # For expiring old URLs
    cached_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)


# ── Studio V2 enums & models ──────────────────────────────────────────────────

class StudioProjectStatus(enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class SceneStatus(enum.Enum):
    EMPTY = "empty"
    SCRIPTED = "scripted"
    AUDIO_READY = "audio_ready"
    MEDIA_READY = "media_ready"
    PREVIEW_READY = "preview_ready"
    FAILED = "failed"

class TrackType(enum.Enum):
    VOICEOVER = "voiceover"
    BACKGROUND_MUSIC = "background_music"
    SOUND_EFFECT = "sound_effect"

class MediaSourceType(enum.Enum):
    STOCK_VIDEO = "stock_video"
    STOCK_IMAGE = "stock_image"
    AI_VIDEO = "ai_video"
    AI_IMAGE = "ai_image"
    USER_UPLOAD = "user_upload"


class StudioProject(Base):
    """A Video Studio V2 project with full timeline persistence."""
    __tablename__ = "studio_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[StudioProjectStatus] = mapped_column(
        SQLEnum(StudioProjectStatus, name="studioprojectstatus", native_enum=True, create_constraint=False,
                values_callable=lambda obj: [e.value for e in obj]),
        nullable=False, default=StudioProjectStatus.DRAFT,
    )

    # Owner (string to support both DB user IDs and API key auth like "env")
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Global settings (voice, resolution, caption style, music, etc.)
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Export results
    final_video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    final_video_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    export_job_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    # Relationships
    scenes: Mapped[list["StudioScene"]] = relationship(
        "StudioScene", back_populates="studio_project",
        cascade="all, delete-orphan", order_by="StudioScene.order_index",
    )
    audio_tracks: Mapped[list["StudioAudioTrack"]] = relationship(
        "StudioAudioTrack", back_populates="studio_project",
        cascade="all, delete-orphan",
    )


class StudioScene(Base):
    """A single scene within a studio project timeline."""
    __tablename__ = "studio_scenes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    studio_project_id: Mapped[str] = mapped_column(
        ForeignKey("studio_projects.id", ondelete="CASCADE"), nullable=False,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Script
    script_text: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Status
    status: Mapped[SceneStatus] = mapped_column(
        SQLEnum(SceneStatus, name="scenestatus", native_enum=True, create_constraint=False,
                values_callable=lambda obj: [e.value for e in obj]),
        nullable=False, default=SceneStatus.EMPTY,
    )

    # TTS Audio
    tts_audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tts_audio_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Word timestamps from Whisper transcription of clean TTS audio
    word_timestamps: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Visual media
    media_source_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    media_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    media_search_terms: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    media_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    media_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timing
    start_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    duration: Mapped[float] = mapped_column(Float, nullable=False, default=3.0)

    # Transition to next scene
    transition_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="crossfade")
    transition_duration: Mapped[float] = mapped_column(Float, nullable=False, default=0.3)

    # Preview
    preview_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    # Relationships
    studio_project: Mapped["StudioProject"] = relationship("StudioProject", back_populates="scenes")


class StudioAudioTrack(Base):
    """A global audio track (background music, SFX) for a project."""
    __tablename__ = "studio_audio_tracks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    studio_project_id: Mapped[str] = mapped_column(
        ForeignKey("studio_projects.id", ondelete="CASCADE"), nullable=False,
    )

    track_type: Mapped[TrackType] = mapped_column(
        SQLEnum(TrackType, name="tracktype", native_enum=True, create_constraint=False,
                values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    audio_url: Mapped[str] = mapped_column(String(500), nullable=False)

    # Timing
    start_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Mix settings
    volume: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    fade_in: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fade_out: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)

    # Relationships
    studio_project: Mapped["StudioProject"] = relationship("StudioProject", back_populates="audio_tracks")


class DatabaseService:
    """Database service for job persistence."""
    
    def __init__(self):
        self.engine = None
        self.async_session = None
        self._db_available = False

    async def _ensure_database_exists(self, database_url: str) -> bool:
        """Create target Postgres database if it does not already exist using raw asyncpg."""
        try:
            import asyncpg
            parsed_url = make_url(database_url)
        except Exception as e:
            logger.warning(f"Could not import asyncpg or parse DATABASE_URL: {e}")
            return False

        target_db = parsed_url.database
        if not target_db:
            logger.warning("DATABASE_URL has no database name; cannot auto-create database")
            return False

        # Guard against SQL injection in the identifier
        if not re.fullmatch(r"[A-Za-z0-9_]+", target_db):
            logger.warning(
                f"Database name '{target_db}' contains unsupported characters; skipping auto-create"
            )
            return False

        # Build connection parameters for the 'postgres' system database
        admin_url = parsed_url.set(database="postgres")
        
        try:
            # Connect directly with asyncpg (bypasses SQLAlchemy transaction management)
            conn = await asyncpg.connect(str(admin_url))
            
            try:
                # Check if database already exists
                db_exists = await conn.fetchval(
                    "SELECT 1 FROM pg_database WHERE datname = $1",
                    target_db
                )
                
                if db_exists:
                    logger.info(f"Database '{target_db}' already exists")
                    return True
                
                # Create database (no transaction needed at connection level)
                await conn.execute(f'CREATE DATABASE "{target_db}"')
                logger.info(f"✅ Created missing database '{target_db}'")
                return True
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.warning(f"Failed to auto-create database '{target_db}': {e}")
            return False
        
    async def initialize(self):
        """Initialize database connection."""
        if self._db_available:
            return  # Already initialized
            
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@postgres:5432/griot"
        )

        try:
            logger.info(f"Connecting to database: {database_url.replace('://', '://[HIDDEN]@')}")

            self.engine = create_async_engine(
                database_url,
                echo=False,  # Set to True for SQL debugging
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )

            self.async_session = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test the connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            self._db_available = True
            logger.info("Database service initialized successfully")
            
        except Exception as e:
            if "does not exist" in str(e):
                logger.warning(
                    f"Database connection failed because target database is missing: {e}. "
                    "Attempting to create it automatically."
                )
                created = await self._ensure_database_exists(database_url)
                if created:
                    try:
                        self.engine = create_async_engine(
                            database_url,
                            echo=False,
                            pool_size=10,
                            max_overflow=20,
                            pool_pre_ping=True,
                            pool_recycle=3600,
                        )
                        self.async_session = async_sessionmaker(
                            self.engine,
                            class_=AsyncSession,
                            expire_on_commit=False,
                        )
                        async with self.engine.begin() as conn:
                            await conn.execute(text("SELECT 1"))
                        self._db_available = True
                        logger.info("Database service initialized successfully after auto-create")
                        return
                    except Exception as retry_error:
                        logger.warning(
                            "Database reconnection failed after auto-create: "
                            f"{retry_error}. Application will continue without database functionality."
                        )

            logger.warning(f"Database connection failed: {e}. Application will continue without database functionality.")
            self.engine = None
            self.async_session = None
            self._db_available = False
        
    def is_database_available(self) -> bool:
        """Check if database is available."""
        return self._db_available
        
    async def create_tables(self):
        """Create database tables."""
        if not self.engine:
            await self.initialize()
        
        if self.engine:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created")
        else:
            logger.error("Failed to initialize database engine")
    
    async def update_enums(self):
        """Update database enums to include any missing values and fix enum issues."""
        if not self.engine:
            await self.initialize()
        
        if self.engine:
            try:
                logger.info("🔧 Checking and fixing database enums...")
                
                # Step 1: Add missing enum values (must be in separate transaction)
                await self._add_missing_enum_values()
                
                # Step 2: Fix invalid enum data (separate transaction after enum values are committed)
                await self._fix_invalid_enum_data_separate()
                        
                logger.info("✅ Database enum update completed successfully")
            except Exception as e:
                logger.warning(f"Database enum update failed (this is OK if enums don't exist yet): {e}")
        else:
            logger.error("Failed to initialize database engine for enum update")
    
    async def _add_missing_enum_values(self):
        """Add missing enum values in a separate transaction."""
        if not self.engine:
            logger.error("Database engine not initialized")
            return
            
        try:
            from sqlalchemy import text
            
            # Define expected enum values based on Python enums
            enum_definitions = {
                'apikeystatus': ['active', 'inactive', 'revoked'],
                'videotype': ['footage_to_video', 'aiimage_to_video', 'scenes_to_video', 'short_video_creation', 'image_to_video', 'other'],
                'userrole': ['admin', 'user', 'viewer'],
                'endpointcategory': ['image', 'audio', 'video', 'ai', 'media', 'other'],
                'jobstatus': ['pending', 'processing', 'completed', 'failed'],
                'mediatype': ['video', 'audio', 'image', 'document'],
                'mediacategory': ['footage_to_video', 'aiimage_to_video', 'scenes_to_video', 'short_video_creation', 'image_to_video', 'youtube_transcript', 'other'],
                'agent_session_status': ['active', 'completed', 'archived'],
                'agent_document_status': ['pending', 'processing', 'completed', 'failed'],
                'agent_message_role': ['user', 'assistant', 'system'],
                'studioprojectstatus': ['draft', 'generating', 'completed', 'failed'],
                'scenestatus': ['empty', 'scripted', 'audio_ready', 'media_ready', 'preview_ready', 'failed'],
                'tracktype': ['voiceover', 'background_music', 'sound_effect'],
                'mediasourcetype': ['stock_video', 'stock_image', 'ai_video', 'ai_image', 'user_upload'],
            }
            
            for enum_name, expected_values in enum_definitions.items():
                try:
                    # Use a separate connection for each enum to check what exists
                    async with self.engine.connect() as conn:
                        # Check if enum type exists
                        type_check = await conn.execute(text("""
                            SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = :enum_name)
                        """), {"enum_name": enum_name})
                        
                        if not type_check.scalar():
                            logger.debug(f"Enum {enum_name} does not exist yet, skipping...")
                            continue
                        
                        # Get current enum values
                        result = await conn.execute(text("""
                            SELECT enumlabel FROM pg_enum 
                            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = :enum_name)
                            ORDER BY enumlabel
                        """), {"enum_name": enum_name})
                        current_values = [row[0] for row in result]
                    
                    # Add missing values one by one, each in its own autocommitted transaction
                    missing_values = set(expected_values) - set(current_values)
                    for value in missing_values:
                        try:
                            # Each enum value addition gets its own connection with autocommit
                            async with self.engine.connect() as conn:
                                await conn.execute(text(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'"))
                                await conn.commit()  # Explicit commit
                                logger.info(f"✅ Added '{value}' to {enum_name} enum")
                        except Exception as e:
                            logger.warning(f"⚠️  Could not add '{value}' to {enum_name}: {e}")
                    
                    # Log current state
                    if missing_values:
                        logger.info(f"📊 Fixed {enum_name}: added {len(missing_values)} missing values")
                    else:
                        logger.debug(f"✅ {enum_name} enum is up to date")
                        
                except Exception as e:
                    logger.warning(f"⚠️  Could not process {enum_name} enum: {e}")
                        
        except Exception as e:
            logger.warning(f"Could not add missing enum values: {e}")
    
    async def _fix_invalid_enum_data_separate(self):
        """Fix invalid enum values in existing database records in a separate transaction."""
        if not self.engine:
            logger.error("Database engine not initialized")
            return
            
        try:
            from sqlalchemy import text
            
            async with self.engine.begin() as conn:
                # Fix API keys with invalid status values
                api_key_fixes = [
                    ("true", "active"), ("1", "active"), ("enabled", "active"), ("valid", "active"),
                    ("false", "inactive"), ("0", "inactive"), ("disabled", "inactive"), ("invalid", "inactive")
                ]
                
                for old_val, new_val in api_key_fixes:
                    try:
                        result = await conn.execute(text("""
                            UPDATE api_keys SET status = :new_val 
                            WHERE status::text = :old_val
                        """), {"old_val": old_val, "new_val": new_val})
                        
                        if result.rowcount > 0:
                            logger.info(f"🔧 Fixed {result.rowcount} API keys: '{old_val}' -> '{new_val}'")
                    except Exception as e:
                        logger.warning(f"Could not fix API key status '{old_val}': {e}")
                
                # Fix any other enum data issues as needed
                # Add more fixes here if other enums have invalid data
                
        except Exception as e:
            logger.warning(f"Could not fix invalid enum data: {e}")
    
    async def migrate_schema(self):
        """Migrate database schema by adding missing columns to existing tables."""
        if not self.engine:
            await self.initialize()
        
        if self.engine:
            try:
                logger.info("🔧 Checking and migrating database schema...")
                
                async with self.engine.begin() as conn:
                    from sqlalchemy import text
                    
                    # Check and add missing columns to users table
                    await self._migrate_users_table(conn)
                    
                    # Add more table migrations here as needed
                    
                logger.info("✅ Database schema migration completed successfully")
            except Exception as e:
                logger.warning(f"Database schema migration failed: {e}")
        else:
            logger.error("Failed to initialize database engine for schema migration")
    
    async def _migrate_users_table(self, conn):
        """Add missing columns to the users table."""
        try:
            # Check if is_verified column exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name = 'is_verified'
                )
            """))
            
            if not result.scalar():
                logger.info("📝 Adding is_verified column to users table...")
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT FALSE
                """))
                logger.info("✅ Successfully added is_verified column")
            else:
                logger.debug("✅ is_verified column already exists")
            
            # Check if verification_token column exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name = 'verification_token'
                )
            """))
            
            if not result.scalar():
                logger.info("📝 Adding verification_token columns to users table...")
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN verification_token VARCHAR(255) UNIQUE,
                    ADD COLUMN verification_token_expires_at TIMESTAMP
                """))
                logger.info("✅ Successfully added verification token columns")
            else:
                logger.debug("✅ verification_token columns already exist")

            # Check and add Stripe / subscription columns
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name = 'stripe_customer_id'
                )
            """))
            if not result.scalar():
                logger.info("📝 Adding stripe_customer_id column to users table...")
                await conn.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN stripe_customer_id VARCHAR(255)
                """))
                logger.info("✅ Successfully added stripe_customer_id column")
            else:
                logger.debug("✅ stripe_customer_id column already exists")

            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name = 'stripe_subscription_id'
                )
            """))
            if not result.scalar():
                logger.info("📝 Adding stripe_subscription_id column to users table...")
                await conn.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN stripe_subscription_id VARCHAR(255)
                """))
                logger.info("✅ Successfully added stripe_subscription_id column")
            else:
                logger.debug("✅ stripe_subscription_id column already exists")

            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name = 'subscription_status'
                )
            """))
            if not result.scalar():
                logger.info("📝 Adding subscription_status column to users table...")
                await conn.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN subscription_status VARCHAR(50)
                """))
                logger.info("✅ Successfully added subscription_status column")
            else:
                logger.debug("✅ subscription_status column already exists")

            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name = 'subscription_expires_at'
                )
            """))
            if not result.scalar():
                logger.info("📝 Adding subscription_expires_at column to users table...")
                await conn.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN subscription_expires_at TIMESTAMP
                """))
                logger.info("✅ Successfully added subscription_expires_at column")
            else:
                logger.debug("✅ subscription_expires_at column already exists")

            # Check if avatar_url column exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'users' AND column_name = 'avatar_url'
                )
            """))
            if not result.scalar():
                logger.info("📝 Adding avatar_url column to users table...")
                await conn.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN avatar_url VARCHAR(500)
                """))
                logger.info("✅ Successfully added avatar_url column")
            else:
                logger.debug("✅ avatar_url column already exists")

        except Exception as e:
            logger.warning(f"Could not migrate users table: {e}")
            raise
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        if not self._db_available:
            raise RuntimeError("Database is not available")
            
        if self.async_session:
            async with self.async_session() as session:
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()
        else:
            raise RuntimeError("Failed to initialize database session")
                
    async def close(self):
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")

# Global database service instance
database_service = DatabaseService()
