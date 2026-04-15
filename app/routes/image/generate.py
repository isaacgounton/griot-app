import uuid
import logging
import base64
from typing import Any
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field, field_validator
from app.models import JobResponse, JobType
from app.services.job_queue import job_queue
from app.services.image.together_ai_service import together_ai_service
from app.services.image.modal_image_service import modal_image_service
from app.services.pollinations.pollinations_service import pollinations_service
from app.services.s3 import s3_service
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["Images"])

# Create a separate router for the simple image edit endpoint
simple_router = APIRouter(tags=["Images"])


class ImageGenerationResponse(BaseModel):
    job_id: str | None = None
    image_url: str | None = None
    prompt_used: str | None = None
    model_used: str | None = None
    dimensions: dict[str, int] | None = None
    processing_time: float | None = None


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(
        description="Text prompt for image generation (will be truncated to 2000 characters if longer)."
    )
    model: str = Field(
        default="black-forest-labs/FLUX.1-schnell",
        description="Image generation model to use."
    )
    width: int = Field(
        default=576,
        ge=256,
        le=2048,
        description="Image width in pixels."
    )
    height: int = Field(
        default=1024,
        ge=256,
        le=2048,
        description="Image height in pixels."
    )
    steps: int = Field(
        default=4,
        ge=1,
        le=50,
        description="Number of inference steps."
    )
    provider: str = Field(
        default="together",
        description="Image generation provider: 'together' or 'modal_image'."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )

    @field_validator('prompt')
    @classmethod
    def truncate_prompt(cls, v: str) -> str:
        if v and len(v) > 2000:
            return v[:2000]
        return v


class ImageGenerationResult(BaseModel):
    image_url: str = Field(
        description="URL to the generated image stored in S3."
    )
    prompt_used: str = Field(
        description="The prompt that was used for generation."
    )
    model_used: str = Field(
        description="The model that was used for generation."
    )
    dimensions: dict[str, int] = Field(
        description="Image dimensions (width, height)."
    )
    processing_time: float = Field(
        description="Processing time in seconds."
    )


class ImageEditRequest(BaseModel):
    prompt: str = Field(
        description="Text prompt describing the desired edit (will be truncated to 2000 characters if longer)."
    )
    guidance_scale: float = Field(
        default=3.5,
        ge=1.0,
        le=20.0,
        description="Guidance scale (higher = more prompt adherence)."
    )
    num_inference_steps: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Number of inference steps."
    )
    seed: int | None = Field(
        default=None,
        description="Optional seed for reproducible results."
    )

    @field_validator('prompt')
    @classmethod
    def truncate_prompt(cls, v: str) -> str:
        if v and len(v) > 2000:
            return v[:2000]
        return v


class ImageEditResult(BaseModel):
    original_image_url: str = Field(
        description="URL to the original image stored in S3."
    )
    edited_image_url: str = Field(
        description="URL to the edited image stored in S3."
    )
    prompt_used: str = Field(
        description="The prompt that was used for editing."
    )
    processing_time: float = Field(
        description="Processing time in seconds."
    )


