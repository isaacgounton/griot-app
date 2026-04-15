"""
Routes for AI video generation from text prompts and images.
"""
import base64
import logging
import os
import tempfile
import time
import uuid
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field, field_validator

from app.models import JobResponse, JobType
from app.services.job_queue import job_queue
from app.services.video.ltx_video_service import ltx_video_service
from app.services.video.wavespeed_service import wavespeed_service
from app.services.video.comfyui_service import comfyui_service
from app.services.pollinations.pollinations_service import pollinations_service
from app.services.s3 import s3_service
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Video"])


class VideoGenerationResponse(BaseModel):
    """Union response model for video generation (sync or async)."""
    job_id: Optional[str] = None
    video_url: Optional[str] = None
    prompt_used: Optional[str] = None
    negative_prompt_used: Optional[str] = None
    dimensions: Optional[dict[str, int]] = None
    num_frames: Optional[int] = None
    processing_time: Optional[float] = None
    provider_used: Optional[str] = None


class VideoGenerationRequest(BaseModel):
    """Request model for AI video generation."""
    prompt: str = Field(description="Text prompt for video generation (max 2000 characters).")

    @field_validator('prompt')
    @classmethod
    def truncate_prompt(cls, v: str) -> str:
        if v and len(v) > 2000:
            return v[:2000]
        return v

    provider: str = Field(
        default="ltx_video",
        description="AI video provider (ltx_video, wavespeed, comfyui, pollinations)."
    )
    negative_prompt: str = Field(default="", description="Negative prompt for what to avoid.")
    width: int = Field(default=704, ge=256, le=1024, description="Video width (divisible by 32).")
    height: int = Field(default=480, ge=256, le=1024, description="Video height (divisible by 32).")
    num_frames: int = Field(default=150, ge=1, le=257, description="Number of frames (1-257).")
    sync: bool = Field(default=False, description="If true, return result immediately instead of creating async job.")
    num_inference_steps: int = Field(default=200, ge=1, le=500, description="Number of inference steps.")
    guidance_scale: float = Field(default=4.5, ge=1.0, le=20.0, description="Guidance scale for prompt adherence.")
    seed: Optional[int] = Field(default=None, description="Seed for reproducible results.")
    duration: Optional[int] = Field(default=None, description="Duration in seconds for WaveSpeed (5 or 8).")
    video_model: Optional[str] = Field(default=None, description="Video model for Pollinations provider (veo, seedance, wan, etc.).")
    audio: bool = Field(default=False, description="Enable audio generation (Pollinations only).")


class VideoGenerationResult(BaseModel):
    """Result model for video generation."""
    video_url: str
    prompt_used: str
    negative_prompt_used: str
    dimensions: dict[str, int]
    num_frames: int
    processing_time: float
    provider_used: str


class VideoFromImageRequest(BaseModel):
    """Request model for AI video generation from image."""
    prompt: str = Field(description="Text prompt describing the video motion/content (max 2000 characters).")

    @field_validator('prompt')
    @classmethod
    def truncate_prompt(cls, v: str) -> str:
        if v and len(v) > 2000:
            return v[:2000]
        return v

    negative_prompt: str = Field(default="", description="Negative prompt for what to avoid.")
    width: int = Field(default=704, ge=256, le=1024, description="Video width (divisible by 32).")
    height: int = Field(default=480, ge=256, le=1024, description="Video height (divisible by 32).")
    num_frames: int = Field(default=150, ge=1, le=257, description="Number of frames (1-257).")
    sync: bool = Field(default=False, description="If true, return result immediately.")
    num_inference_steps: int = Field(default=200, ge=1, le=500, description="Number of inference steps.")
    guidance_scale: float = Field(default=4.5, ge=1.0, le=20.0, description="Guidance scale for prompt adherence.")
    seed: Optional[int] = Field(default=None, description="Seed for reproducible results.")


class VideoFromImageResult(BaseModel):
    """Result model for video generation from image."""
    original_image_url: str
    video_url: str
    prompt_used: str
    negative_prompt_used: str
    dimensions: dict[str, int]
    num_frames: int
    processing_time: float
    provider_used: str


