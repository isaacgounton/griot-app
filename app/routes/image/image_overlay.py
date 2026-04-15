"""
Routes for image overlay operations.
"""
import uuid
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from app.models import (
    ImageOverlayRequest,
    JobResponse,
    JobType,
)
from app.services.job_queue import job_queue
from app.services.image.image_overlay import image_overlay_service
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["Images"])


@router.post("/edit", response_model=JobResponse)
async def create_image_edit_job(
    request: ImageOverlayRequest,
    _: dict[str, Any] = Depends(get_current_user),
):
    """Overlay one or more images onto a base image with positioning, rotation, and opacity control."""
    try:
        # Convert overlay_images to a list of dictionaries
        overlay_images = []
        for overlay in request.overlay_images:
            # Convert Pydantic model to dictionary
            overlay_dict = overlay.model_dump(exclude_none=True)
            # Ensure URL is a string
            overlay_dict["url"] = str(overlay_dict["url"])
            overlay_images.append(overlay_dict)
            
        # Create parameters dictionary
        params = {
            "base_image_url": str(request.base_image_url),
            "overlay_images": overlay_images,
            "output_format": request.output_format,
            "output_quality": request.output_quality,
            "maintain_aspect_ratio": request.maintain_aspect_ratio
        }
        
        # Add optional output dimensions if provided
        if request.output_width:
            params["output_width"] = request.output_width
        if request.output_height:
            params["output_height"] = request.output_height
        
        # Create and start the job using new job queue
        job_id = str(uuid.uuid4())
        
        # Create a wrapper function that matches the expected signature
        async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
            return await image_overlay_service.overlay_images(data)
        
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.IMAGE_OVERLAY,
            process_func=process_wrapper,
            data=params
        )
        
        logger.info(f"Created image overlay job: {job_id}")
        
        return JobResponse(job_id=job_id)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 