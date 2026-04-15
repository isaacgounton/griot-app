import uuid
from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from app.models import JobResponse, JobType, AiimageToVideoRequest
from app.services.job_queue import job_queue
from app.services.video_pipeline import process as video_pipeline_process
from app.utils.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Content"])


async def process_aiimage_to_video_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Wrapper function for aiimage-to-video pipeline job processing."""
    # Set the media strategy to AI images for this route
    data['footage_provider'] = 'ai_generated'
    data['media_type'] = 'image'
    return await video_pipeline_process(data)


@router.post("/aiimage-to-video", response_model=JobResponse)
async def generate_video_from_script_with_ai_images(
    request: AiimageToVideoRequest,
    _: dict[str, Any] = Depends(get_current_user)
):
    """Generate a video from a topic using AI-generated images instead of stock footage."""
    job_id = str(uuid.uuid4())
    
    try:
        # Validate input: either topic provided or auto_topic enabled
        if not request.auto_topic and not request.topic:
            raise HTTPException(
                status_code=400, 
                detail="Either 'topic' must be provided or 'auto_topic' must be set to true"
            )
        
        # Prepare data for job processing
        # Note: Service validation will be done during job processing to avoid timeouts
        job_data = request.model_dump()
        
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.AIIMAGE_TO_VIDEO,
            process_func=process_aiimage_to_video_wrapper,
            data=job_data
        )
        
        return JobResponse(job_id=job_id)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create aiimage-to-video job: {str(e)}")