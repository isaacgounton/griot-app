"""Video-to-blog skill — convert a video into a blog post."""

import asyncio
import uuid
from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(
    name="video_to_blog",
    description="Convert a video into a blog post with screenshots and optional social media posts",
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


async def _video_to_blog(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.job_queue import job_queue
    from app.models import JobType
    from app.services.simone.simone_service import SimoneService

    url = args.get("url")
    if not url:
        return {"error": "url is required"}

    simone_service = SimoneService()

    job_params = {
        "url": url,
        "platform": args.get("platform"),
    }

    job_id = str(uuid.uuid4())

    async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return await simone_service.process_video_to_blog(data)

    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.SIMONE_VIDEO_TO_BLOG,
        process_func=process_wrapper,
        data=job_params,
    )

    result = await _poll_job(job_id, timeout=600)
    if result.get("error"):
        return {**result, "job_id": job_id}

    return {**result.get("result", {}), "job_id": job_id}


skill.action(
    name="video_to_blog",
    description=(
        "Convert a video URL into a blog post with screenshots and key points. "
        "Optionally generates social media posts for a specified platform. "
        "Returns the blog content and media assets."
    ),
    handler=_video_to_blog,
    properties={
        "url": {
            "type": "string",
            "description": "Video URL to process (YouTube, direct video URL, etc.)",
        },
        "platform": {
            "type": "string",
            "enum": ["x", "linkedin", "instagram", "facebook"],
            "description": "Social media platform for additional post generation (optional)",
        },
    },
    required=["url"],
)
