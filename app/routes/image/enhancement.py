"""
Routes for image enhancement and artifact removal operations.
"""
import uuid
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from app.models import (
    ImageEnhancementRequest,
    JobResponse,
    JobType,
)
from app.services.job_queue import job_queue
from app.services.image.enhancement_service import image_enhancement_service
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["Images"])


@router.post("/enhance", response_model=JobResponse)
async def create_image_enhancement_job(
    request: ImageEnhancementRequest,
    _: dict[str, Any] = Depends(get_current_user),
):
    """Enhance an image by removing AI artifacts and adding natural imperfections like film grain and vintage effects."""
    try:
        # Create parameters dictionary
        params = {
            "image_url": str(request.image_url),
            "enhance_color": request.enhance_color,
            "enhance_contrast": request.enhance_contrast,
            "noise_strength": request.noise_strength,
            "remove_artifacts": request.remove_artifacts,
            "add_film_grain": request.add_film_grain,
            "vintage_effect": request.vintage_effect,
            "output_format": request.output_format,
            "output_quality": request.output_quality
        }
        
        # Create and start the job using new job queue
        job_id = str(uuid.uuid4())
        
        # Create a wrapper function that matches the expected signature
        async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
            return await image_enhancement_service.enhance_image(data)
        
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.IMAGE_ENHANCEMENT,
            process_func=process_wrapper,
            data=params
        )
        
        logger.info(f"Created image enhancement job: {job_id}")
        
        return JobResponse(job_id=job_id)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")