async def process_video_generation_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Process a text-to-video generation job."""
    start_time = time.time()
    temp_file_path = None

    try:
        prompt = data["prompt"]
        provider = data.get("provider", "ltx_video")
        negative_prompt = data.get("negative_prompt", "")
        width = data.get("width", 704)
        height = data.get("height", 480)
        num_frames = data.get("num_frames", 150)
        num_inference_steps = data.get("num_inference_steps", 200)
        guidance_scale = data.get("guidance_scale", 4.5)
        seed = data.get("seed")
        duration = data.get("duration")

        if provider == "wavespeed":
            if not wavespeed_service.is_available():
                raise ValueError("WaveSpeed service is not available (API key or URL not configured)")

            if width == 704 and height == 480:
                size = "832*480"
            elif width == 480 and height == 704:
                size = "480*832"
            else:
                size = f"{width}*{height}"

            if duration is not None:
                if duration not in [5, 8]:
                    raise ValueError(f"WaveSpeed duration must be 5 or 8 seconds, got {duration}")
            else:
                calculated_duration = int(num_frames / 15)
                duration = 5 if calculated_duration <= 5 else 8

            video_data = await wavespeed_service.text_to_video(
                prompt=prompt,
                model="wan-2.2",
                size=size,
                duration=duration,
                seed=seed if seed is not None else -1
            )
        elif provider == "pollinations":
            video_model = data.get("video_model") or "veo"
            aspect_ratio = "16:9" if width > height else "9:16"
            calculated_duration = duration if duration is not None else int(num_frames / 30)
            audio_enabled = data.get("audio", False)

            video_data = await pollinations_service.generate_video(
                prompt=prompt,
                model=video_model,
                duration=calculated_duration,
                aspect_ratio=aspect_ratio,
                audio=audio_enabled,
                negative_prompt=negative_prompt if negative_prompt else None,
                seed=seed,
                width=width,
                height=height,
                private=True,
            )
        elif provider == "comfyui":
            if not comfyui_service.is_available():
                raise ValueError("ComfyUI service is not available (URL and auth not configured)")

            video_data = await comfyui_service.text_to_video(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_frames=num_frames
            )
        else:
            if not ltx_video_service.is_available():
                raise ValueError("Modal Video service is not available (API key or URL not configured)")

            video_data = await ltx_video_service.generate_video(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                seed=seed
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(video_data)
            temp_file_path = temp_file.name

        s3_path = f"generated-videos/{job_id}.mp4"
        video_url = await s3_service.upload_file(
            file_path=temp_file_path,
            object_name=s3_path,
            content_type="video/mp4"
        )

        processing_time = time.time() - start_time

        result = VideoGenerationResult(
            video_url=video_url,
            prompt_used=prompt,
            negative_prompt_used=negative_prompt,
            dimensions={"width": width, "height": height},
            num_frames=num_frames,
            processing_time=processing_time,
            provider_used=provider
        )

        return result.model_dump()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_err:
                logger.warning(f"Failed to clean up temporary file {temp_file_path}: {cleanup_err}")


async def process_video_from_image_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Process an image-to-video generation job."""
    start_time = time.time()
    original_temp_file = None
    video_temp_file = None

    try:
        prompt = data["prompt"]
        provider = data.get("provider", "ltx_video")
        negative_prompt = data.get("negative_prompt", "")
        width = data.get("width", 704)
        height = data.get("height", 480)
        num_frames = data.get("num_frames", 150)
        num_inference_steps = data.get("num_inference_steps", 200)
        guidance_scale = data.get("guidance_scale", 4.5)
        seed = data.get("seed")
        duration = data.get("duration")

        if "original_image_data_b64" in data:
            original_image_data = base64.b64decode(data["original_image_data_b64"])
        else:
            original_image_data = data["original_image_data"]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_file.write(original_image_data)
            original_temp_file = temp_file.name

        original_s3_path = f"original-images/{job_id}.png"
        original_image_url = await s3_service.upload_file(
            file_path=original_temp_file,
            object_name=original_s3_path,
            content_type="image/png"
        )

        if provider == "wavespeed":
            if not wavespeed_service.is_available():
                raise ValueError("WaveSpeed service is not available (API key or URL not configured)")

            resolution = f"{width}x{height}" if width and height else "720p"

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tf:
                tf.write(original_image_data)
                ws_temp_path = tf.name

            try:
                object_name = f"temp_images/{uuid.uuid4()}.png"
                image_url = await s3_service.upload_file(ws_temp_path, object_name, "image/png")

                video_data = await wavespeed_service.image_to_video(
                    image_url=image_url,
                    prompt=prompt,
                    model="wan-2.2",
                    resolution=resolution,
                    seed=seed if seed is not None else -1
                )
            finally:
                if os.path.exists(ws_temp_path):
                    os.unlink(ws_temp_path)
        elif provider == "comfyui":
            if not comfyui_service.is_available():
                raise ValueError("ComfyUI service is not available (URL and auth not configured)")

            video_data = await comfyui_service.text_to_video(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_frames=num_frames
            )
        elif provider == "pollinations":
            video_model = data.get("video_model") or "veo"
            aspect_ratio = "16:9" if width > height else "9:16"
            calculated_duration = duration if duration is not None else int(num_frames / 30)
            audio_enabled = data.get("audio", False)

            video_data = await pollinations_service.generate_video(
                prompt=prompt,
                model=video_model,
                duration=calculated_duration,
                aspect_ratio=aspect_ratio,
                audio=audio_enabled,
                negative_prompt=negative_prompt if negative_prompt else None,
                seed=seed,
                width=width,
                height=height,
                image_url=data.get("original_image_url"),
                private=True,
            )
        else:
            if not ltx_video_service.is_available():
                raise ValueError("Modal Video service is not available (API key or URL not configured)")

            video_data = await ltx_video_service.image_to_video(
                image_bytes=original_image_data,
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                seed=seed
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(video_data)
            video_temp_file = temp_file.name

        video_s3_path = f"generated-videos/{job_id}.mp4"
        video_url = await s3_service.upload_file(
            file_path=video_temp_file,
            object_name=video_s3_path,
            content_type="video/mp4"
        )

        processing_time = time.time() - start_time

        result = VideoFromImageResult(
            original_image_url=original_image_url,
            video_url=video_url,
            prompt_used=prompt,
            negative_prompt_used=negative_prompt,
            dimensions={"width": width, "height": height},
            num_frames=num_frames,
            processing_time=processing_time,
            provider_used=provider
        )

        result_dict = result.model_dump()
        result_dict['video_url'] = video_url
        return result_dict

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video generation from image failed: {str(e)}")
    finally:
        for path in [original_temp_file, video_temp_file]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception as cleanup_err:
                    logger.warning(f"Failed to clean up temporary file {path}: {cleanup_err}")


@router.post("/generate", response_model=VideoGenerationResponse)
async def generate_video(
    request: VideoGenerationRequest,
    _: Dict[str, Any] = Depends(get_current_user)
):
    """Generate an AI video from a text prompt. Supports ltx_video, wavespeed, comfyui, and pollinations providers with sync/async modes."""
    job_id = str(uuid.uuid4())

    try:
        if request.provider not in ["ltx_video", "wavespeed", "comfyui", "pollinations"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported provider: {request.provider}. Supported: ltx_video, wavespeed, comfyui, pollinations"
            )

        if request.provider == "wavespeed" and not wavespeed_service.is_available():
            raise HTTPException(status_code=503, detail="WaveSpeed service is currently unavailable")
        elif request.provider == "comfyui" and not comfyui_service.is_available():
            raise HTTPException(status_code=503, detail="ComfyUI service is currently unavailable")
        elif request.provider == "ltx_video" and not ltx_video_service.is_available():
            raise HTTPException(status_code=503, detail="Modal Video service is currently unavailable")

        job_data = request.model_dump()

        if request.sync:
            result = await process_video_generation_wrapper(job_id, job_data)
            return VideoGenerationResponse(
                video_url=result.get("video_url"),
                prompt_used=result.get("prompt_used"),
                negative_prompt_used=result.get("negative_prompt_used"),
                dimensions=result.get("dimensions"),
                num_frames=result.get("num_frames"),
                processing_time=result.get("processing_time"),
                provider_used=result.get("provider_used")
            )

        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.VIDEO_GENERATION,
            process_func=process_video_generation_wrapper,
            data=job_data
        )

        return VideoGenerationResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        if request.sync:
            raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to create video generation job: {str(e)}")


