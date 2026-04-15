"""
Routes for advanced video generation with TTS and captions.
"""
import logging
import uuid
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.services.job_queue import job_queue
from app.models import JobType, JobResponse
from app.services.video.video_builder_service import video_builder_service
from app.services.video.colorkey_overlay_service import colorkey_overlay_service
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advanced", tags=["Video"])


class TTSCaptionedVideoRequest(BaseModel):
    """Request model for TTS-captioned video generation."""
    background_url: str = Field(..., description="URL of the background image")
    text: Optional[str] = Field(None, description="Text to generate video from")
    width: int = Field(1080, description="Video width in pixels")
    height: int = Field(1920, description="Video height in pixels")
    audio_url: Optional[str] = Field(None, description="Audio URL (optional, alternative to text)")

    tts_provider: str = Field("kokoro", description="TTS provider: kokoro, piper, edge, kitten")
    voice: str = Field("af_heart", description="Voice name (provider-specific)")
    speed: float = Field(1.0, description="Speech speed")
    volume_multiplier: float = Field(1.0, description="Volume multiplier")

    caption_font_size: int = Field(120, description="Font size for captions")
    caption_font_color: str = Field("#ffffff", description="Font color for captions")
    caption_shadow_color: str = Field("#000000", description="Shadow color for captions")
    caption_stroke_color: str = Field("#000000", description="Stroke color for captions")
    caption_position: str = Field("bottom", description="Caption position: top, center, bottom")

    image_effect: str = Field("ken_burns", description="Background effect: ken_burns, pan, none")


class VideoEditRequest(BaseModel):
    """Request model for video editing and overlay operations."""
    base_image_url: str = Field(..., description="Base image URL to use as background")
    overlay_videos: list[Dict[str, Any]] = Field(..., description="List of overlay video configurations")
    output_duration: Optional[float] = Field(None, description="Output duration in seconds")
    frame_rate: int = Field(30, description="Frame rate")
    output_width: Optional[int] = Field(None, description="Output video width")
    output_height: Optional[int] = Field(None, description="Output video height")
    maintain_aspect_ratio: bool = Field(True, description="Maintain aspect ratio")


@router.post("", response_model=JobResponse)
async def create_video_edit_job(
    request: VideoEditRequest,
    _: Dict[str, Any] = Depends(get_current_user)
):
    """Overlay multiple videos on a base image with position, size, timing, and colorkey controls."""
    try:
        if not request.base_image_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Base image URL is required"
            )

        if not request.overlay_videos or len(request.overlay_videos) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one overlay video is required"
            )

        job_data = {
            "base_image_url": str(request.base_image_url),
            "overlay_videos": request.overlay_videos,
            "output_duration": request.output_duration,
            "frame_rate": request.frame_rate,
            "output_width": request.output_width,
            "output_height": request.output_height,
            "maintain_aspect_ratio": request.maintain_aspect_ratio,
        }

        job_id = str(uuid.uuid4())

        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.VIDEO_OVERLAY,
            process_func=colorkey_overlay_service.process_colorkey_overlay_job,
            data=job_data
        )

        return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating video edit job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create video edit job"
        )


@router.post("/tts-captioned-video")
async def create_tts_captioned_video(
    request: TTSCaptionedVideoRequest,
    _: Dict[str, Any] = Depends(get_current_user)
):
    """Generate a video with TTS audio and synchronized captions from a background image and text. Always async."""
    try:
        if not request.background_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Background URL is required"
            )

        if not request.text and not request.audio_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either text for TTS or audio_url must be provided"
            )

        job_data = {
            "background_url": str(request.background_url),
            "text": request.text,
            "dimensions": (request.width, request.height),
            "audio_url": request.audio_url,
            "tts_provider": request.tts_provider,
            "voice": request.voice,
            "speed": request.speed,
            "volume_multiplier": request.volume_multiplier,
            "caption_config": {
                "font_size": request.caption_font_size,
                "font_color": request.caption_font_color,
                "shadow_color": request.caption_shadow_color,
                "stroke_color": request.caption_stroke_color,
                "position": request.caption_position,
            },
            "image_effect": request.image_effect,
        }

        job_id = str(uuid.uuid4())

        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.VIDEO_ADD_CAPTIONS,
            process_func=video_builder_service.process_tts_captioned_video_job,
            data=job_data
        )

        return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating TTS-captioned video job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create video generation job"
        )


class ColorkeyOverlayRequest(BaseModel):
    """Request model for colorkey overlay (green screen) effects."""
    video_url: str = Field(..., description="URL of the main video")
    overlay_video_url: str = Field(..., description="URL of the overlay video")
    color: str = Field("green", description="Color to key out: green, blue, red, etc.")
    similarity: float = Field(0.3, description="Similarity threshold 0-1")
    blend: float = Field(0.1, description="Blend amount 0-1")
    sync: bool = Field(False, description="Process synchronously")


@router.post("/colorkey-overlay")
async def create_colorkey_overlay(
    request: ColorkeyOverlayRequest,
    _: Dict[str, Any] = Depends(get_current_user)
):
    """Apply colorkey (green screen) overlay, compositing one video on top of another."""
    try:
        if not request.video_url or not request.overlay_video_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both video_url and overlay_video_url are required"
            )

        job_data = {
            "video_url": str(request.video_url),
            "overlay_video_url": str(request.overlay_video_url),
            "color": request.color,
            "similarity": request.similarity,
            "blend": request.blend,
        }

        job_id = str(uuid.uuid4())

        if request.sync:
            result = await colorkey_overlay_service.process_colorkey_overlay_job(job_id, job_data)
            return result
        else:
            await job_queue.add_job(
                job_id=job_id,
                job_type=JobType.VIDEO_OVERLAY,
                process_func=colorkey_overlay_service.process_colorkey_overlay_job,
                data=job_data
            )

            return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating colorkey overlay job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create overlay job"
        )
