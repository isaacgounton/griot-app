"""
Routes for music generation using Meta's MusicGen model.
"""
from typing import Any
from fastapi import APIRouter, HTTPException
from app.models import MusicGenerationRequest, JobResponse, JobType
from app.services.job_queue import job_queue
from app.services.audio.music_generation import music_generation_service
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/music", tags=["Audio"])


@router.post("", response_model=JobResponse)
async def create_music_generation_job(request: MusicGenerationRequest):
    """Generate music from a text description using Meta's MusicGen model. Supports WAV and MP3 output."""
    try:
        # Validate request
        if not request.description or not request.description.strip():
            raise HTTPException(status_code=400, detail="Description cannot be empty")
        
        if len(request.description) > 500:
            raise HTTPException(status_code=400, detail="Description exceeds maximum length of 500 characters")
        
        # Validate model size
        if request.model_size.lower() not in ["small"]:
            raise HTTPException(status_code=400, detail="Model size must be 'small'")
        
        # Validate output format
        if request.output_format.lower() not in ["wav", "mp3"]:
            raise HTTPException(status_code=400, detail="Output format must be 'wav' or 'mp3'")
        
        # Create job parameters
        job_params = {
            "description": request.description.strip(),
            "duration": request.duration,
            "model_size": request.model_size.lower(),
            "output_format": request.output_format.lower()
        }
        
        # Create a new job
        job_id = str(uuid.uuid4())
        
        # Create a wrapper function that matches job queue signature
        async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
            return await music_generation_service.process_music_generation(_job_id, data)
        
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.MUSIC_GENERATION,
            process_func=process_wrapper,
            data=job_params
        )
        
        logger.info(f"Created music generation job {job_id} with description: {request.description[:50]}...")
        
        return JobResponse(job_id=job_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create music generation job: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/info")
async def get_music_generation_info():
    """Get music generation capabilities, supported models, formats, and examples."""
    return {
        "endpoint": "/v1/audio/music",
        "method": "POST",
        "description": "Generate music from text descriptions using Meta's MusicGen model",
        "model_info": {
            "name": "Meta MusicGen Stereo",
            "type": "Text-to-audio generation",
            "supported_models": ["small"],
            "max_duration": 30,
            "supported_formats": ["wav", "mp3"]
        },
        "parameters": {
            "description": {
                "type": "string",
                "required": True,
                "max_length": 500,
                "description": "Text description of the music to generate"
            },
            "duration": {
                "type": "integer",
                "required": False,
                "default": 8,
                "min": 1,
                "max": 30,
                "description": "Duration in seconds"
            },
            "model_size": {
                "type": "string",
                "required": False,
                "default": "small",
                "options": ["small"],
                "description": "Model size to use"
            },
            "output_format": {
                "type": "string",
                "required": False,
                "default": "wav",
                "options": ["wav", "mp3"],
                "description": "Output audio format"
            }
        },
        "examples": [
            {
                "description": "lo-fi music with a soothing melody",
                "duration": 8,
                "model_size": "small"
            },
            {
                "description": "upbeat electronic dance music",
                "duration": 15,
                "model_size": "small"
            },
            {
                "description": "acoustic guitar melody in major key",
                "duration": 10,
                "model_size": "small"
            },
            {
                "description": "orchestral music with strings and piano",
                "duration": 20,
                "model_size": "small"
            }
        ],
        "tips": [
            "Be specific in your descriptions for better results",
            "Include genre, instruments, mood, and style",
            "Longer descriptions often produce more accurate results",
            "Consider tempo keywords like 'slow', 'fast', 'upbeat'"
        ]
    }