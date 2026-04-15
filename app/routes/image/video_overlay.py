"""
Routes for video overlay operations.
"""
import uuid
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from app.models import (
    VideoOverlayRequest,
    JobResponse,
    JobType,
)
from app.services.job_queue import job_queue
from app.services.image.video_overlay import video_overlay_service
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/videos", tags=["Images"])


@router.post("/edit", response_model=JobResponse)
async def create_video_edit_job(
    request: VideoOverlayRequest,
    _: dict[str, Any] = Depends(get_current_user),
):
    """Overlay one or more videos onto a base image with positioning, timing, and audio mixing control."""
    try:
        # Convert overlay_videos to a list of dictionaries
        overlay_videos = []
        for overlay in request.overlay_videos:
            # Convert Pydantic model to dictionary
            overlay_dict = overlay.model_dump(exclude_none=True)
            # Ensure URL is a string
            overlay_dict["url"] = str(overlay_dict["url"])
            overlay_videos.append(overlay_dict)
            
        # Create parameters dictionary
        params = {
            "base_image_url": str(request.base_image_url),
            "overlay_videos": overlay_videos,
            "frame_rate": request.frame_rate,
            "maintain_aspect_ratio": request.maintain_aspect_ratio
        }
        
        # Add optional parameters if provided
        if request.output_duration:
            params["output_duration"] = request.output_duration
        if request.output_width:
            params["output_width"] = request.output_width
        if request.output_height:
            params["output_height"] = request.output_height
        if request.background_audio_url:
            params["background_audio_url"] = str(request.background_audio_url)
            params["background_audio_volume"] = request.background_audio_volume
        
        # Create and start the job using new job queue
        job_id = str(uuid.uuid4())
        
        # Create a wrapper function that matches the expected signature
        async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
            return await video_overlay_service.overlay_videos(data)
        
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.VIDEO_OVERLAY,
            process_func=process_wrapper,
            data=params
        )
        
        logger.info(f"Created video overlay job: {job_id}")
        
        return JobResponse(job_id=job_id)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 