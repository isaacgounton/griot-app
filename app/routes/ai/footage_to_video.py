import uuid
import logging
from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from app.models import JobResponse, JobType, FootageToVideoRequest
from app.services.job_queue import job_queue
from app.services.video_pipeline import process as video_pipeline_process
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Content"])


async def process_unified_video_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Wrapper function for video pipeline job processing."""
    return await video_pipeline_process(data)


@router.post("/footage-to-video", response_model=JobResponse)
async def generate_video_from_footage(
    request: FootageToVideoRequest,
    _: dict[str, Any] = Depends(get_current_user)
):
    """Generate a complete video from a topic using the end-to-end AI pipeline (script, TTS, visuals, captions)."""
    return await process_footage_to_video_request(request)


async def process_footage_to_video_request(request: FootageToVideoRequest) -> JobResponse:
    """Process a validated footage-to-video request."""
    job_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Topic-to-video request received: {request.model_dump()}")
        
        # Validate input: either topic provided or auto_topic enabled or custom_script provided
        if not request.auto_topic and not request.topic and not request.custom_script:
            raise HTTPException(
                status_code=400,
                detail="Either 'topic' must be provided or 'auto_topic' must be set to true or 'custom_script' must be provided"
            )
        
        # Prepare data for job processing
        # Note: Auto-topic discovery will be done during job processing to avoid timeouts
        job_data = request.model_dump()
        
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.FOOTAGE_TO_VIDEO,
            process_func=process_unified_video_wrapper,
            data=job_data
        )
        
        return JobResponse(job_id=job_id)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create footage-to-video job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create footage-to-video job: {str(e)}")