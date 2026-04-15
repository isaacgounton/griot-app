"""
Comprehensive YouTube Shorts routes with all advanced features.
"""
import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from app.services.job_queue import job_queue
from app.models import JobType, JobResponse
from app.services.yt_shorts.shorts_service import youtube_shorts_service
from app.utils.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/yt-shorts", tags=["Content Tools"])

class ComprehensiveYouTubeShortsRequest(BaseModel):
    """Comprehensive YouTube Shorts generation request with all features."""

    # Basic parameters
    video_url: str = Field(description="YouTube video URL to generate shorts from")
    max_duration: int = Field(default=60, description="Maximum duration for the short in seconds")
    quality: str = Field(default="high", description="Video quality (low, medium, high, ultra)")
    output_format: str = Field(default="mp4", description="Output video format")

    # AI and cropping options
    use_ai_highlight: bool = Field(default=True, description="Use AI to detect best highlight segment")
    crop_to_vertical: bool = Field(default=True, description="Crop to vertical (9:16) format")
    speaker_tracking: bool = Field(default=True, description="Enable advanced speaker tracking")

    # Custom time segment (overrides AI if provided)
    custom_start_time: float | None = Field(default=None, description="Custom start time in seconds")
    custom_end_time: float | None = Field(default=None, description="Custom end time in seconds")

    # Sync parameter
    sync: bool = Field(default=False, description="If True, return response immediately. If False (default), create async job.")
    
    # Enhancement options
    enhance_audio: bool = Field(default=True, description="Enhance audio quality for speech")
    smooth_transitions: bool = Field(default=True, description="Add smooth fade transitions")
    create_thumbnail: bool = Field(default=True, description="Create preview thumbnail")
    
    # Advanced options
    target_resolution: str = Field(default="720x1280", description="Target resolution (WxH)")
    audio_enhancement_level: str = Field(default="speech", description="Audio enhancement type (speech, music, auto)")
    face_tracking_sensitivity: str = Field(default="medium", description="Face tracking sensitivity (low, medium, high)")
    
    # Cookie support for YouTube downloads
    cookies_url: str | None = Field(default=None, description="URL to download cookies file for YouTube access (required for restricted videos)")

class ComprehensiveYouTubeShortsResult(BaseModel):
    """Comprehensive YouTube Shorts generation result."""
    
    # Basic results
    url: str = Field(description="S3 URL of the generated short video")
    path: str = Field(description="S3 path of the generated short video")
    duration: float = Field(description="Duration of the generated short in seconds")
    
    # Original video info
    original_title: str = Field(description="Title of the original YouTube video")
    original_duration: float = Field(description="Duration of the original video in seconds")
    
    # Highlight information
    highlight_start: float = Field(description="Start time of the highlighted segment")
    highlight_end: float = Field(description="End time of the highlighted segment")
    ai_generated: bool = Field(description="Whether AI was used to select the highlight")
    
    # Processing information
    is_vertical: bool = Field(description="Whether the video was cropped to vertical format")
    quality: str = Field(description="Processing quality used")
    
    # Additional results
    thumbnail_url: str | None = Field(default=None, description="S3 URL of the preview thumbnail")
    processing_stats: dict = Field(description="Processing statistics and metadata")
    quality_check: dict = Field(description="Quality verification results")
    
    # Features used
    features_used: dict = Field(description="Features that were applied during processing")