async def process_image_generation_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Wrapper function for image generation job processing."""
    import time
    import tempfile
    import os
    start_time = time.time()
    
    temp_file_path = None
    try:
        # Extract parameters
        prompt = data["prompt"]
        model = data.get("model", "black-forest-labs/FLUX.1-schnell")
        width = data.get("width", 576)
        height = data.get("height", 1024)
        steps = data.get("steps", 4)
        provider = data.get("provider", "together")
        
        if provider == "together":
            if not together_ai_service.is_available():
                raise ValueError("Together.ai service is not available (API key not configured)")
            
            # Generate image with Together.ai
            image_data = await together_ai_service.generate_image_from_b64(
                prompt=prompt,
                model=model,
                width=width,
                height=height,
                steps=steps
            )
        elif provider == "modal_image":
            if not modal_image_service.is_available():
                raise ValueError("Flux service is not available (API key or URL not configured)")
            
            # Generate image with Flux (using steps as num_inference_steps)
            image_data = await modal_image_service.generate_image(
                prompt=prompt,
                width=width,
                height=height,
                num_inference_steps=steps
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}. Supported providers: 'together', 'modal_image'")
        
        # Save binary data to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name
        
        # Upload to S3
        s3_path = f"generated-images/{job_id}.png"
        image_url = await s3_service.upload_file(
            file_path=temp_file_path,
            object_name=s3_path,
            content_type="image/png"
        )
        
        processing_time = time.time() - start_time
        
        result = ImageGenerationResult(
            image_url=image_url,
            prompt_used=prompt,
            model_used=model,
            dimensions={"width": width, "height": height},
            processing_time=processing_time
        )
        
        return result.model_dump()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                # Log error but don't fail the main operation
                logger.warning(f"Failed to clean up temporary file {temp_file_path}: {e}")


async def process_image_edit_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Wrapper function for image editing job processing using Pollinations AI."""
    import time
    import tempfile
    import os
    start_time = time.time()

    original_temp_file = None
    edited_temp_file = None
    try:
        # Extract parameters
        prompt = data["prompt"]
        seed = data.get("seed")
        negative_prompt = data.get("negative_prompt")

        # Handle both old format (binary) and new format (base64)
        if "original_image_data_b64" in data:
            original_image_data = base64.b64decode(data["original_image_data_b64"])
        else:
            # Fallback for old format (if any exist)
            original_image_data = data["original_image_data"]

        # Save original image to temporary file for S3 upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_file.write(original_image_data)
            original_temp_file = temp_file.name

        # Upload original image to S3
        original_s3_path = f"original-images/{job_id}.png"
        original_image_url = await s3_service.upload_file(
            file_path=original_temp_file,
            object_name=original_s3_path,
            content_type="image/png"
        )

        # Edit image with Pollinations AI (kontext supports in-context editing)
        model = data.get("model", "kontext")
        edited_image_data = await pollinations_service.edit_image(
            image_bytes=original_image_data,
            prompt=prompt,
            model=model,
            seed=seed,
            negative_prompt=negative_prompt,
        )
        
        # Save edited image to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_file.write(edited_image_data)
            edited_temp_file = temp_file.name
        
        # Upload edited image to S3
        edited_s3_path = f"edited-images/{job_id}.png"
        edited_image_url = await s3_service.upload_file(
            file_path=edited_temp_file,
            object_name=edited_s3_path,
            content_type="image/png"
        )
        
        processing_time = time.time() - start_time
        
        result = ImageEditResult(
            original_image_url=original_image_url,
            edited_image_url=edited_image_url,
            prompt_used=prompt,
            processing_time=processing_time
        )
        
        # Add image_url for media library compatibility
        result_dict = result.model_dump()
        result_dict['image_url'] = edited_image_url  # Primary URL for media library
        
        return result_dict
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image editing failed: {str(e)}")
    finally:
        # Clean up temporary files
        for temp_file_path in [original_temp_file, edited_temp_file]:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {temp_file_path}: {e}")


@router.post("/generate", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest,
    _: dict[str, Any] = Depends(get_current_user)
):
    """Generate AI images from text prompts using Together.ai or Modal. Supports sync and async modes."""
    job_id = str(uuid.uuid4())
    
    try:
        # Validate provider and check availability
        if request.provider == "together":
            if not together_ai_service.is_available():
                raise HTTPException(
                    status_code=503,
                    detail="Together.ai service is currently unavailable (API key not configured)"
                )
        elif request.provider == "modal_image":
            if not modal_image_service.is_available():
                raise HTTPException(
                    status_code=503,
                    detail="Flux service is currently unavailable (API key or URL not configured)"
                )
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported provider. Supported providers: 'together', 'modal_image'"
            )
        
        # Handle synchronous mode
        if request.sync:
            # Generate image directly and return result
            job_data = request.model_dump()
            result = await process_image_generation_wrapper(job_id, job_data)
            
            return ImageGenerationResponse(
                image_url=result.get("image_url"),
                prompt_used=result.get("prompt_used"),
                model_used=result.get("model_used"),
                dimensions=result.get("dimensions"),
                processing_time=result.get("processing_time")
            )
        
        # Handle asynchronous mode (default)
        # Prepare job data
        job_data = request.model_dump()
        
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.IMAGE_GENERATION,
            process_func=process_image_generation_wrapper,
            data=job_data
        )
        
        return ImageGenerationResponse(job_id=job_id)
    
    except HTTPException:
        raise
    except Exception as e:
        if request.sync:
            raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to create image generation job: {str(e)}")


