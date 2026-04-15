"""
FFmpeg compose routes for complex media processing operations.
"""
import uuid
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends

from app.models import (
    FFmpegComposeRequest, 
    FFmpegComposeResult,
    JobResponse,
    JobStatusResponse,
    JobStatus,
    JobType
)
from app.utils.auth import get_current_user
from app.services.job_queue import job_queue
from app.services.ffmpeg import ffmpeg_composer

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ffmpeg",
    tags=["System"],
    responses={
        400: {"description": "Bad Request - Invalid parameters"},
        401: {"description": "Unauthorized - Invalid API key"},
        500: {"description": "Internal Server Error"}
    }
)

@router.post(
    "/compose",
    summary="Compose and Execute FFmpeg Commands",
    description="Compose and execute FFmpeg commands from JSON configuration. "
                "Supports multiple inputs, filter graphs, stream mapping, metadata extraction, "
                "and sync/async processing. See /ffmpeg/compose/examples for usage examples.",
    operation_id="compose_ffmpeg_command"
)
async def compose_ffmpeg_command(
    request: FFmpegComposeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Compose and execute FFmpeg commands from JSON configuration.
    
    This endpoint processes complex FFmpeg operations including:
    - Multiple input files with individual options
    - Complex filter graphs and stream mapping
    - Multiple output configurations
    - Metadata extraction and thumbnail generation
    - Background processing with status tracking
    
    Args:
        request: FFmpeg compose request with sync parameter
        
    Returns:
        For sync=True: Direct processing result
        For sync=False: JobResponse with job_id for tracking progress
    """
    try:
        logger.info(f"Received FFmpeg compose request: {request.id}")
        
        # Validate the request using the composer service
        validation_errors = ffmpeg_composer.validate_request(request)
        if validation_errors:
            logger.warning(f"Request validation failed: {validation_errors}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Request validation failed",
                    "validation_errors": validation_errors,
                    "message": "Please check your request parameters and try again"
                }
            )
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Compose FFmpeg command for logging/debugging
        try:
            ffmpeg_command = ffmpeg_composer.compose_command(request)
            logger.info(f"Composed FFmpeg command for job {job_id}: {ffmpeg_command}")
        except Exception as e:
            logger.error(f"Failed to compose FFmpeg command: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Failed to compose FFmpeg command",
                    "message": str(e)
                }
            )
        
        # Prepare job parameters
        job_params = request.model_dump()
        
        # Handle sync vs async processing
        if request.sync:
            # Process FFmpeg composition synchronously
            try:
                result = await ffmpeg_composer.process_ffmpeg_compose("sync", job_params)
                logger.info(f"Completed synchronous FFmpeg composition for request {request.id}")
                return {
                    "job_id": None,
                    "status": "completed",
                    "result": result
                }
            except Exception as e:
                logger.error(f"Error in synchronous FFmpeg composition: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"FFmpeg composition failed: {str(e)}"
                )
        else:
            # Create async job (existing logic)
            # Generate job ID
            job_id = str(uuid.uuid4())
            
            # Create job
            await job_queue.add_job(
                job_id=job_id,
                job_type=JobType.FFMPEG_COMPOSE,
                process_func=ffmpeg_composer.process_ffmpeg_compose,
                data=job_params
            )
            
            logger.info(f"FFmpeg compose request {request.id} queued with job ID {job_id}")
            
            return JobResponse(job_id=job_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in FFmpeg compose endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred while processing your request"
            }
        )

@router.get(
    "/compose/examples",
    response_model=Dict[str, Any],
    summary="Get FFmpeg Compose Examples",
    description="Get example configurations for common FFmpeg operations (conversion, scaling, mixing, overlays).",
    operation_id="get_ffmpeg_compose_examples"
)
async def get_ffmpeg_compose_examples() -> Dict[str, Any]:
    """Get example configurations for FFmpeg compose operations."""
    return {
        "examples": {
            "video_conversion": {
                "description": "Convert video to different format with quality settings",
                "request": {
                    "id": "video-conversion-example",
                    "inputs": [
                        {
                            "file_url": "https://example.com/input.mov",
                            "options": []
                        }
                    ],
                    "outputs": [
                        {
                            "options": [
                                {"option": "-c:v", "argument": "libx264"},
                                {"option": "-crf", "argument": 23},
                                {"option": "-c:a", "argument": "aac"},
                                {"option": "-b:a", "argument": "128k"}
                            ]
                        }
                    ],
                    "metadata": {
                        "filesize": True,
                        "duration": True,
                        "bitrate": True,
                        "encoder": True,
                        "thumbnail": True
                    }
                }
            },
            "video_scaling": {
                "description": "Scale video to specific resolution using simple filter",
                "request": {
                    "id": "video-scaling-example",
                    "inputs": [
                        {
                            "file_url": "https://example.com/input.mp4",
                            "options": []
                        }
                    ],
                    "filters": [
                        {
                            "filter": "scale",
                            "arguments": ["1920", "1080"],
                            "type": "video"
                        }
                    ],
                    "use_simple_video_filter": True,
                    "outputs": [
                        {
                            "options": [
                                {"option": "-c:v", "argument": "libx264"},
                                {"option": "-c:a", "argument": "copy"}
                            ]
                        }
                    ]
                }
            },
            "audio_mixing": {
                "description": "Mix multiple audio files with volume adjustment",
                "request": {
                    "id": "audio-mixing-example",
                    "inputs": [
                        {
                            "file_url": "https://example.com/audio1.mp3",
                            "options": []
                        },
                        {
                            "file_url": "https://example.com/audio2.mp3",
                            "options": []
                        }
                    ],
                    "filters": [
                        {
                            "filter": "volume",
                            "arguments": ["0.8"],
                            "input_labels": ["0:a"],
                            "output_label": "a1"
                        },
                        {
                            "filter": "volume", 
                            "arguments": ["0.6"],
                            "input_labels": ["1:a"],
                            "output_label": "a2"
                        },
                        {
                            "filter": "amix",
                            "arguments": ["inputs=2"],
                            "input_labels": ["a1", "a2"],
                            "output_label": "mixed"
                        }
                    ],
                    "outputs": [
                        {
                            "options": [
                                {"option": "-c:a", "argument": "mp3"},
                                {"option": "-b:a", "argument": "192k"}
                            ],
                            "stream_mappings": ["[mixed]"]
                        }
                    ]
                }
            },
            "video_overlay": {
                "description": "Overlay one video on top of another with positioning",
                "request": {
                    "id": "video-overlay-example",
                    "inputs": [
                        {
                            "file_url": "https://example.com/background.mp4",
                            "options": []
                        },
                        {
                            "file_url": "https://example.com/overlay.mp4",
                            "options": []
                        }
                    ],
                    "filters": [
                        {
                            "filter": "scale",
                            "arguments": ["320", "240"],
                            "input_labels": ["1:v"],
                            "output_label": "overlay_scaled"
                        },
                        {
                            "filter": "overlay",
                            "arguments": ["10", "10"],
                            "input_labels": ["0:v", "overlay_scaled"],
                            "output_label": "output"
                        }
                    ],
                    "outputs": [
                        {
                            "options": [
                                {"option": "-c:v", "argument": "libx264"},
                                {"option": "-c:a", "argument": "copy"}
                            ],
                            "stream_mappings": ["[output]", "0:a"]
                        }
                    ]
                }
            },
            "stream_mapping": {
                "description": "Map specific streams from multiple inputs",
                "request": {
                    "id": "stream-mapping-example",
                    "inputs": [
                        {
                            "file_url": "https://example.com/video.mp4",
                            "options": []
                        },
                        {
                            "file_url": "https://example.com/audio.mp3",
                            "options": []
                        }
                    ],
                    "stream_mappings": ["0:v:0", "1:a:0"],
                    "outputs": [
                        {
                            "options": [
                                {"option": "-c:v", "argument": "copy"},
                                {"option": "-c:a", "argument": "aac"}
                            ]
                        }
                    ]
                }
            },
            "extract_segment": {
                "description": "Extract a segment from video with timing options",
                "request": {
                    "id": "extract-segment-example",
                    "inputs": [
                        {
                            "file_url": "https://example.com/long_video.mp4",
                            "options": [
                                {"option": "-ss", "argument": "00:01:30"},
                                {"option": "-t", "argument": "00:00:30"}
                            ]
                        }
                    ],
                    "outputs": [
                        {
                            "options": [
                                {"option": "-c:v", "argument": "libx264"},
                                {"option": "-c:a", "argument": "aac"}
                            ]
                        }
                    ],
                    "metadata": {
                        "duration": True,
                        "filesize": True,
                        "thumbnail": True
                    }
                }
            }
        },
        "tips": {
            "input_options": "Input-specific options (like -ss, -t) should be placed in the input's options array",
            "stream_mapping": "Use 0:v:0 for first video stream, 1:a:0 for first audio from second input, etc.",
            "complex_filters": "For complex operations, use filter graphs with input_labels and output_label",
            "simple_filters": "For single-input operations, use simple filters with use_simple_video_filter or use_simple_audio_filter",
            "global_options": "Use global_options for settings that apply to the entire FFmpeg command (like -y for overwrite)"
        }
    }

@router.get(
    "/compose/{job_id}",
    response_model=JobStatusResponse,
    summary="Get FFmpeg Compose Job Status",
    description="Get the status and results of an FFmpeg compose job by ID.",
    operation_id="get_ffmpeg_compose_status"
)
async def get_ffmpeg_compose_status(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> JobStatusResponse:
    """Get the status and results of an FFmpeg compose job."""
    try:
        # Get job status from job queue
        job_status = await job_queue.get_job_info(job_id)

        if not job_status:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Job not found",
                    "message": f"No job found with ID {job_id}"
                }
            )

        # Ensure status is a JobStatus enum
        status = job_status.status if isinstance(job_status.status, JobStatus) else JobStatus(job_status.status.lower())

        return JobStatusResponse(
            job_id=job_id,
            status=status,
            result=job_status.result,
            error=job_status.error
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get job status",
                "message": str(e)
            }
        )