@router.post("/from_image", response_model=JobResponse)
async def generate_video_from_image(
    prompt: str = Form(..., description="Text prompt describing the video motion/content (max 1000 characters)."),
    image: UploadFile = File(..., description="Image file to animate (PNG, JPG, JPEG up to 10MB)."),
    provider: str = Form("ltx_video", description="AI video provider (ltx_video, wavespeed, comfyui, pollinations)."),
    negative_prompt: str = Form("", description="Negative prompt for what to avoid."),
    width: int = Form(704, ge=256, le=1024, description="Video width (divisible by 32)."),
    height: int = Form(480, ge=256, le=1024, description="Video height (divisible by 32)."),
    num_frames: int = Form(150, ge=1, le=257, description="Number of frames (1-257)."),
    num_inference_steps: int = Form(200, ge=1, le=500, description="Number of inference steps."),
    guidance_scale: float = Form(4.5, ge=1.0, le=20.0, description="Guidance scale for prompt adherence."),
    seed: Optional[int] = Form(None, description="Seed for reproducible results."),
    duration: Optional[int] = Form(None, description="Duration in seconds for WaveSpeed (5 or 8)."),
    _: Dict[str, Any] = Depends(get_current_user)
):
    """Generate a video by animating an uploaded image with AI. Supports multiple providers."""
    job_id = str(uuid.uuid4())

    try:
        if len(prompt) > 1000:
            raise HTTPException(status_code=400, detail="Prompt too long. Maximum 1000 characters.")

        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PNG or JPEG image.")

        if provider not in ["ltx_video", "wavespeed", "comfyui", "pollinations"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported provider: {provider}. Supported: ltx_video, wavespeed, comfyui, pollinations"
            )

        if provider == "wavespeed" and not wavespeed_service.is_available():
            raise HTTPException(status_code=503, detail="WaveSpeed service is currently unavailable")
        elif provider == "comfyui" and not comfyui_service.is_available():
            raise HTTPException(status_code=503, detail="ComfyUI service is currently unavailable")
        elif provider == "ltx_video" and not ltx_video_service.is_available():
            raise HTTPException(status_code=503, detail="Modal Video service is currently unavailable")

        image_data = await image.read()

        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image file too large. Maximum 10MB.")

        image_data_b64 = base64.b64encode(image_data).decode('utf-8')

        job_data = {
            "prompt": prompt,
            "provider": provider,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "num_frames": num_frames,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "seed": seed,
            "duration": duration,
            "original_image_data_b64": image_data_b64
        }

        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.VIDEO_FROM_IMAGE,
            process_func=process_video_from_image_wrapper,
            data=job_data
        )

        return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in video generation from image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create video generation job: {str(e)}")
