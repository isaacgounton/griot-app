"""
Routes for extracting video clips from videos.
"""
import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.services.job_queue import job_queue
from app.models import JobType, JobResponse, VideoClipsRequest

from app.services.video.clips_service import video_clips_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clips", tags=["Video"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_clips_job(request: VideoClipsRequest):
    """Extract video clips using manual time segments or AI-powered content search."""
    try:
        video_url = str(request.video_url)

        if not request.segments and not request.ai_query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'segments' or 'ai_query' must be provided"
            )

        if request.segments and request.ai_query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot use both 'segments' and 'ai_query' simultaneously"
            )

        if request.segments:
            for i, segment in enumerate(request.segments):
                if segment.start < 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Segment {i}: Start time cannot be negative"
                    )
                if segment.end <= segment.start:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Segment {i}: End time must be greater than start time"
                    )
                if segment.end - segment.start > 600:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Segment {i}: Clip duration cannot exceed 10 minutes"
                    )

        if request.ai_query:
            if len(request.ai_query.strip()) < 3:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="AI query must be at least 3 characters long"
                )
            if len(request.ai_query) > 500:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="AI query cannot exceed 500 characters"
                )

        valid_formats = ["mp4", "webm", "avi", "mov", "mkv"]
        if request.output_format not in valid_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid output format. Supported formats: {', '.join(valid_formats)}"
            )

        valid_qualities = ["low", "medium", "high"]
        if request.quality and request.quality not in valid_qualities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid quality. Supported qualities: {', '.join(valid_qualities)}"
            )

        job_id = str(uuid.uuid4())
        job_params: dict[str, Any] = {
            "video_url": video_url,
            "output_format": request.output_format,
            "quality": request.quality or "medium"
        }

        if request.segments:
            job_params["segments"] = [
                {
                    "start": segment.start,
                    "end": segment.end,
                    "name": segment.name
                }
                for segment in request.segments
            ]
        else:
            job_params["ai_query"] = request.ai_query.strip()
            job_params["max_clips"] = request.max_clips

        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.VIDEO_CLIPS,
            process_func=video_clips_service.process_clips_job,
            data=job_params
        )

        logger.info(f"Created video clips job {job_id} for video: {video_url}")

        return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating video clips job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create video clips job"
        )
