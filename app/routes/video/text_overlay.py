"""
Routes for text overlay functionality.
"""
import uuid
import logging
from fastapi import APIRouter, HTTPException

from app.models import (
    JobResponse,
    TextOverlayRequest,
    JobType,
)
from app.services.job_queue import job_queue
from app.services.video.text_overlay import text_overlay_service, TextOverlayOptions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/text-overlay", tags=["Video"])


async def process_text_overlay_job(_job_id: str, job_data: dict) -> dict:
    """Process text overlay job using the clean service."""
    try:
        video_url = job_data["video_url"]
        text = job_data["text"]
        options_dict = job_data.get("options", {})

        # Use `or` pattern because Pydantic legacy fields may exist as None
        overlay_options = TextOverlayOptions(
            text=text,
            font_size=options_dict.get("font_size") or 48,
            font_color=options_dict.get("font_color") or "white",
            position=options_dict.get("position") or "bottom-center",
            y_offset=options_dict.get("y_offset") if options_dict.get("y_offset") is not None else 50,
            box_color=options_dict.get("box_color"),
            box_opacity=options_dict.get("box_opacity") if options_dict.get("box_opacity") is not None else 0.8,
            box_padding=options_dict.get("box_padding") or options_dict.get("boxborderw") or 10,
            duration=options_dict.get("duration") or 5.0,
            start_time=options_dict.get("start_time") or 0.0,
            line_spacing=options_dict.get("line_spacing") if options_dict.get("line_spacing") is not None else 8,
            auto_wrap=options_dict.get("auto_wrap") if options_dict.get("auto_wrap") is not None else True,
            max_chars_per_line=options_dict.get("max_chars_per_line") or 25
        )

        result = await text_overlay_service.create_text_overlay(video_url, overlay_options)

        if not result.get("success"):
            raise Exception(result.get("error", "Unknown error"))

        return {
            "url": result["video_url"],
            "file_size": result.get("file_size", 0),
            "message": result["message"]
        }

    except Exception as e:
        logger.error(f"Text overlay processing failed: {str(e)}")
        raise


@router.post("", response_model=JobResponse)
async def create_text_overlay_job(request: TextOverlayRequest):
    """Add text overlay to a video with customizable font, color, position, background box, and duration."""
    try:
        if not request.video_url:
            raise HTTPException(status_code=400, detail="No video URL provided")

        if not request.text.strip():
            raise HTTPException(status_code=400, detail="No text provided")

        job_data = {
            "video_url": str(request.video_url),
            "text": request.text,
            "options": request.options.model_dump() if request.options else {}
        }

        job_id = str(uuid.uuid4())

        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.TEXT_OVERLAY,
            process_func=process_text_overlay_job,
            data=job_data
        )

        logger.info(f"Created text overlay job: {job_id}")
        return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create text overlay job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create text overlay job: {str(e)}"
        )


@router.get("/all-presets")
async def get_all_text_overlay_presets():
    """Get available text overlay presets (title, subtitle, watermark, alert, caption)."""
    try:
        presets = text_overlay_service.get_presets()
        return {
            "presets": presets,
            "categories": list(presets.keys()),
            "total_count": len(presets)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving presets: {str(e)}")
