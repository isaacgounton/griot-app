"""
Routes for silence/speech detection in media files.
"""
import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status, Depends

from app.utils.auth import get_current_user
from app.services.job_queue import job_queue
from app.models import JobType, JobResponse, MediaSilenceRequest, MediaAnalyzeRequest
from app.services.media.silence_service import silence_service

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/silence", tags=["Media"])

@router.post("/", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_silence_detection_job(
    request: MediaSilenceRequest,
    current_user: dict[str, Any] = Depends(get_current_user)
):
    """Detect silence or speech segments in media files. Supports VAD-based and FFmpeg-based detection."""
    # Validate input
    if not request.media_url:
        raise HTTPException(status_code=400, detail="No media URL provided")
    
    # Create job data
    job_data = {
        "media_url": str(request.media_url),
        "start": request.start,
        "end": request.end,
        "noise": request.noise,
        "duration": request.duration,
        "mono": request.mono,
        "volume_threshold": request.volume_threshold,
        "use_advanced_vad": request.use_advanced_vad,
        "min_speech_duration": request.min_speech_duration,
        "speech_padding_ms": request.speech_padding_ms,
        "silence_padding_ms": request.silence_padding_ms
    }
    
    # Create a job
    job_id = str(uuid.uuid4())
    
    try:
        # Create wrapper function to match job queue signature
        async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
            return await silence_service.process_silence_job(_job_id, data)
        
        # Add job to queue
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.MEDIA_SILENCE_DETECTION,
            process_func=process_wrapper,
            data=job_data
        )
        
        logger.info(f"Created silence detection job: {job_id}")
        
        # Return the response with the job_id and status
        return JobResponse(
            job_id=job_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create silence detection job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create silence detection job: {str(e)}"
        )

@router.post("/analyze", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_audio_analysis_job(
    request: MediaAnalyzeRequest,
    current_user: dict[str, Any] = Depends(get_current_user)
):
    """Analyze audio characteristics (quality, dynamic range, noise floor) and recommend optimal processing parameters."""
    # Validate input
    if not request.media_url:
        raise HTTPException(status_code=400, detail="No media URL provided")
    
    # Create job data
    job_data = {
        "media_url": str(request.media_url)
    }
    
    # Create a job
    job_id = str(uuid.uuid4())
    
    try:
        # Create wrapper function to match job queue signature
        async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
            return await silence_service.process_analyze_job(_job_id, data)
        
        # Add job to queue
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.MEDIA_AUDIO_ANALYSIS,
            process_func=process_wrapper,
            data=job_data
        )
        
        logger.info(f"Created audio analysis job: {job_id}")
        
        # Return the response with the job_id and status
        return JobResponse(
            job_id=job_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create audio analysis job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create audio analysis job: {str(e)}"
        )