from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import logging
import uuid

from app.services.job_queue import job_queue
from app.models import JobType
from app.services.simone.simone_service import SimoneService
from app.models import JobResponse
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/simone", tags=["Content Tools"])

simone_service = SimoneService()


class SimoneVideoRequest(BaseModel):
    url: str = Field(..., description="Video URL to process")
    platform: str | None = Field(None, description="Social media platform for post generation")
    cookies_content: str | None = Field(None, description="Cookie content for authentication")
    cookies_url: str | None = Field(None, description="Cookie URL for authentication")


class SimoneEnhancedRequest(BaseModel):
    url: str = Field(..., description="Video URL to process")
    include_topics: bool = Field(True, description="Include topic identification")
    include_x_thread: bool = Field(True, description="Include X thread generation")
    platforms: list[str] = Field(default=["x", "linkedin", "instagram"], description="Social media platforms")
    thread_config: dict[str, Any] = Field(
        default={
            "max_posts": 8,
            "character_limit": 280,
            "thread_style": "viral"
        },
        description="Thread configuration"
    )
    cookies_content: str | None = Field(None, description="Cookie content for authentication")
    cookies_url: str | None = Field(None, description="Cookie URL for authentication")


@router.post("/video-to-blog", response_model=JobResponse)
async def create_video_to_blog_job(
    request: SimoneVideoRequest,
    current_user: dict[str, Any] = Depends(get_current_user)
):
    """Process a video into a blog post with screenshots and optional social media posts."""
    try:
        # Create job parameters
        job_params = request.model_dump()
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create wrapper function that matches job queue signature
        async def process_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
            return await simone_service.process_video_to_blog(data)
        
        # Add job to queue
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.SIMONE_VIDEO_TO_BLOG,
            process_func=process_wrapper,
            data=job_params
        )
        
        logger.info(f"Created video-to-blog job {job_id} for URL: {request.url}")
        
        return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating video-to-blog job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.post("/viral-content", response_model=JobResponse)
async def create_viral_content_job(
    request: SimoneEnhancedRequest,
    current_user: dict[str, Any] = Depends(get_current_user)
):
    """Generate viral content from a video: topics, X threads, multi-platform posts, and blog."""
    try:
        # Create job parameters
        job_params = request.model_dump()
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create wrapper function that matches job queue signature
        async def process_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
            return await simone_service.process_video_with_enhanced_features(data)
        
        # Add job to queue
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.SIMONE_ENHANCED_PROCESSING,
            process_func=process_wrapper,
            data=job_params
        )
        
        logger.info(f"Created viral content job {job_id} for URL: {request.url}")
        
        return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating viral content job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")