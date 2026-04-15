"""YouTube Shorts skill — generate shorts from YouTube videos."""

import asyncio
import uuid
from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(
    name="yt_shorts",
    description="Generate YouTube Shorts with AI highlight detection and speaker tracking",
)


async def _poll_job(job_id: str, timeout: int = 600) -> dict[str, Any]:
    from app.services.job_queue import job_queue

    elapsed = 0
    interval = 5
    while elapsed < timeout:
        job_info = await job_queue.get_job(job_id)
        if job_info is None:
            return {"error": f"Job {job_id} not found"}

        status = getattr(job_info, "status", None)
        if status is not None:
            status_val = status.value if hasattr(status, "value") else str(status)
        else:
            status_val = "unknown"

        if status_val == "completed":
            return {"result": getattr(job_info, "result", None) or {}}
        elif status_val == "failed":
            return {"error": str(getattr(job_info, "error", "Job failed"))}

        await asyncio.sleep(interval)
        elapsed += interval

    return {"error": f"Job timed out after {timeout}s", "job_id": job_id}


async def _create_yt_short(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.job_queue import job_queue
    from app.models import JobType
    from app.services.yt_shorts.shorts_service import youtube_shorts_service

    video_url = args.get("video_url")
    if not video_url:
        return {"error": "video_url is required"}

    job_params = {
        "video_url": video_url,
        "max_duration": args.get("max_duration", 60),
        "quality": args.get("quality", "high"),
        "output_format": args.get("output_format", "mp4"),
        "use_ai_highlight": args.get("use_ai_highlight", True),
        "crop_to_vertical": args.get("crop_to_vertical", True),
        "speaker_tracking": args.get("speaker_tracking", True),
        "custom_start_time": args.get("custom_start_time"),
        "custom_end_time": args.get("custom_end_time"),
        "enhance_audio": args.get("enhance_audio", True),
        "smooth_transitions": args.get("smooth_transitions", True),
        "create_thumbnail": args.get("create_thumbnail", True),
        "target_resolution": args.get("target_resolution", "720x1280"),
        "audio_enhancement_level": args.get("audio_enhancement_level", "speech"),
        "face_tracking_sensitivity": args.get("face_tracking_sensitivity", "medium"),
        "cookies_url": args.get("cookies_url"),
    }

    job_id = str(uuid.uuid4())

    async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return await youtube_shorts_service.process_shorts_job(_job_id, data)

    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.YOUTUBE_SHORTS,
        process_func=process_wrapper,
        data=job_params,
    )

    result = await _poll_job(job_id, timeout=600)
    if result.get("error"):
        return {**result, "job_id": job_id}

    res = result.get("result", {})
    short_url = res.get("url") or res.get("video_url")
    if short_url:
        return {
            "short_url": short_url,
            "thumbnail_url": res.get("thumbnail_url"),
            "duration": res.get("duration"),
            "job_id": job_id,
        }
    return {"error": "Shorts generation completed but no URL returned", "job_id": job_id}


skill.action(
    name="create_youtube_short",
    description=(
        "Generate a YouTube Short from a YouTube video URL. Uses AI to detect the best "
        "highlight segment, crops to vertical format, and enhances audio. Returns the short URL."
    ),
    handler=_create_yt_short,
    properties={
        "video_url": {
            "type": "string",
            "description": "YouTube video URL",
        },
        "max_duration": {
            "type": "integer",
            "description": "Maximum short duration in seconds (5-300)",
            "default": 60,
        },
        "quality": {
            "type": "string",
            "enum": ["low", "medium", "high", "ultra"],
            "description": "Video quality",
            "default": "high",
        },
        "use_ai_highlight": {
            "type": "boolean",
            "description": "Use AI to find the best segment",
            "default": True,
        },
        "crop_to_vertical": {
            "type": "boolean",
            "description": "Crop to 9:16 vertical format",
            "default": True,
        },
        "speaker_tracking": {
            "type": "boolean",
            "description": "Enable face/speaker tracking for smart cropping",
            "default": True,
        },
        "custom_start_time": {
            "type": "number",
            "description": "Custom start time in seconds (overrides AI)",
        },
        "custom_end_time": {
            "type": "number",
            "description": "Custom end time in seconds (overrides AI)",
        },
    },
    required=["video_url"],
)
