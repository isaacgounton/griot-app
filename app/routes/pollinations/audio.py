"""Pollinations AI audio generation routes."""

import uuid
import time
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.models import (
    JobResponse,
    JobType,
    PollinationsAudioRequest,
    PollinationsTranscriptionRequest,
)
from app.services.job_queue import job_queue
from app.services.pollinations import pollinations_service, PollinationsError
from app.utils.auth import get_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pollinations", tags=["Pollinations AI"])


def _audio_mime_type(fmt: str) -> str:
    fmt = (fmt or "mp3").lower()
    return {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "flac": "audio/flac",
        "opus": "audio/opus",
        "pcm": "audio/pcm",
        "aac": "audio/aac",
    }.get(fmt, f"audio/{fmt}")


class PollinationsTranscriptionResponse(BaseModel):
    """Response for audio transcription (sync or async)."""
    job_id: str | None = None
    transcription: str | None = None
    audio_format: str | None = None
    generation_time: float | None = None
    file_name: str | None = None
    file_size: int | None = None
    character_count: int | None = None


@router.post("/audio/tts")
async def text_to_speech(
    request: PollinationsAudioRequest,
    api_key: str = Depends(get_api_key)
):
    """Generate speech audio from text using Pollinations dedicated audio endpoints."""
    # Handle sync mode
    if request.sync:
        try:
            start_time = time.time()

            # Generate TTS audio
            audio_response = await pollinations_service.generate_audio_tts(
                text=request.text,
                voice=request.voice,
                model=request.model or "openai-audio",
                response_format=request.response_format,
                speed=request.speed,
            )

            # Handle different response types (URL or bytes)
            if isinstance(audio_response, str):
                # Response is a URL
                s3_url = audio_response
                file_size = None
            elif isinstance(audio_response, bytes):
                # Response is audio bytes, save to S3
                job_id = str(uuid.uuid4())
                filename = f"pollinations-tts-sync-{job_id}.mp3"
                s3_url = await pollinations_service.save_generated_content_to_s3(
                    audio_response,
                    filename,
                    _audio_mime_type(request.response_format)
                )
                file_size = len(audio_response)
            else:
                raise Exception("Unexpected response type from TTS generation")

            generation_time = time.time() - start_time

            return {
                "content_url": s3_url,
                "content_type": _audio_mime_type(request.response_format),
                "file_size": file_size,
                "generation_time": generation_time,
                "model_used": request.model,
                "voice_used": request.voice,
                "text": request.text,
                "text_length": len(request.text)
            }

        except HTTPException:
            raise
        except PollinationsError as e:
            logger.error(f"Griot AI error in sync TTS generation: {e}")
            raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error in sync TTS generation: {e}")
            raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

    # Handle async mode (default)
    job_id = str(uuid.uuid4())
    
    async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Wrapper function for job queue processing"""
        start_time = time.time()
        
        try:
            # Generate TTS audio using Pollinations dedicated endpoint
            audio_response = await pollinations_service.generate_audio_tts(
                text=data["text"],
                voice=data.get("voice", "default"),
                model=data.get("model", "openai-audio") or "openai-audio",
                response_format=data.get("response_format", "mp3"),
                speed=data.get("speed", 1.0),
            )
            
            # Handle different response types (URL or bytes)
            if isinstance(audio_response, str):
                # Response is a URL
                s3_url = audio_response
                file_size = None
            elif isinstance(audio_response, bytes):
                # Response is audio bytes, save to S3
                filename = f"pollinations-tts-{_job_id}.mp3"
                s3_url = await pollinations_service.save_generated_content_to_s3(
                    audio_response,
                    filename,
                    _audio_mime_type(data.get("response_format", "mp3"))
                )
                file_size = len(audio_response)
            else:
                raise Exception("Unexpected response type from TTS generation")
            
            generation_time = time.time() - start_time
            
            return {
                "content_url": s3_url,
                "content_type": _audio_mime_type(data.get("response_format", "mp3")),
                "file_size": file_size,
                "generation_time": generation_time,
                "model_used": data.get("model", "openai-audio"),
                "voice_used": data.get("voice", "default"),
                "text": data["text"],
                "text_length": len(data["text"])
            }
            
        except PollinationsError as e:
            logger.error(f"Griot AI error generating TTS audio: {e}")
            raise Exception(f"TTS generation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating TTS audio: {e}")
            raise Exception(f"TTS generation failed: {str(e)}")
    
    # Add job to queue
    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.POLLINATIONS_AUDIO,
        process_func=process_wrapper,
        data=request.model_dump()
    )
    
    return JobResponse(job_id=job_id)


@router.post("/audio/transcribe", response_model=PollinationsTranscriptionResponse)
async def transcribe_audio(
    request: PollinationsTranscriptionRequest,
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key)
):
    """Transcribe an audio file using Griot AI STT. Supports sync and async modes."""
    # Validate file type
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    # Determine audio format
    audio_format = request.audio_format  # Use from request model
    
    job_id = str(uuid.uuid4())
    
    async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Wrapper function for job queue processing"""
        start_time = time.time()
        
        try:
            # Transcribe audio using Griot AI
            result = await pollinations_service.transcribe_audio(
                audio_data=data["audio_data"]
            )
            
            # Extract transcription from result
            transcription = result.get("text", "") if isinstance(result, dict) else str(result)
            
            generation_time = time.time() - start_time
            
            return {
                "transcription": transcription,
                "audio_format": data["audio_format"],
                "generation_time": generation_time,
                "file_name": data.get("file_name"),
                "file_size": len(data["audio_data"]),
                "character_count": len(transcription)
            }
            
        except PollinationsError as e:
            logger.error(f"Griot AI error transcribing audio: {e}")
            raise Exception(f"Audio transcription failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise Exception(f"Audio transcription failed: {str(e)}")
    
    # Read file data
    audio_data = await file.read()
    
    # Handle synchronous mode
    if request.sync:
        # Transcribe audio directly and return result
        start_time = time.time()
        try:
            result = await pollinations_service.transcribe_audio(
                audio_data=audio_data
            )
            
            # Extract transcription from result
            transcription = result.get("text", "") if isinstance(result, dict) else str(result)
            
            generation_time = time.time() - start_time
            
            return PollinationsTranscriptionResponse(
                transcription=transcription,
                audio_format=audio_format,
                generation_time=generation_time,
                file_name=file.filename,
                file_size=len(audio_data),
                character_count=len(transcription)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in sync transcription: {e}")
            raise HTTPException(status_code=500, detail=f"Audio transcription failed: {str(e)}")
    
    # Handle asynchronous mode (default)
    # Add job to queue
    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.POLLINATIONS_AUDIO,
        process_func=process_wrapper,
        data={
            "audio_data": audio_data,
            "audio_format": audio_format,
            "question": request.question,
            "file_name": file.filename
        }
    )
    
    return PollinationsTranscriptionResponse(job_id=job_id)


@router.get("/models/audio")
async def list_audio_models():
    """List available Griot AI audio/speech models"""
    try:
        # Fetch from Griot AI service
        models = await pollinations_service.list_audio_models()

        return {"models": models}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching audio models: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch audio models")
