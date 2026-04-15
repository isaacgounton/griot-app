"""
Routes for media transcription using Whisper.
"""
import os
import uuid
import tempfile
import logging
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status

from app.models import JobResponse, MediaTranscriptionRequest, JobType
from app.services.job_queue import job_queue
from app.services.media.transcription import get_transcription_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcriptions", tags=["Audio"])


async def process_transcription(job_id: str, params: dict[str, Any]) -> dict[str, Any]:
    """Process a transcription job using the transcription service."""
    return await get_transcription_service().process_media_transcription(job_id, params)


@router.post("")
async def create_transcriptions_job(request: MediaTranscriptionRequest):
    """Transcribe media using Whisper. Supports text, SRT, word timestamps, and segment output."""
    try:
        # Create job parameters
        job_params = {
            "media_url": str(request.media_url),
            "include_text": request.include_text,
            "include_srt": request.include_srt,
            "word_timestamps": request.word_timestamps,
            "include_segments": request.include_segments,
            "language": request.language,
            "max_words_per_line": request.max_words_per_line,
            "beam_size": request.beam_size,
            "model_size": request.model_size or "base",
            "temperature": request.temperature or 0.0,
            "initial_prompt": request.initial_prompt,
        }

        # Handle sync vs async processing
        if request.sync:
            # Process transcription synchronously
            try:
                result = await get_transcription_service().process_media_transcription("sync", job_params)
                logger.info("Completed synchronous media transcription")
                return {
                    "job_id": None,
                    "status": "completed",
                    "result": result
                }
            except Exception as e:
                logger.error(f"Error in synchronous transcription: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Transcription failed: {str(e)}"
                )
        else:
            # Create async job (existing logic)
            job_id = str(uuid.uuid4())

            await job_queue.add_job(
                job_id=job_id,
                job_type=JobType.MEDIA_TRANSCRIPTION,
                process_func=process_transcription,
                data=job_params
            )

            logger.info(f"Created media transcription job: {job_id}")

            return JobResponse(job_id=job_id)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/upload")
async def create_transcription_upload_job(
    file: UploadFile = File(..., description="Audio/video file to transcribe"),
    include_text: bool = Form(True),
    include_srt: bool = Form(True),
    word_timestamps: bool = Form(False),
    include_segments: bool = Form(False),
    language: Optional[str] = Form(None),
    max_words_per_line: int = Form(10),
    beam_size: int = Form(5),
    model_size: str = Form("base"),
    temperature: float = Form(0.0),
    initial_prompt: Optional[str] = Form(None),
):
    """Transcribe an uploaded audio/video file using Whisper.

    Upload a file directly instead of providing a URL. Supports MP3, WAV, M4A,
    MP4, MOV, AVI, MKV, WebM, FLAC, OGG.
    """
    tmp_path = None
    try:
        # Save uploaded file to temp location
        suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir="temp") as tmp:
            tmp_path = tmp.name
            content = await file.read()
            tmp.write(content)

        logger.info(f"Saved uploaded file ({len(content)} bytes) to {tmp_path}")

        # Create job parameters with file_path instead of media_url
        job_params: dict[str, Any] = {
            "file_path": tmp_path,
            "include_text": include_text,
            "include_srt": include_srt,
            "word_timestamps": word_timestamps,
            "include_segments": include_segments,
            "language": language,
            "max_words_per_line": max_words_per_line,
            "beam_size": beam_size,
            "model_size": model_size,
            "temperature": temperature,
            "initial_prompt": initial_prompt,
        }

        job_id = str(uuid.uuid4())

        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.MEDIA_TRANSCRIPTION,
            process_func=process_transcription,
            data=job_params
        )

        logger.info(f"Created file upload transcription job: {job_id}")
        return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        # Clean up temp file on error
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Upload transcription failed: {str(e)}")