@router.post("/ai-edit", response_model=JobResponse)
async def edit_image(
    prompt: str = Form(..., description="Text prompt describing the desired edit (max 1000 characters)."),
    image: UploadFile = File(..., description="Image file to edit (PNG, JPG, JPEG up to 10MB)."),
    model: str = Form("kontext", description="Image editing model (kontext, nanobanana, seedream, klein, etc.)."),
    negative_prompt: str | None = Form(None, description="What to avoid in the edited image."),
    seed: int | None = Form(None, description="Optional seed for reproducible results."),
    _: dict[str, Any] = Depends(get_current_user)
):
    """Edit an uploaded image using AI (Pollinations). Accepts PNG/JPG up to 10MB."""
    job_id = str(uuid.uuid4())

    try:
        # Validate prompt length
        if len(prompt) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Prompt too long. Maximum 1000 characters allowed."
            )

        # Validate file type
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload a PNG or JPEG image."
            )

        logger.info(f"Image edit request received - prompt: '{prompt}', model: {model}, seed: {seed}")
        logger.info(f"Image info - filename: {image.filename}, content_type: {image.content_type}")

        # Read image data after all other validations
        image_data = await image.read()

        # Validate file size (10MB limit)
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="Image file too large. Please upload an image smaller than 10MB."
            )

        # Convert image data to base64 for JSON serialization
        image_data_b64 = base64.b64encode(image_data).decode('utf-8')

        # Prepare job data
        job_data = {
            "prompt": prompt,
            "model": model,
            "negative_prompt": negative_prompt,
            "seed": seed,
            "original_image_data_b64": image_data_b64
        }

        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.IMAGE_EDITING,
            process_func=process_image_edit_wrapper,
            data=job_data
        )

        return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in image editing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create image editing job: {str(e)}")



@router.post("/edit_image", response_model=JobResponse)
async def simple_image_edit(
    prompt: str = Form(..., description="Text prompt describing the desired edit (max 1000 characters)."),
    image: UploadFile = File(..., description="Image file to edit (PNG, JPG, JPEG up to 10MB)."),
    model: str = Form("kontext", description="Image editing model (kontext, nanobanana, seedream, klein, etc.)."),
    negative_prompt: str | None = Form(None, description="What to avoid in the edited image."),
    seed: int | None = Form(None, description="Optional seed for reproducible results."),
    _: dict[str, Any] = Depends(get_current_user)
):
    """Simple image editing endpoint for external tool compatibility (n8n, etc.)."""
    job_id = str(uuid.uuid4())

    try:
        # Validate prompt length
        if len(prompt) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Prompt too long. Maximum 1000 characters allowed."
            )

        # Validate file type
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload a PNG or JPEG image."
            )

        logger.info(f"Simple image edit request received - prompt: '{prompt}', model: {model}, seed: {seed}")
        logger.info(f"Image info - filename: {image.filename}, content_type: {image.content_type}")

        # Read image data after all other validations
        image_data = await image.read()

        # Validate file size (10MB limit)
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="Image file too large. Please upload an image smaller than 10MB."
            )

        # Convert image data to base64 for JSON serialization
        image_data_b64 = base64.b64encode(image_data).decode('utf-8')

        # Prepare job data
        job_data = {
            "prompt": prompt,
            "model": model,
            "negative_prompt": negative_prompt,
            "seed": seed,
            "original_image_data_b64": image_data_b64
        }

        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.IMAGE_EDITING,
            process_func=process_image_edit_wrapper,
            data=job_data
        )
        
        return JobResponse(job_id=job_id)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in simple image editing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create image editing job: {str(e)}")


@router.get("/models/together", response_model=dict[str, list[str]])
async def list_together_models(current_user: dict[str, Any] = Depends(get_current_user)):
    """List available Together.ai image generation models."""
    try:
        models = together_ai_service.get_available_models()
        return {"models": models}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Together.ai models: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Together.ai models")


@router.get("/models/modal", response_model=dict[str, list[str]])
async def list_modal_models(current_user: dict[str, Any] = Depends(get_current_user)):
    """List available Modal image generation models."""
    try:
        models = modal_image_service.get_available_models()
        return {"models": models}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Modal Image models: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Modal Image models")