@router.post("/create", status_code=status.HTTP_202_ACCEPTED)
async def create_comprehensive_shorts_job(
    request: ComprehensiveYouTubeShortsRequest,
    _: dict[str, Any] = Depends(get_current_user),
):
    """
    Create a YouTube Shorts generation job with AI-powered highlight detection,
    speaker tracking, vertical cropping, and audio enhancement.
    """
    try:
        # Validate YouTube URL
        video_url = request.video_url.strip()
        if not video_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video URL is required"
            )
        
        # Validate YouTube URL format
        youtube_domains = ["youtube.com", "youtu.be", "m.youtube.com", "www.youtube.com"]
        if not any(domain in video_url for domain in youtube_domains):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide a valid YouTube URL"
            )
        
        # Validate duration
        if request.max_duration < 5 or request.max_duration > 300:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Max duration must be between 5 and 300 seconds"
            )
        
        # Validate custom time segments
        if request.custom_start_time is not None and request.custom_end_time is not None:
            if request.custom_start_time < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Custom start time cannot be negative"
                )
            if request.custom_end_time <= request.custom_start_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Custom end time must be greater than start time"
                )
            if request.custom_end_time - request.custom_start_time > 300:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Custom segment duration cannot exceed 5 minutes"
                )
        
        # Validate quality
        valid_qualities = ["low", "medium", "high", "ultra"]
        if request.quality not in valid_qualities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid quality. Supported: {', '.join(valid_qualities)}"
            )
        
        # Validate output format
        valid_formats = ["mp4", "webm", "mov"]
        if request.output_format not in valid_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid output format. Supported: {', '.join(valid_formats)}"
            )
        
        # Validate resolution
        try:
            width, height = map(int, request.target_resolution.split('x'))
            if width < 360 or height < 640 or width > 1920 or height > 3840:
                raise ValueError("Resolution out of range")
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid resolution format. Use WxH (e.g., 720x1280)"
            )
        
        # Validate audio enhancement level
        valid_audio_levels = ["speech", "music", "auto"]
        if request.audio_enhancement_level not in valid_audio_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid audio enhancement level. Supported: {', '.join(valid_audio_levels)}"
            )
        
        # Validate face tracking sensitivity
        valid_sensitivities = ["low", "medium", "high"]
        if request.face_tracking_sensitivity not in valid_sensitivities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid face tracking sensitivity. Supported: {', '.join(valid_sensitivities)}"
            )
        
        # Create job
        job_id = str(uuid.uuid4())
        job_params = {
            # Basic parameters
            "video_url": video_url,
            "max_duration": request.max_duration,
            "quality": request.quality,
            "output_format": request.output_format,

            # AI and cropping options
            "use_ai_highlight": request.use_ai_highlight,
            "crop_to_vertical": request.crop_to_vertical,
            "speaker_tracking": request.speaker_tracking,

            # Custom time segments
            "custom_start_time": request.custom_start_time,
            "custom_end_time": request.custom_end_time,

            # Enhancement options
            "enhance_audio": request.enhance_audio,
            "smooth_transitions": request.smooth_transitions,
            "create_thumbnail": request.create_thumbnail,

            # Advanced options
            "target_resolution": request.target_resolution,
            "audio_enhancement_level": request.audio_enhancement_level,
            "face_tracking_sensitivity": request.face_tracking_sensitivity,

            # Cookie support
            "cookies_url": request.cookies_url
        }

        # Create wrapper function for job queue
        async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
            return await youtube_shorts_service.process_shorts_job(_job_id, data)

        # Handle synchronous mode
        if request.sync:
            result = await process_wrapper(job_id, job_params)
            return result

        # Queue the job (async mode, default)
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.YOUTUBE_SHORTS,
            process_func=process_wrapper,
            data=job_params
        )

        logger.info(f"Created comprehensive YouTube Shorts job {job_id} for: {video_url}")

        return JobResponse(job_id=job_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating comprehensive YouTube Shorts job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create comprehensive YouTube Shorts job"
        )

@router.get("/", status_code=status.HTTP_200_OK)
async def get_comprehensive_shorts_info():
    """Get information about the YouTube Shorts generation endpoint and its capabilities."""
    return {
        "endpoint": "/v1/yt-shorts/create",
        "method": "POST",
        "description": "AI-powered YouTube Shorts generation with highlight detection, speaker tracking, and audio enhancement",
        "version": "2.0",
        "features": [
            "AI-powered highlight detection",
            "Voice Activity Detection (VAD)",
            "DNN-based face detection",
            "Dynamic face-following crop",
            "Audio enhancement and speech optimization",
            "Automatic thumbnail generation",
        ],
        "supported_qualities": ["low", "medium", "high", "ultra"],
        "output_resolutions": ["720x1280", "1080x1920", "480x854"],
        "max_duration_seconds": 300,
    }

@router.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_video_for_shorts(
    video_url: str,
    _: dict[str, Any] = Depends(get_current_user),
):
    """Analyze a YouTube video and return recommendations for shorts generation."""
    try:
        # This would implement video analysis logic
        # For now, return a placeholder response
        return {
            "video_url": video_url,
            "analysis": {
                "duration": "12:34",
                "speaker_count": 2,
                "face_detection_confidence": 0.85,
                "audio_quality": "good",
                "recommended_segments": [
                    {"start": 45, "end": 105, "reason": "High engagement, clear speaker"},
                    {"start": 234, "end": 289, "reason": "Emotional peak, good audio"},
                    {"start": 456, "end": 516, "reason": "Key insight, face visible"}
                ],
                "optimization_suggestions": [
                    "Enable speaker tracking for better cropping",
                    "Use audio enhancement for clarity",
                    "Consider 45-60 second segments for optimal engagement"
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze video"
        )