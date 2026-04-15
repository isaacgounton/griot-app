"""
Routes for YouTube transcript generation.
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.models import YouTubeTranscriptRequest, JobResponse, JobType
from app.services.media.youtube_transcript_service import youtube_transcript_service
from app.services.job_queue import job_queue
from app.utils.auth import get_current_user
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Media"])


@router.post("/youtube-transcripts")
async def generate_youtube_transcript(
    request: YouTubeTranscriptRequest,
    _: dict[str, Any] = Depends(get_current_user),  # API key validation (not used in function)
):
    """Extract transcripts from YouTube videos with optional translation and multiple output formats (text, SRT, VTT, JSON)."""
    try:
        # Validate YouTube URL
        video_url = str(request.video_url)
        if "youtube.com" not in video_url and "youtu.be" not in video_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid YouTube URL. Please provide a valid YouTube video URL."
            )
        
        # Validate format
        valid_formats = ["text", "srt", "vtt", "json"]
        if request.format and request.format not in valid_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid format. Supported formats: {', '.join(valid_formats)}"
            )
        
        # Handle sync vs async processing
        if request.sync:
            # Process transcript generation synchronously
            try:
                job_data = {
                    "video_url": video_url,
                    "languages": request.languages,
                    "translate_to": request.translate_to,
                    "format": request.format or "text"
                }
                
                result = await youtube_transcript_service.process_transcript_generation(job_data)
                
                logger.info(f"Completed synchronous YouTube transcript for video: {video_url}")
                
                return {
                    "job_id": None,
                    "status": "completed",
                    "result": result
                }
            except Exception as e:
                logger.error(f"Error in synchronous YouTube transcript: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Transcript generation failed: {str(e)}"
                )
        else:
            # Create async job (existing logic)
            job_id = str(uuid.uuid4())
            job_data = {
                "video_url": video_url,
                "languages": request.languages,
                "translate_to": request.translate_to,
                "format": request.format or "text"
            }
            
            # Create a wrapper function that matches the expected signature
            async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
                return await youtube_transcript_service.process_transcript_generation(data)
            
            # Queue the job using consistent pattern
            await job_queue.add_job(
                job_id=job_id,
                job_type=JobType.YOUTUBE_TRANSCRIPT,
                process_func=process_wrapper,
                data=job_data
            )
            
            logger.info(f"Created YouTube transcript job {job_id} for video: {video_url}")
            
            return JobResponse(job_id=job_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating YouTube transcript job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create YouTube transcript job"
        )
