"""
Dashboard API endpoints for web UI management.
Provides stats, user management, and system information.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.utils.auth import get_current_user
from app.services.database.database_service import db_job_service
from app.services.api_key import api_key_service
from app.services.settings.user_service import user_service
from app.services.settings import settings_service
from app.models import JobStatus, JobType
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


async def calculate_average_processing_time() -> float:
    """Calculate average processing time for completed jobs in seconds."""
    try:
        from app.services.database.database_service import db_job_service
        
        # Get completed jobs
        completed_jobs = await db_job_service.get_jobs_by_status(JobStatus.COMPLETED)
        
        if not completed_jobs:
            return 0.0
        
        total_time = 0
        valid_jobs = 0
        
        # Only process the most recent 100 jobs for performance
        recent_jobs = completed_jobs[:100]
        
        for job in recent_jobs:
            # Calculate processing time from created_at to updated_at
            try:
                created_at = datetime.fromisoformat(job.created_at.replace('Z', '+00:00'))
                updated_at = datetime.fromisoformat(job.updated_at.replace('Z', '+00:00'))
                processing_time = (updated_at - created_at).total_seconds()
                
                # Only include reasonable processing times (between 1 second and 1 hour)
                if 1 <= processing_time <= 3600:
                    total_time += processing_time
                    valid_jobs += 1
            except (ValueError, AttributeError):
                continue
        
        return total_time / valid_jobs if valid_jobs > 0 else 0.0
    except Exception as e:
        logger.error(f"Error calculating average processing time: {e}")
        return 0.0

async def calculate_storage_usage() -> tuple[Optional[float], Optional[float]]:
    """Calculate storage usage from static files and job outputs."""
    try:
        # Get storage paths from environment or use defaults
        static_path = os.getenv('STATIC_FILES_PATH', '/app/static')
        data_path = os.getenv('DATA_PATH', '/app/data')
        
        total_used = 0
        paths_to_check = [static_path, data_path]
        
        for path in paths_to_check:
            if os.path.exists(path):
                try:
                    # Calculate directory size
                    total_size = 0
                    for dirpath, dirnames, filenames in os.walk(path):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            try:
                                total_size += os.path.getsize(filepath)
                            except (OSError, IOError):
                                continue
                    total_used += total_size
                except Exception as e:
                    logger.warning(f"Failed to calculate size for {path}: {e}")
        
        # Convert to GB
        used_gb = total_used / (1024 ** 3)
        
        # Get total disk space for the mount point
        try:
            disk_usage = shutil.disk_usage('/')
            total_gb = disk_usage.total / (1024 ** 3)
        except Exception as e:
            logger.warning(f"Failed to get total disk space: {e}")
            total_gb = 100.0  # Fallback to 100GB
        
        logger.info(f"Storage usage: {used_gb:.2f}GB of {total_gb:.2f}GB")
        return round(used_gb, 2), round(total_gb, 2)
        
    except Exception as e:
        logger.warning(f"Failed to calculate storage usage: {e}")
        return None, None

# Pydantic models for requests/responses
class DashboardStats(BaseModel):
    total_videos: int
    active_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_users: int
    active_api_keys: int
    storage_used_gb: Optional[float] = None
    storage_total_gb: Optional[float] = None
    avg_processing_time_seconds: Optional[float] = None

class UserInfo(BaseModel):
    id: str
    email: str
    role: str
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    projects_count: int
    api_keys_count: int

class ApiKeyInfo(BaseModel):
    id: str
    name: str
    key: str
    user_id: str
    user_email: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]
    expires_at: Optional[datetime]
    usage_count: int
    rate_limit: int
    permissions: List[str]

class ApiKeysResponse(BaseModel):
    api_keys: List[ApiKeyInfo]
    total: int
    pages: int

class SystemSettings(BaseModel):
    auto_refresh: bool
    email_notifications: bool
    api_logging: bool
    max_concurrent_jobs: int
    default_video_resolution: str
    storage_retention_days: int

class CreateUserRequest(BaseModel):
    email: str
    role: str
    password: Optional[str] = None

class CreateApiKeyRequest(BaseModel):
    name: str
    user_id: Optional[str] = None
    rate_limit: int = 100
    permissions: List[str] = []
    expires_at: Optional[datetime] = None

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get dashboard statistics overview."""
    try:
        # Get real job statistics from database with error handling
        try:
            job_counts = await db_job_service.get_job_count_by_status()
        except Exception as e:
            logger.warning(f"Failed to get job counts: {e}")
            job_counts = {}
        
        # Count completed video creation jobs specifically
        # These are the job types that actually create videos (not just process them)
        video_creation_types = {
            JobType.AIIMAGE_TO_VIDEO,
            JobType.FOOTAGE_TO_VIDEO, 
            JobType.SCENES_TO_VIDEO,
            JobType.SHORT_VIDEO_CREATION,
            JobType.IMAGE_TO_VIDEO,
            JobType.YOUTUBE_SHORTS
        }
        
        # Get count of completed video creation jobs efficiently using database query
        try:
            total_videos = await db_job_service.get_video_creation_jobs_count(video_creation_types)
            logger.info(f"Dashboard stats: Found {total_videos} completed video creation jobs")
        except Exception as e:
            logger.warning(f"Failed to get video creation jobs count: {e}")
            total_videos = 0
        
        # Calculate average processing time for completed jobs
        try:
            avg_processing_time = await calculate_average_processing_time()
        except Exception as e:
            logger.warning(f"Failed to calculate average processing time: {e}")
            avg_processing_time = 0.0
        
        # Calculate storage usage
        try:
            storage_used, storage_total = await calculate_storage_usage()
        except Exception as e:
            logger.warning(f"Failed to calculate storage usage: {e}")
            storage_used, storage_total = None, None
        
        # Get real user and API key stats
        try:
            user_stats = await user_service.get_user_stats()
            api_key_stats = await api_key_service.get_api_key_stats()
        except Exception as e:
            logger.warning(f"Failed to get user/API key stats: {e}")
            user_stats = {"total_users": 0}
            api_key_stats = {"active_keys": 0}

        stats = DashboardStats(
            total_videos=total_videos,
            active_jobs=job_counts.get(JobStatus.PROCESSING, 0) + job_counts.get(JobStatus.PENDING, 0),
            completed_jobs=job_counts.get(JobStatus.COMPLETED, 0),
            failed_jobs=job_counts.get(JobStatus.FAILED, 0),
            total_users=user_stats.get("total_users", 0),
            active_api_keys=api_key_stats.get("active_keys", 0),
            storage_used_gb=storage_used,
            storage_total_gb=storage_total,
            avg_processing_time_seconds=avg_processing_time
        )
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard statistics"
        )

