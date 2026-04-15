"""
Routes for generating video thumbnails.
"""
import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.services.job_queue import job_queue
from app.models import JobType, JobResponse, VideoThumbnailsRequest
from app.services.video.thumbnails_service import video_thumbnails_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/thumbnails", tags=["Video"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_thumbnails_job(request: VideoThumbnailsRequest):
    """Generate thumbnails from a video at specified timestamps or evenly distributed intervals."""
    try:
        video_url = str(request.video_url)

        valid_formats = ["jpg", "png", "webp"]
        if request.format not in valid_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid format. Supported formats: {', '.join(valid_formats)}"
            )

        if request.timestamps:
            for i, ts in enumerate(request.timestamps):
                if ts < 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Timestamp at index {i} cannot be negative"
                    )

            if len(request.timestamps) != request.count:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Number of timestamps must match the count parameter"
                )

        job_id = str(uuid.uuid4())
        job_params = {
            "video_url": video_url,
            "timestamps": request.timestamps,
            "count": request.count,
            "format": request.format,
            "quality": request.quality
        }

        async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
            return await video_thumbnails_service.process_thumbnails_job(_job_id, data)

        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.VIDEO_THUMBNAILS,
            process_func=process_wrapper,
            data=job_params
        )

        logger.info(f"Created video thumbnails job {job_id} for video: {video_url}")

        return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating video thumbnails job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create video thumbnails job"
        )
