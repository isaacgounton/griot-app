"""
Routes for image to video conversion.
"""
import uuid
import logging
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models import (
    ImageToVideoRequest,
    JobType
)
from app.services.job_queue import job_queue
from app.services.image.image_to_video import image_to_video_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/videos", tags=["Images"])


class ImageToVideoResponse(BaseModel):
    """Union response model for image to video generations (sync or async)."""
    # For async mode
    job_id: str | None = None
    # For sync mode
    final_video_url: str | None = None
    srt_url: str | None = None
    duration_seconds: float | None = None
    processing_time_seconds: float | None = None


@router.post("/generations", response_model=ImageToVideoResponse)
async def create_video_generation_job(request: ImageToVideoRequest):
    """Convert an image to video with Ken Burns effects, optional narration, background music, and captions."""
    try:
        # Validate match_length parameter
        if request.match_length not in ["audio", "video"]:
            raise ValueError("match_length must be either 'audio' or 'video'")
        
        # Create a new job with all the parameters
        params = {
            "image_url": str(request.image_url),
            "video_length": request.video_length,
            "frame_rate": request.frame_rate,
            "zoom_speed": request.zoom_speed,
            "match_length": request.match_length,
            "narrator_vol": request.narrator_vol,
            "should_add_captions": request.should_add_captions,
            "effect_type": request.effect_type,
            "pan_direction": request.pan_direction,
            "ken_burns_keypoints": request.ken_burns_keypoints
        }
        
        # Add optional narrator audio parameters if provided
        if request.narrator_speech_text:
            params["narrator_speech_text"] = request.narrator_speech_text
            params["voice"] = request.voice
            params["provider"] = request.provider
        elif request.narrator_audio_url:
            params["narrator_audio_url"] = str(request.narrator_audio_url)
        
        # Add optional background music parameters if provided
        if request.background_music_url:
            params["background_music_url"] = str(request.background_music_url)
            params["background_music_vol"] = request.background_music_vol
        
        if request.caption_properties:
            params["caption_properties"] = request.caption_properties.model_dump(
                exclude_none=True  # Only include non-None values
            )
        
        # Add caption language for transcription
        if request.caption_language:
            params["caption_language"] = request.caption_language
        
        # Create and start the job using new job queue
        job_id = str(uuid.uuid4())
        
        # Create a wrapper function that matches the expected signature
        async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
            return await image_to_video_service.image_to_video(data)
        
        # Handle synchronous mode
        if request.sync:
            # Process the job directly and return result
            result = await process_wrapper(job_id, params)
            
            return ImageToVideoResponse(
                final_video_url=result.get("final_video_url"),
                srt_url=result.get("srt_url"),
                duration_seconds=result.get("video_duration"),
                processing_time_seconds=result.get("processing_time_seconds", 0.0)
            )
        
        # Handle asynchronous mode (default)
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.IMAGE_TO_VIDEO,
            process_func=process_wrapper,
            data=params
        )
        
        logger.info(f"Created image-to-video job: {job_id}")
        
        return ImageToVideoResponse(job_id=job_id)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if request.sync:
            raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to create video generation job: {str(e)}") 