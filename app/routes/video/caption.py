"""
Routes for advanced caption operations with auto-transcription and multiple styles.
"""
import uuid
import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field

from app.models import JobResponse, JobStatusResponse, JobType, JobStatus
from app.services.job_queue import job_queue
from app.services.video.caption_service import advanced_caption_service
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/add-captions", tags=["Video"])


class TimeRange(BaseModel):
    """Time range for excluding caption segments."""
    start: str = Field(..., description="Start time (hh:mm:ss.ms)")
    end: str = Field(..., description="End time (hh:mm:ss.ms)")


class TextReplacement(BaseModel):
    """Text replacement rule."""
    find: str = Field(..., description="Text to find")
    replace: str = Field(..., description="Text to replace with")


class CaptionSettings(BaseModel):
    """Advanced caption styling settings."""
    line_color: Optional[str] = Field(None, description="Line text color (hex or ASS format)")
    word_color: Optional[str] = Field(None, description="Highlighted word color")
    outline_color: Optional[str] = Field(None, description="Outline color")
    all_caps: Optional[bool] = Field(False, description="Convert text to uppercase")
    max_words_per_line: Optional[int] = Field(None, description="Max words per line")
    x: Optional[int] = Field(None, description="X position coordinate")
    y: Optional[int] = Field(None, description="Y position coordinate")
    position: Optional[str] = Field(None, description="Position preset (bottom_center, top_left, etc.)")
    alignment: Optional[str] = Field(None, description="Text alignment (left, center, right)")
    font_family: Optional[str] = Field("Arial", description="Font family name")
    font_size: Optional[int] = Field(24, description="Font size in pixels")
    bold: Optional[bool] = Field(False, description="Bold text")
    italic: Optional[bool] = Field(False, description="Italic text")
    underline: Optional[bool] = Field(False, description="Underline text")
    strikeout: Optional[bool] = Field(False, description="Strikeout text")
    style: Optional[str] = Field("classic", description="Style: classic, karaoke, highlight, underline, word_by_word")
    outline_width: Optional[int] = Field(2, description="Outline width in pixels")
    spacing: Optional[int] = Field(0, description="Character spacing")
    angle: Optional[int] = Field(0, description="Text rotation angle")
    shadow_offset: Optional[int] = Field(0, description="Shadow offset")
    margin_v: Optional[int] = Field(20, description="Vertical margin")


class CaptionRequest(BaseModel):
    """Request model for caption creation."""
    video_url: str = Field(..., description="URL of the video to caption")
    captions: Optional[str] = Field(None, description="SRT/ASS text, URL, or omit for auto-transcription")
    settings: Optional[CaptionSettings] = Field(None, description="Caption styling settings")
    replace: Optional[List[TextReplacement]] = Field(None, description="Text replacement rules")
    exclude_time_ranges: Optional[List[TimeRange]] = Field(None, description="Time ranges to exclude")
    language: Optional[str] = Field("auto", description="Language for transcription (e.g., 'en', 'fr', 'auto')")
    sync: Optional[bool] = Field(False, description="Process synchronously if true")


@router.post("")
async def create_advanced_caption_job(
    request: CaptionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Add advanced captions to a video with auto-transcription, multiple styles (classic, karaoke, highlight, underline, word_by_word), text replacement, and time range exclusion."""
    try:
        logger.info(f"Advanced caption request: video={request.video_url}, style={request.settings.style if request.settings else 'classic'}, sync={request.sync}")

        job_data = {
            "video_url": request.video_url,
            "captions": request.captions,
            "settings": request.settings.model_dump() if request.settings else {},
            "replace": [r.model_dump() for r in request.replace] if request.replace else [],
            "exclude_time_ranges": [t.model_dump() for t in request.exclude_time_ranges] if request.exclude_time_ranges else [],
            "language": request.language
        }

        if request.sync:
            try:
                logger.info("Processing synchronous advanced caption job")
                result = await advanced_caption_service.process_caption_job(
                    job_id="sync",
                    params=job_data
                )

                return JobStatusResponse(
                    job_id="sync",
                    status=JobStatus.COMPLETED,
                    result=result
                )
            except Exception as e:
                logger.error(f"Synchronous caption processing failed: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Caption processing failed: {str(e)}"
                )
        else:
            job_id = str(uuid.uuid4())

            try:
                await job_queue.add_job(
                    job_id=job_id,
                    job_type=JobType.VIDEO_ADD_CAPTIONS,
                    process_func=advanced_caption_service.process_caption_job,
                    data=job_data
                )

                logger.info(f"Created advanced caption job: {job_id}")
                return JobResponse(job_id=job_id)
            except Exception as e:
                logger.error(f"Failed to create caption job: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create caption job: {str(e)}"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_advanced_caption_job: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_caption_job_status(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get the status of a caption job by ID."""
    try:
        job_info = await job_queue.get_job(job_id)

        if not job_info:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )

        logger.info(f"Caption job {job_id} status: {job_info.status}")

        return JobStatusResponse(
            job_id=job_id,
            status=job_info.status,
            result=job_info.result,
            error=job_info.error
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.get("/styles/list")
async def list_caption_styles(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List available caption styles with descriptions and use cases."""
    return {
        "styles": [
            {
                "name": "classic",
                "description": "Regular captioning with all text displayed at once",
                "use_case": "Traditional subtitles"
            },
            {
                "name": "karaoke",
                "description": "Word-by-word highlighting with smooth transitions",
                "use_case": "Social media short-form videos"
            },
            {
                "name": "highlight",
                "description": "Full text visible with current word color-highlighted",
                "use_case": "Educational content and tutorials"
            },
            {
                "name": "underline",
                "description": "Full text visible with current word underlined",
                "use_case": "Professional and corporate videos"
            },
            {
                "name": "word_by_word",
                "description": "Shows one word at a time for maximum focus",
                "use_case": "Dramatic effect and motivational content"
            }
        ],
        "default": "classic",
        "recommended_for_social_media": "karaoke"
    }


@router.post("/preview")
async def preview_caption_style(
    video_url: str = Body(..., embed=True),
    text: str = Body("Sample caption text", embed=True),
    style: str = Body("karaoke", embed=True),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Preview how captions will render with a specific style (returns description, not actual video)."""
    style_info = {
        "classic": {
            "description": "All text appears at once and stays visible for the duration",
            "best_for": "Long sentences, traditional subtitles",
        },
        "karaoke": {
            "description": "Words highlight sequentially with smooth color transitions",
            "best_for": "Music videos, engaging short-form videos",
        },
        "highlight": {
            "description": "Full text is always visible, current word changes color",
            "best_for": "Education, presentations, tutorials",
        },
        "underline": {
            "description": "Full text is always visible, current word gets underlined",
            "best_for": "Professional content, corporate videos",
        },
        "word_by_word": {
            "description": "Only one word visible at a time, maximum focus",
            "best_for": "Dramatic effect, motivational quotes",
        }
    }

    if style not in style_info:
        raise HTTPException(status_code=400, detail=f"Unknown style: {style}")

    return {
        "style": style,
        "sample_text": text,
        "rendering": style_info[style]
    }
