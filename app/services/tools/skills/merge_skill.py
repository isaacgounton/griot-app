"""Merge skill — concatenate multiple videos into one."""

import asyncio
import uuid
from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="merge", description="Concatenate multiple videos into one with transition effects")


async def _poll_job(job_id: str, timeout: int = 300) -> dict[str, Any]:
    from app.services.job_queue import job_queue

    elapsed = 0
    interval = 3
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


async def _merge_videos(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.job_queue import job_queue
    from app.models import JobType
    from app.services.video.concatenate import concatenation_service

    video_urls = args.get("video_urls", [])
    if len(video_urls) < 2:
        return {"error": "At least 2 video URLs are required"}

    job_data = {
        "video_urls": video_urls,
        "output_format": f".{args.get('output_format', 'mp4')}",
        "transition": args.get("transition", "none"),
        "transition_duration": args.get("transition_duration", 1.0),
        "max_segment_duration": args.get("max_segment_duration"),
        "total_duration_limit": args.get("total_duration_limit"),
    }

    job_id = str(uuid.uuid4())
    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.VIDEO_CONCATENATION,
        process_func=concatenation_service.process_job,
        data=job_data,
    )

    result = await _poll_job(job_id, timeout=300)
    if result.get("error"):
        return {**result, "job_id": job_id}

    res = result.get("result", {})
    output_url = res.get("video_url") or res.get("output_url")
    if output_url:
        return {"video_url": output_url, "videos_merged": len(video_urls), "job_id": job_id}
    return {"error": "Merge completed but no URL returned", "job_id": job_id}


skill.action(
    name="merge_videos",
    description=(
        "Concatenate multiple videos into one with optional transition effects "
        "(fade, dissolve, slide, wipe). Returns the merged video URL."
    ),
    handler=_merge_videos,
    properties={
        "video_urls": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of video URLs to concatenate (minimum 2)",
        },
        "transition": {
            "type": "string",
            "enum": ["none", "fade", "dissolve", "slide", "wipe"],
            "description": "Transition effect between videos",
            "default": "none",
        },
        "transition_duration": {
            "type": "number",
            "description": "Transition duration in seconds",
            "default": 1.0,
        },
        "output_format": {
            "type": "string",
            "enum": ["mp4", "webm", "mov"],
            "description": "Output video format",
            "default": "mp4",
        },
    },
    required=["video_urls"],
)
