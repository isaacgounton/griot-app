from fastapi import APIRouter, HTTPException, Depends, status, Response
from pydantic import BaseModel, HttpUrl
from typing import Any
import logging

from app.services.job_queue import job_queue
from app.services.media.metadata import metadata_service
from app.models import JobType, JobResponse
from app.utils.auth import get_current_user
import uuid

router = APIRouter(tags=["Media"])
logger = logging.getLogger(__name__)

class MetadataRequest(BaseModel):
    media_url: HttpUrl
    sync: bool = False

class MetadataResponse(BaseModel):
    filesize: int
    filesize_mb: float
    duration: float | None = None
    duration_formatted: str | None = None
    format: str | None = None
    overall_bitrate: int | None = None
    overall_bitrate_mbps: float | None = None
    has_video: bool
    has_audio: bool
    
    # Video properties (if present)
    video_codec: str | None = None
    video_codec_long: str | None = None
    width: int | None = None
    height: int | None = None
    resolution: str | None = None
    fps: float | None = None
    video_bitrate: int | None = None
    video_bitrate_mbps: float | None = None
    pixel_format: str | None = None
    
    # Audio properties (if present)
    audio_codec: str | None = None
    audio_codec_long: str | None = None
    audio_channels: int | None = None
    audio_sample_rate: int | None = None
    audio_sample_rate_khz: float | None = None
    audio_bitrate: int | None = None
    audio_bitrate_kbps: float | None = None

@router.post("/metadata")
async def extract_metadata(
    request: MetadataRequest,
    response: Response,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Extract comprehensive metadata from a media file including video/audio codec, resolution, bitrate, and duration."""
    # If sync requested, process immediately and return metadata
    if request.sync:
        try:
            metadata = await metadata_service.get_metadata(str(request.media_url), "sync")
            # Return metadata directly with 200 OK
            response.status_code = status.HTTP_200_OK
            return metadata
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Synchronous metadata extraction failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to process request: {str(e)}")

    # Otherwise create an async job and return a job id
    job_id = str(uuid.uuid4())
    try:
        async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
            media_url = data["media_url"]
            metadata = await metadata_service.get_metadata(media_url, _job_id)
            return metadata

        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.METADATA_EXTRACTION,
            process_func=process_wrapper,
            data={"media_url": str(request.media_url)}
        )

        response.status_code = status.HTTP_202_ACCEPTED
        return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create metadata extraction job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process request: {str(e)}")