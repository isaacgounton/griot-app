"""
Routes for video concatenation operations.
"""
import logging
import uuid

from fastapi import APIRouter, HTTPException, status

from app.utils.media import SUPPORTED_VIDEO_FORMATS
from app.services.job_queue import job_queue
from app.models import JobType, JobResponse, VideoConcatenateRequest
from app.services.video.concatenate import concatenation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/merge", tags=["Video"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_concatenate_job(request: VideoConcatenateRequest):
    """Concatenate multiple videos into one with optional transition effects (fade, dissolve, slide, wipe)."""
    if not request.video_urls:
        raise HTTPException(status_code=400, detail="No video URLs provided")

    if len(request.video_urls) < 2:
        raise HTTPException(status_code=400, detail="At least 2 video URLs are required for concatenation")

    valid_transitions = ["none", "fade", "dissolve", "slide", "wipe"]
    if request.transition not in valid_transitions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition effect. Supported transitions: {', '.join(valid_transitions)}"
        )

    output_format = request.output_format.lower()
    if not output_format.startswith('.'):
        output_format = f".{output_format}"

    if output_format not in SUPPORTED_VIDEO_FORMATS:
        valid_formats = [f[1:] for f in SUPPORTED_VIDEO_FORMATS]
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported output format. Supported formats: {', '.join(valid_formats)}"
        )

    job_data = {
        "video_urls": request.video_urls,
        "output_format": output_format,
        "transition": request.transition,
        "transition_duration": request.transition_duration,
        "max_segment_duration": request.max_segment_duration,
        "total_duration_limit": request.total_duration_limit
    }

    job_id = str(uuid.uuid4())

    try:
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.VIDEO_CONCATENATION,
            process_func=concatenation_service.process_job,
            data=job_data
        )

        logger.info(f"Created video concatenation job: {job_id}")

        return JobResponse(job_id=job_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create concatenation job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create concatenation job: {str(e)}"
        )
