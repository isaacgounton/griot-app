"""Viral content skill — generate viral social media content from a video."""

import asyncio
import uuid
from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(
    name="viral_content",
    description="Generate viral social media content from a video (topics, threads, multi-platform posts, blog)",
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


async def _generate_viral_content(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.job_queue import job_queue
    from app.models import JobType
    from app.services.simone.simone_service import SimoneService

    url = args.get("url")
    if not url:
        return {"error": "url is required"}

    simone_service = SimoneService()

    job_params = {
        "url": url,
        "include_topics": args.get("include_topics", True),
        "include_x_thread": args.get("include_x_thread", True),
        "platforms": args.get("platforms", ["x", "linkedin", "instagram"]),
        "thread_config": {
            "max_posts": args.get("max_posts", 8),
            "character_limit": 280,
            "thread_style": args.get("thread_style", "viral"),
        },
    }

    job_id = str(uuid.uuid4())

    async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return await simone_service.process_video_with_enhanced_features(data)

    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.SIMONE_ENHANCED_PROCESSING,
        process_func=process_wrapper,
        data=job_params,
    )

    result = await _poll_job(job_id, timeout=600)
    if result.get("error"):
        return {**result, "job_id": job_id}

    return {**result.get("result", {}), "job_id": job_id}


skill.action(
    name="generate_viral_content",
    description=(
        "Generate viral social media content from a video URL. Produces topic identification, "
        "X/Twitter threads, multi-platform posts (X, LinkedIn, Instagram), and a blog post. "
        "Returns all generated content."
    ),
    handler=_generate_viral_content,
    properties={
        "url": {
            "type": "string",
            "description": "Video URL to process (YouTube, direct video URL, etc.)",
        },
        "platforms": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Social media platforms for post generation",
            "default": ["x", "linkedin", "instagram"],
        },
        "include_topics": {
            "type": "boolean",
            "description": "Include topic identification",
            "default": True,
        },
        "include_x_thread": {
            "type": "boolean",
            "description": "Include X/Twitter thread generation",
            "default": True,
        },
        "thread_style": {
            "type": "string",
            "enum": ["viral", "educational", "storytelling"],
            "description": "Style of X thread to generate",
            "default": "viral",
        },
        "max_posts": {
            "type": "integer",
            "description": "Maximum number of posts in the X thread",
            "default": 8,
        },
    },
    required=["url"],
)
