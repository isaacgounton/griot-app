"""Pollinations AI video analysis routes."""

import base64
import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.models import (
    JobResponse,
    JobType,
    PollinationsVideoAnalysisRequest,
)
from app.services.job_queue import job_queue
from app.services.pollinations import pollinations_service
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pollinations", tags=["Pollinations AI"])

MAX_VIDEO_ANALYSIS_UPLOAD_BYTES = 25 * 1024 * 1024


def _video_format_from_content_type(content_type: str | None) -> str:
    if not content_type:
        return "mp4"
    return content_type.split("/", 1)[1].split(";", 1)[0] or "mp4"


@router.post("/video/analyze", response_model=JobResponse)
async def analyze_video(
    request: PollinationsVideoAnalysisRequest,
    _: dict[str, Any] = Depends(get_current_user),
):
    """Analyze a video URL using Pollinations chat completions."""
    if not request.video_url:
        raise HTTPException(status_code=422, detail="video_url is required")

    job_id = str(uuid.uuid4())

    async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
        start_time = time.time()

        try:
            video_url = data["video_url"]
            question = data.get("question", "Describe this video in detail")
            model = data.get("model", "openai")

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {"type": "video_url", "video_url": {"url": video_url}},
                    ],
                }
            ]

            response_text = await pollinations_service.generate_text_chat(
                messages=messages,
                model=model,
            )

            return {
                "text": response_text,
                "model_used": model,
                "generation_time": time.time() - start_time,
                "video_url": video_url,
            }

        except Exception as e:
            logger.error(f"Error analyzing video: {e}")
            raise Exception(f"Video analysis failed: {str(e)}")

    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.POLLINATIONS_VIDEO_ANALYSIS,
        process_func=process_wrapper,
        data=request.model_dump(),
    )

    return JobResponse(job_id=job_id)


@router.post("/video/analyze-upload", response_model=JobResponse)
async def analyze_video_upload(
    file: UploadFile = File(...),
    question: str = "Describe this video in detail",
    model: str = "openai",
    _: dict[str, Any] = Depends(get_current_user),
):
    """Analyze an uploaded video using Pollinations chat completions."""
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")

    file_data = await file.read()
    if len(file_data) > MAX_VIDEO_ANALYSIS_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File too large. Please use a video smaller than 25MB or analyze by URL.",
        )

    job_id = str(uuid.uuid4())

    async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
        start_time = time.time()

        try:
            video_data_b64 = data["video_data"]
            content_type = data.get("file_content_type", "video/mp4")
            format_hint = data.get("video_format", _video_format_from_content_type(content_type))
            question_text = data.get("question", "Describe this video in detail")
            model_name = data.get("model", "openai")

            file_url = None
            try:
                file_url = await pollinations_service.save_generated_content_to_s3(
                    base64.b64decode(video_data_b64),
                    data.get("file_name") or f"video-analysis-{_job_id}.{format_hint}",
                    content_type,
                )
            except Exception as e:
                logger.warning(f"Failed to save uploaded video to S3 for job {_job_id}: {e}")

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question_text},
                        {
                            "type": "input_video",
                            "input_video": {
                                "data": video_data_b64,
                                "format": format_hint,
                            },
                        },
                    ],
                }
            ]

            response_text = await pollinations_service.generate_text_chat(
                messages=messages,
                model=model_name,
            )

            result: dict[str, Any] = {
                "text": response_text,
                "model_used": model_name,
                "generation_time": time.time() - start_time,
            }
            if file_url:
                result["video_url"] = file_url
            return result

        except Exception as e:
            logger.error(f"Error analyzing uploaded video: {e}")
            raise Exception(f"Video analysis failed: {str(e)}")

    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.POLLINATIONS_VIDEO_ANALYSIS,
        process_func=process_wrapper,
        data={
            "video_data": base64.b64encode(file_data).decode("utf-8"),
            "question": question,
            "model": model,
            "file_name": file.filename,
            "file_content_type": file.content_type,
            "video_format": _video_format_from_content_type(file.content_type),
        },
    )

    return JobResponse(job_id=job_id)
