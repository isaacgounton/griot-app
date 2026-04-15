"""
Routes for extracting frames from videos.
"""
import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.services.job_queue import job_queue
from app.models import JobType, JobResponse, VideoFramesRequest
from app.services.video.frames_service import video_frames_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/frames", tags=["Video"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_frames_job(request: VideoFramesRequest):
    """Extract frames from a video at a specified interval, with configurable format and quality."""
    try:
        video_url = str(request.video_url)

        valid_formats = ["jpg", "png", "webp"]
        if request.format not in valid_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid format. Supported formats: {', '.join(valid_formats)}"
            )

        if request.max_frames and request.max_frames > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum frames cannot exceed 1000"
            )

        job_id = str(uuid.uuid4())
        job_params = {
            "video_url": video_url,
            "interval": request.interval,
            "format": request.format,
            "quality": request.quality,
            "max_frames": request.max_frames
        }

        async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
            return await video_frames_service.process_frames_job(_job_id, data)

        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.VIDEO_FRAMES,
            process_func=process_wrapper,
            data=job_params
        )

        logger.info(f"Created video frames job {job_id} for video: {video_url}")

        return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating video frames job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create video frames job"
        )
