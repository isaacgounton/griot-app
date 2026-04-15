"""
Routes for adding audio to videos.
"""
import logging
import uuid

from fastapi import APIRouter, HTTPException, status, Response

from app.services.job_queue import job_queue
from app.models import JobType, JobResponse, VideoAddAudioRequest
from app.services.video.add_audio import add_audio_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/add-audio", tags=["Video"])


@router.post("")
async def create_add_audio_job(request: VideoAddAudioRequest, response: Response):
    """Add audio to a video with configurable sync mode (replace, mix, overlay) and fade effects."""
    if not request.video_url:
        raise HTTPException(status_code=400, detail="No video URL provided")

    if not request.audio_url:
        raise HTTPException(status_code=400, detail="No audio URL provided")

    valid_sync_modes = ["replace", "mix", "overlay"]
    if request.sync_mode not in valid_sync_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sync mode. Supported modes: {', '.join(valid_sync_modes)}"
        )

    if request.match_length not in ["audio", "video"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid match_length option. Must be either 'audio' or 'video'"
        )

    job_data = {
        "video_url": request.video_url,
        "audio_url": request.audio_url,
        "video_volume": request.video_volume,
        "audio_volume": request.audio_volume,
        "sync_mode": request.sync_mode,
        "match_length": request.match_length,
        "fade_in_duration": request.fade_in_duration,
        "fade_out_duration": request.fade_out_duration
    }

    if request.sync:
        try:
            result = await add_audio_service.process_job("sync", job_data)
            logger.info("Completed synchronous add audio processing")
            response.status_code = status.HTTP_200_OK
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in synchronous add audio processing: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Add audio processing failed: {str(e)}"
            )
    else:
        job_id = str(uuid.uuid4())

        try:
            await job_queue.add_job(
                job_id=job_id,
                job_type=JobType.VIDEO_ADD_AUDIO,
                process_func=add_audio_service.process_job,
                data=job_data
            )

            logger.info(f"Created video add audio job: {job_id}")
            response.status_code = status.HTTP_202_ACCEPTED
            return JobResponse(job_id=job_id)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create add audio job: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create add audio job: {str(e)}"
            )
