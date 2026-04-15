"""Add-audio skill — add audio tracks to videos."""

import asyncio
import uuid
from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="add_audio", description="Add audio to videos with sync modes and fade effects")


async def _poll_job(job_id: str, timeout: int = 180) -> dict[str, Any]:
    from app.services.job_queue import job_queue

    elapsed = 0
    interval = 3
    while elapsed < timeout:
        job_info = await job_queue.get_job(job_id)
        if job_info is None:
            return {"error": f"Job {job_id} not found"}

        status = getattr(job_info, "status", None)
        status_val = status.value if hasattr(status, "value") else str(status) if status else "unknown"

        if status_val == "completed":
            return {"result": getattr(job_info, "result", None) or {}}
        elif status_val == "failed":
            return {"error": str(getattr(job_info, "error", "Job failed"))}

        await asyncio.sleep(interval)
        elapsed += interval

    return {"error": f"Job timed out after {timeout}s", "job_id": job_id}


async def _add_audio_to_video(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.job_queue import job_queue
    from app.models import JobType
    from app.services.video.add_audio import add_audio_service

    video_url = args.get("video_url")
    audio_url = args.get("audio_url")
    if not video_url:
        return {"error": "video_url is required"}
    if not audio_url:
        return {"error": "audio_url is required"}

    job_data = {
        "video_url": video_url,
        "audio_url": audio_url,
        "video_volume": args.get("video_volume", 1.0),
        "audio_volume": args.get("audio_volume", 1.0),
        "sync_mode": args.get("sync_mode", "replace"),
        "match_length": args.get("match_length", "video"),
        "fade_in_duration": args.get("fade_in_duration", 0.0),
        "fade_out_duration": args.get("fade_out_duration", 0.0),
    }

    job_id = str(uuid.uuid4())
    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.VIDEO_ADD_AUDIO,
        process_func=add_audio_service.process_job,
        data=job_data,
    )

    result = await _poll_job(job_id, timeout=180)
    if result.get("error"):
        return {**result, "job_id": job_id}

    res = result.get("result", {})
    output_url = res.get("video_url") or res.get("output_url")
    if output_url:
        return {"video_url": output_url, "job_id": job_id}
    return {"error": "Add audio completed but no URL returned", "job_id": job_id}


skill.action(
    name="add_audio_to_video",
    description=(
        "Add an audio track to a video. Supports replace, mix, and overlay sync modes "
        "with configurable volumes and fade effects. Returns the output video URL."
    ),
    handler=_add_audio_to_video,
    properties={
        "video_url": {
            "type": "string",
            "description": "URL of the video",
        },
        "audio_url": {
            "type": "string",
            "description": "URL of the audio to add",
        },
        "sync_mode": {
            "type": "string",
            "enum": ["replace", "mix", "overlay"],
            "description": "How to combine audio: replace original, mix together, or overlay",
            "default": "replace",
        },
        "video_volume": {
            "type": "number",
            "description": "Original video volume (0.0-2.0)",
            "default": 1.0,
        },
        "audio_volume": {
            "type": "number",
            "description": "New audio volume (0.0-2.0)",
            "default": 1.0,
        },
        "match_length": {
            "type": "string",
            "enum": ["audio", "video"],
            "description": "Match output duration to audio or video length",
            "default": "video",
        },
        "fade_in_duration": {
            "type": "number",
            "description": "Fade-in duration in seconds",
            "default": 0.0,
        },
        "fade_out_duration": {
            "type": "number",
            "description": "Fade-out duration in seconds",
            "default": 0.0,
        },
    },
    required=["video_url", "audio_url"],
)