class RecentActivity(BaseModel):
    id: str
    type: str
    title: str
    timestamp: str
    status: str
    details: Optional[str] = None
    operation: Optional[str] = None
    progress: Optional[int] = None

@router.get("/recent-activity", response_model=List[RecentActivity])
async def get_recent_activity(
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get recent activity from jobs and system events."""
    try:
        # Get recent jobs from database
        recent_jobs = await db_job_service.get_all_jobs(limit=limit * 2)  # Get more to filter
        
        # Define video creation job types for better activity classification
        video_creation_types = {
            JobType.AIIMAGE_TO_VIDEO,
            JobType.FOOTAGE_TO_VIDEO, 
            JobType.SCENES_TO_VIDEO,
            JobType.SHORT_VIDEO_CREATION,
            JobType.IMAGE_TO_VIDEO,
            JobType.YOUTUBE_SHORTS
        }
        
        activities = []
        # Sort jobs by most recent (updated_at or created_at) and take the most recent ones
        sorted_jobs = sorted(recent_jobs, key=lambda job: job.updated_at or job.created_at, reverse=True)
        for job in sorted_jobs[:limit]:  # Get the most recent ones
            # Determine activity type and title based on job operation
            if job.operation in video_creation_types:
                if job.status == JobStatus.COMPLETED:
                    activity_type = 'video_created'
                    title = f"Video created: {job.operation.replace('_', ' ').title()}"
                else:
                    activity_type = 'job_completed'
                    title = f"Video creation {'failed' if job.status == JobStatus.FAILED else 'processing'}: {job.operation.replace('_', ' ').title()}"
            elif job.operation == JobType.AI_SCRIPT_GENERATION:
                activity_type = 'job_completed'
                title = f"Script generation {'completed' if job.status == JobStatus.COMPLETED else 'failed'}"
            else:
                activity_type = 'job_completed'
                title = f"Job {job.operation.replace('_', ' ').title()} {'completed' if job.status == JobStatus.COMPLETED else 'failed'}"
            
            # Calculate time ago
            now = datetime.utcnow()
            job_time = job.updated_at if job.updated_at else job.created_at
            if isinstance(job_time, str):
                job_time = datetime.fromisoformat(job_time.replace('Z', '+00:00'))
            
            time_diff = now - job_time.replace(tzinfo=None)
            if time_diff.total_seconds() < 60:
                timestamp = "Just now"
            elif time_diff.total_seconds() < 3600:
                minutes = int(time_diff.total_seconds() / 60)
                timestamp = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif time_diff.total_seconds() < 86400:
                hours = int(time_diff.total_seconds() / 3600)
                timestamp = f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = int(time_diff.total_seconds() / 86400)
                timestamp = f"{days} day{'s' if days != 1 else ''} ago"
            
            # Map job status to activity status
            if job.status == JobStatus.COMPLETED:
                status = 'success'
            elif job.status == JobStatus.FAILED:
                status = 'error'
            else:
                status = 'info'
            
            activities.append(RecentActivity(
                id=job.id,
                type=activity_type,
                title=title,
                timestamp=timestamp,
                status=status,
                operation=str(job.operation),
                progress=getattr(job, 'progress', None),
                details=f"Operation: {str(job.operation).replace('_', ' ').title()}" if job.operation else None
            ))
        
        return activities
    except Exception as e:
        logger.error(f"Failed to get recent activity: {e}")
        # Return empty list on error rather than failing
        return []

@router.get("/users", response_model=List[UserInfo])
async def get_users(
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    role: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get list of users with filtering and pagination."""
    try:
        result = await user_service.list_users(
            page=page,
            limit=limit,
            search=search,
            role_filter=role
        )
        
        users = []
        for user_data in result["users"]:
            users.append(UserInfo(
                id=user_data["id"],
                email=user_data["email"],
                role=user_data["role"],
                created_at=datetime.fromisoformat(user_data["created_at"]),
                last_login=datetime.fromisoformat(user_data["last_login"]) if user_data["last_login"] else None,
                is_active=user_data["is_active"],
                projects_count=user_data["projects_count"],
                api_keys_count=user_data["api_keys_count"]
            ))
        
        return users
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.post("/users", response_model=UserInfo)
async def create_user(
    user_data: CreateUserRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new user."""
    try:
        create_data = {
            "email": user_data.email,
            "role": user_data.role,
            "password": user_data.password or "temp_password_123"  # Generate secure password if not provided
        }
        
        result = await user_service.create_user(create_data)
        
        return UserInfo(
            id=result["id"],
            email=result["email"],
            role=result["role"],
            created_at=datetime.fromisoformat(result["created_at"]),
            last_login=datetime.fromisoformat(result["last_login"]) if result["last_login"] else None,
            is_active=result["is_active"],
            projects_count=0,
            api_keys_count=0
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a user."""
    try:
        success = await user_service.delete_user(int(user_id))
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": f"User {user_id} deleted successfully"}
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

@router.get("/api-keys", response_model=ApiKeysResponse)
async def get_api_keys(
    request: Request,
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get list of API keys with filtering and pagination.
    
    Admins can see all API keys, regular users can only see their own.
    """
    try:
        # Check if user is admin or regular user
        api_key_info = getattr(request.state, "api_key_info", None)
        user_id_filter = None
        
        # Non-admin users can only see their own API keys
        if api_key_info and api_key_info.get("user_role") != "admin":
            caller_user_id = api_key_info.get("user_id")
            if caller_user_id:
                user_id_filter = int(caller_user_id)
            else:
                # If we can't determine the user, return empty list
                return ApiKeysResponse(api_keys=[], total=0, pages=0)
        
        result = await api_key_service.list_api_keys(
            page=page,
            limit=limit,
            search=search,
            status_filter=status_filter,
            user_id=user_id_filter
        )
        
        api_keys = []
        for key_data in result["api_keys"]:
            api_keys.append(ApiKeyInfo(
                id=key_data["key_id"],
                name=key_data["name"],
                key=key_data["key"],
                user_id=key_data["user_id"],
                user_email=key_data["user_email"],
                is_active=key_data["is_active"],
                created_at=datetime.fromisoformat(key_data["created_at"]),
                last_used=datetime.fromisoformat(key_data["last_used"]) if key_data["last_used"] else None,
                expires_at=datetime.fromisoformat(key_data["expires_at"]) if key_data["expires_at"] else None,
                usage_count=key_data["usage_count"],
                rate_limit=key_data["rate_limit"] or 100,
                permissions=key_data["permissions"]
            ))
        
        return ApiKeysResponse(
            api_keys=api_keys,
            total=result["pagination"]["total_count"],
            pages=result["pagination"]["total_pages"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API keys"
        )

@router.post("/api-keys", response_model=ApiKeyInfo)
async def create_api_key(
    key_data: CreateApiKeyRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new API key."""
    try:
        # Enforce that callers cannot create API keys for other users unless admin
        create_data = {
            "name": key_data.name,
            "user_id": key_data.user_id if key_data.user_id else None,
            "rate_limit": key_data.rate_limit,
            "expires_at": key_data.expires_at,
            "is_active": True
        }

        api_key_info = getattr(request.state, "api_key_info", None)

        # Default user_id from JWT/API key info if not provided
        if not create_data.get("user_id") and api_key_info and api_key_info.get("user_id"):
            create_data["user_id"] = api_key_info["user_id"]

        if not api_key_info:
            if not create_data.get("user_id"):
                raise HTTPException(status_code=403, detail="Unable to determine caller identity: user_id is required")

        if api_key_info and api_key_info.get("user_role") != "admin":
            # Force user_id to be the caller's user_id for non-admins
            caller_user_id = int(api_key_info.get("user_id")) if api_key_info.get("user_id") else None
            if not caller_user_id:
                raise HTTPException(status_code=403, detail="Insufficient permissions to create API keys without a valid API key owner")
            if create_data.get("user_id"):
                if int(create_data.get("user_id")) != caller_user_id:
                    raise HTTPException(status_code=403, detail="Insufficient permissions to create an API key for another user")
            else:
                create_data["user_id"] = caller_user_id

        # Audit logging: record who requested the key and from which IP
        origin_ip = None
        if request.client:
            origin_ip = request.client.host
        origin_user_agent = request.headers.get("user-agent")
        logger.info(f"API key create requested by: {api_key_info.get('user_email') if api_key_info else 'unknown'}, ip={origin_ip}, ua={origin_user_agent}, target_user={create_data.get('user_id')}" )

        result = await api_key_service.create_api_key(create_data, requester_info=getattr(request.state, "api_key_info", None))
        
        return ApiKeyInfo(
            id=result["key_id"],
            name=result["name"],
            key=result["key"],  # Full key is returned only on creation
            user_id=result["user_id"],
            user_email=result["user_email"],
            is_active=result["is_active"],
            created_at=datetime.fromisoformat(result["created_at"]),
            last_used=datetime.fromisoformat(result["last_used"]) if result["last_used"] else None,
            expires_at=datetime.fromisoformat(result["expires_at"]) if result["expires_at"] else None,
            usage_count=result["usage_count"],
            rate_limit=result["rate_limit"],
            permissions=result["permissions"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )

@router.put("/api-keys/{key_id}", response_model=ApiKeyInfo)
async def update_api_key(
    key_id: str,
    key_data: CreateApiKeyRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update an API key."""
    try:
        update_data = {
            "name": key_data.name,
            "rate_limit": key_data.rate_limit,
            "expires_at": key_data.expires_at,
            "is_active": True  # Default to active for updates
        }
        
        # Enforce that non-admins can only update their own API keys
        api_key_info = getattr(request.state, "api_key_info", None)
        if api_key_info and api_key_info.get("user_role") != "admin":
            # Lookup target key owner
            target_key = await api_key_service.get_api_key(key_id)
            if not target_key:
                raise HTTPException(status_code=404, detail="API key not found")
            if int(target_key["user_id"]) != int(api_key_info.get("user_id")):
                raise HTTPException(status_code=403, detail="Insufficient permissions to update this API key")

        result = await api_key_service.update_api_key(key_id, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return ApiKeyInfo(
            id=result["key_id"],
            name=result["name"],
            key=result["key"],  # Masked key
            user_id=result["user_id"],
            user_email=result["user_email"],
            is_active=result["is_active"],
            created_at=datetime.fromisoformat(result["created_at"]),
            last_used=datetime.fromisoformat(result["last_used"]) if result["last_used"] else None,
            expires_at=datetime.fromisoformat(result["expires_at"]) if result["expires_at"] else None,
            usage_count=result["usage_count"],
            rate_limit=result["rate_limit"],
            permissions=result["permissions"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update API key {key_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update API key: {str(e)}"
        )

@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete an API key."""
    try:
        # Enforce that non-admins can only delete their own API keys
        api_key_info = getattr(request.state, "api_key_info", None)
        if api_key_info and api_key_info.get("user_role") != "admin":
            target_key = await api_key_service.get_api_key(key_id)
            if not target_key:
                raise HTTPException(status_code=404, detail="API key not found")
            if int(target_key["user_id"]) != int(api_key_info.get("user_id")):
                raise HTTPException(status_code=403, detail="Insufficient permissions to delete this API key")

        success = await api_key_service.delete_api_key(key_id)
        if not success:
            raise HTTPException(status_code=404, detail="API key not found")
        return {"message": f"API key {key_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete API key {key_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key"
        )

@router.get("/settings", response_model=SystemSettings)
async def get_system_settings(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current system settings with fallback to defaults."""
    default_settings = SystemSettings(
        auto_refresh=True,
        email_notifications=True,
        api_logging=True,
        max_concurrent_jobs=5,
        default_video_resolution="1080x1920",
        storage_retention_days=90
    )
    
    try:
        settings_data = await settings_service.get_all_settings()
        
        # Build settings from database data, using defaults for missing keys
        settings = SystemSettings(
            auto_refresh=settings_data.get("auto_refresh", default_settings.auto_refresh),
            email_notifications=settings_data.get("email_notifications", default_settings.email_notifications),
            api_logging=settings_data.get("api_logging", default_settings.api_logging),
            max_concurrent_jobs=settings_data.get("max_concurrent_jobs", default_settings.max_concurrent_jobs),
            default_video_resolution=settings_data.get("default_video_resolution", default_settings.default_video_resolution),
            storage_retention_days=settings_data.get("storage_retention_days", default_settings.storage_retention_days)
        )
        logger.info(f"Settings loaded from database: {settings.model_dump()}")
        return settings
    except Exception as e:
        logger.warning(f"Failed to get settings from database, using defaults: {e}")
        # Return default settings as fallback - this is normal behavior if settings table is empty
        return default_settings

@router.put("/settings", response_model=SystemSettings)
async def update_system_settings(
    settings: SystemSettings,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update system settings."""
    try:
        # Convert Pydantic model to dict
        settings_dict = {
            "auto_refresh": settings.auto_refresh,
            "email_notifications": settings.email_notifications,
            "api_logging": settings.api_logging,
            "max_concurrent_jobs": settings.max_concurrent_jobs,
            "default_video_resolution": settings.default_video_resolution,
            "storage_retention_days": settings.storage_retention_days
        }
        
        # Update settings in database
        success = await settings_service.update_settings(settings_dict, updated_by="admin")
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save settings to database"
            )
        
        logger.info(f"Successfully updated system settings: {settings_dict}")
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings"
        )

@router.get("/system-info")
async def get_system_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get system information and health status."""
    try:
        system_info = await settings_service.get_system_info()
        return system_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system information"
        )


# Email Testing Endpoint

class SendTestEmailRequest(BaseModel):
    recipient_email: str
    subject: Optional[str] = "Test Email from Griot"
    message: Optional[str] = "This is a test email from your Griot dashboard."


class SendTestEmailResponse(BaseModel):
    success: bool
    message: str
    email_id: Optional[str] = None


@router.post("/send-test-email", response_model=SendTestEmailResponse)
async def send_test_email(
    request: SendTestEmailRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Send a test email using the configured Resend email service.
    
    This endpoint allows administrators to test the email functionality
    by sending a test email to a specified recipient.
    """
    from app.utils.email import send_verification_email, RESEND_AVAILABLE, RESEND_API_KEY
    import resend
    
    # Check if Resend is configured
    if not RESEND_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Email service is not available. Please install the resend package."
        )
    
    if not RESEND_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Email service is not configured. Please set RESEND_API_KEY environment variable."
        )
    
    try:
        # Initialize Resend
        from app.utils.email import initialize_resend, EMAIL_FROM_ADDRESS, EMAIL_FROM_NAME
        initialize_resend()
        
        # Create HTML email
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        color: #333;
                        line-height: 1.6;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .header h1 {{
                        color: #2563eb;
                        margin: 0;
                    }}
                    .content {{
                        background: #f9fafb;
                        padding: 20px;
                        border-radius: 8px;
                        margin: 20px 0;
                    }}
                    .footer {{
                        font-size: 12px;
                        color: #6b7280;
                        text-align: center;
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #e5e7eb;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Test Email from {EMAIL_FROM_NAME}</h1>
                    </div>
                    
                    <div class="content">
                        <p><strong>Subject:</strong> {request.subject}</p>
                        <p><strong>Message:</strong></p>
                        <p>{request.message}</p>
                        
                        <p style="margin-top: 30px; font-size: 14px; color: #059669;">
                            ✅ If you received this email, your email service is working correctly!
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>This is a test email sent from your Griot dashboard.</p>
                        <p>© 2024 {EMAIL_FROM_NAME}. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # Send email using Resend
        email_response = resend.Emails.send({
            "from": f"{EMAIL_FROM_NAME} <{EMAIL_FROM_ADDRESS}>",
            "to": request.recipient_email,
            "subject": request.subject,
            "html": html_content,
        })
        
        if email_response.get("id"):
            logger.info(f"✅ Test email sent to {request.recipient_email} (ID: {email_response.get('id')})")
            return SendTestEmailResponse(
                success=True,
                message=f"Test email sent successfully to {request.recipient_email}",
                email_id=email_response.get("id")
            )
        else:
            logger.error(f"❌ Failed to send test email: {email_response}")
            raise HTTPException(
                status_code=500,
                detail="Failed to send test email"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send test email: {str(e)}"
        )


# ── Configurable Settings (env overrides) ─────────────────────────

@router.get("/settings/config")
async def get_config_settings(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Return all configurable settings grouped by category.

    Passwords are masked in responses.  Admin only.
    Refreshes os.environ from DB first so multi-worker deployments
    always show the latest saved values.
    """
    await settings_service.load_config_overrides()
    from app.services.settings.config_registry import get_current_config
    return get_current_config()


class UpdateConfigRequest(BaseModel):
    settings: Dict[str, Any]


@router.put("/settings/config")
async def update_config_settings(
    body: UpdateConfigRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Save config overrides.

    Values are written to the system_settings table AND applied to
    ``os.environ`` so they take effect immediately (single-worker) or
    after the next restart (multi-worker).
    """
    from app.services.settings.config_registry import (
        apply_config_values,
        CONFIGURABLE_SETTINGS,
    )

    values = body.settings
    if not values:
        raise HTTPException(status_code=400, detail="No settings provided")

    # Apply to os.environ
    updated_keys = apply_config_values(values)

    # Persist to DB so values survive restarts
    for key in updated_keys:
        meta = CONFIGURABLE_SETTINGS[key]
        val = os.getenv(key, "")
        await settings_service.set_setting(
            f"config:{key}",
            val,
            data_type="string",
            updated_by="admin",
        )

    logger.info(f"Config settings updated: {updated_keys}")
    return {"updated": updated_keys, "count": len(updated_keys)}