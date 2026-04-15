"""Scenes-to-video route for creating videos from scene-based input."""

import uuid
import logging
from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from app.models import JobResponse, JobType
from app.services.job_queue import job_queue
from app.services.ai.scenes_video_service import ScenesVideoService
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Content"])

# Initialize service
scenes_video_service = ScenesVideoService()


class VideoScene(BaseModel):
    """Individual scene definition."""
    text: str = Field(
        description="Narration text for this scene"
    )
    searchTerms: list[str] = Field(
        default=[],
        description="Search terms for background video/image"
    )
    duration: float = Field(
        default=3.0,
        ge=1.0,
        le=30.0,
        description="Scene duration in seconds"
    )

    @field_validator('text')
    @classmethod
    def truncate_text(cls, v: str) -> str:
        if v and len(v) > 2000:
            return v[:2000]
        return v


class SceneConfig(BaseModel):
    """Configuration for scenes-to-video generation."""
    voice: str = Field(default="af_heart", description="Voice for TTS")
    provider: str = Field(default="kokoro", description="TTS provider")
    ttsSpeed: float = Field(default=1.0, description="TTS speed multiplier")
    enable_voice_over: bool = Field(default=True, description="Enable voice-over narration")
    enable_built_in_audio: bool = Field(default=False, description="Enable built-in audio from AI video models")
    music: str = Field(default="chill", description="Background music style")
    musicVolume: str = Field(default="medium", description="Music volume: low, medium, high")
    captionPosition: str = Field(default="bottom", description="Caption position")
    captionStyle: str = Field(default="viral_bounce", description="Caption style preset")
    captionColor: str | None = Field(default=None, description="Caption color override")
    highlightColor: str | None = Field(default=None, description="Highlighted word color override")
    enableCaptions: bool = Field(default=True, description="Enable captions")
    fontSize: int | None = Field(default=None, description="Font size in pixels")
    fontFamily: str | None = Field(default=None, description="Font family name")
    wordsPerLine: int | None = Field(default=None, description="Max words per caption line")
    marginV: int | None = Field(default=None, description="Vertical margin in pixels")
    outlineWidth: int | None = Field(default=None, description="Outline width in pixels")
    allCaps: bool | None = Field(default=None, description="Convert text to uppercase")
    orientation: str = Field(default="portrait", description="Video orientation")
    resolution: str = Field(default="1080x1920", description="Video resolution")
    language: str = Field(default="en", description="Language code")
    footageProvider: str = Field(default="pexels", description="Stock footage provider")
    footageQuality: str = Field(default="high", description="Footage quality")
    searchSafety: str = Field(default="moderate", description="Search safety level")
    mediaType: str = Field(default="video", description="Media type: video or image")
    aiVideoProvider: str = Field(default="wavespeed", description="AI video provider")
    aiImageProvider: str = Field(default="together", description="AI image provider")
    aiImageModel: str | None = Field(default=None, description="AI image model to use")
    aiVideoModel: str | None = Field(default=None, description="AI video model to use")
    # Image-to-video motion settings
    effect_type: str = Field(default="ken_burns", description="Motion effect: ken_burns, zoom, pan, fade")
    zoom_speed: float = Field(default=10.0, description="Zoom speed (1-100)")
    pan_direction: str = Field(default="left_to_right", description="Pan direction")
    ken_burns_keypoints: list[dict] | None = Field(default=None, description="Ken Burns keypoints")
    paddingBack: int = Field(default=1500, description="Padding at end in ms")


class ScenesToVideoRequest(BaseModel):
    """Request model for scenes-to-video generation."""
    scenes: list[VideoScene] = Field(
        description="List of scenes to create video from"
    )
    config: SceneConfig = Field(
        default_factory=SceneConfig,
        description="Video generation configuration"
    )

    @field_validator('scenes')
    @classmethod
    def validate_scenes(cls, v: list[VideoScene]) -> list[VideoScene]:
        if not v or len(v) < 1:
            raise ValueError('At least one scene is required')
        return v


async def process_scenes_to_video_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Wrapper function for scenes-to-video job processing."""
    return await scenes_video_service.create_video(data)


@router.post("/scenes-to-video", response_model=JobResponse)
async def generate_video_from_scenes(
    request: ScenesToVideoRequest,
    _: dict[str, Any] = Depends(get_current_user)
):
    """Generate a video from individually defined scenes with narration, background media, and captions."""
    job_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Scenes-to-video request received with {len(request.scenes)} scenes")
        
        # Validate scenes
        valid_scenes = [s for s in request.scenes if s.text.strip()]
        if not valid_scenes:
            raise HTTPException(
                status_code=400,
                detail="At least one scene with text is required"
            )
        
        # Prepare job data
        job_data = {
            "scenes": [scene.model_dump() for scene in request.scenes],
            "config": request.config.model_dump()
        }
        
        # Create async job
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.SCENES_TO_VIDEO,
            process_func=process_scenes_to_video_wrapper,
            data=job_data
        )
        
        logger.info(f"Created scenes-to-video job {job_id}")
        
        return JobResponse(job_id=job_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating scenes-to-video job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create video generation job: {str(e)}"
        )
