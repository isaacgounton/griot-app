"""Pollinations AI image generation routes."""

import uuid
import time
from typing import Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.models import (
    JobType,
)
from app.services.job_queue import job_queue
from app.services.pollinations import pollinations_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/pollinations", tags=["Pollinations AI"])


class PollinationsImageRequest(BaseModel):
    prompt: str = Field(description="Text prompt for image generation")
    model: str = Field(default="flux", description="Image model")
    width: int | None = Field(default=None, ge=256, le=2048)
    height: int | None = Field(default=None, ge=256, le=2048)
    seed: int | None = Field(default=None)
    negative_prompt: str | None = Field(default=None, description="What to avoid in the image")
    enhance: bool = Field(default=False)
    nologo: bool = Field(default=True)
    safe: bool = Field(default=False)
    transparent: bool = Field(default=False)
    sync: bool = Field(default=False, description="If True, return response immediately. If False (default), create async job.")


class PollinationsImageResponse(BaseModel):
    job_id: str | None = None
    image_url: str | None = None
    prompt_used: str | None = None
    model_used: str | None = None
    dimensions: dict[str, int] | None = None
    processing_time: float | None = None


async def _process_pollinations_image(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    start_time = time.time()
    result = await pollinations_service.generate_image(
        prompt=data["prompt"],
        model=data.get("model", "flux"),
        width=data.get("width"),
        height=data.get("height"),
        seed=data.get("seed"),
        negative_prompt=data.get("negative_prompt"),
        enhance=data.get("enhance", False),
        nologo=data.get("nologo", True),
    )
    processing_time = time.time() - start_time
    image_url = result.get("url") or result.get("b64_json", "")
    return {
        "image_url": image_url,
        "prompt_used": data["prompt"],
        "model_used": data.get("model", "flux"),
        "dimensions": {"width": data.get("width", 0), "height": data.get("height", 0)},
        "processing_time": processing_time,
    }


@router.post("/image/generate", response_model=PollinationsImageResponse)
async def generate_pollinations_image(
    request: PollinationsImageRequest,
    _: dict[str, Any] = Depends(get_current_user),
):
    """Generate an image using Pollinations AI. Supports sync and async modes."""
    job_id = str(uuid.uuid4())
    job_data = request.model_dump()

    if request.sync:
        result = await _process_pollinations_image(job_id, job_data)
        return PollinationsImageResponse(
            image_url=result.get("image_url"),
            prompt_used=result.get("prompt_used"),
            model_used=result.get("model_used"),
            dimensions=result.get("dimensions"),
            processing_time=result.get("processing_time"),
        )

    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.IMAGE_GENERATION,
        process_func=_process_pollinations_image,
        data=job_data,
    )
    return PollinationsImageResponse(job_id=job_id)


@router.get("/models/image")
async def list_image_models():
    """List available Griot AI image generation models"""
    try:
        models = await pollinations_service.list_image_models()
        return {"models": models}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching image models: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch image models")


@router.get("/models/image-edit")
async def list_image_edit_models():
    """List image models that support editing (accept image input)"""
    try:
        models = await pollinations_service.list_image_edit_models()
        return {"models": models}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching image edit models: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch image edit models")


@router.get("/models/text")
async def list_text_models():
    """List available text generation models and voices"""
    try:
        models = await pollinations_service.list_text_models()
        return models
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching text models: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch text models")


@router.get("/models/video")
async def list_video_models():
    """List available Pollinations AI video generation models"""
    try:
        models = await pollinations_service.list_video_models()
        return {"models": models}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching video models: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch video models")
