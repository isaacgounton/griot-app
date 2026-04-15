"""Clips skill — extract video clips using time segments or AI search."""

import asyncio
import uuid
from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="clips", description="Extract video clips using manual time segments or AI-powered search")


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


async def _extract_clips(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.job_queue import job_queue
    from app.models import JobType
    from app.services.video.clips_service import video_clips_service

    video_url = args.get("video_url")
    if not video_url:
        return {"error": "video_url is required"}

    segments = args.get("segments")
    ai_query = args.get("ai_query")

    if not segments and not ai_query:
        return {"error": "Either 'segments' or 'ai_query' must be provided"}
    if segments and ai_query:
        return {"error": "Cannot use both 'segments' and 'ai_query'"}

    job_params: dict[str, Any] = {
        "video_url": video_url,
        "output_format": args.get("output_format", "mp4"),
        "quality": args.get("quality", "medium"),
    }

    if segments:
        job_params["segments"] = [
            {"start": s["start"], "end": s["end"], "name": s.get("name")}
            for s in segments
        ]
    else:
        job_params["ai_query"] = ai_query
        job_params["max_clips"] = args.get("max_clips", 5)

    job_id = str(uuid.uuid4())
    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.VIDEO_CLIPS,
        process_func=video_clips_service.process_clips_job,
        data=job_params,
    )

    result = await _poll_job(job_id, timeout=300)
    if result.get("error"):
        return {**result, "job_id": job_id}

    return {**result.get("result", {}), "job_id": job_id}


skill.action(
    name="extract_clips",
    description=(
        "Extract clips from a video using manual time segments or AI-powered content search. "
        "Returns URLs of the extracted clips."
    ),
    handler=_extract_clips,
    properties={
        "video_url": {
            "type": "string",
            "description": "URL of the source video",
        },
        "segments": {
            "type": "array",
            "description": "Manual time segments to extract",
            "items": {
                "type": "object",
                "properties": {
                    "start": {"type": "number", "description": "Start time in seconds"},
                    "end": {"type": "number", "description": "End time in seconds"},
                    "name": {"type": "string", "description": "Optional clip name"},
                },
                "required": ["start", "end"],
            },
        },
        "ai_query": {
            "type": "string",
            "description": "AI search query to find relevant segments (e.g., 'funny moments')",
        },
        "max_clips": {
            "type": "integer",
            "description": "Max clips to extract when using AI search",
            "default": 5,
        },
        "quality": {
            "type": "string",
            "enum": ["low", "medium", "high"],
            "description": "Output quality",
            "default": "medium",
        },
        "output_format": {
            "type": "string",
            "enum": ["mp4", "webm", "mov"],
            "description": "Output video format",
            "default": "mp4",
        },
    },
    required=["video_url"],
)
