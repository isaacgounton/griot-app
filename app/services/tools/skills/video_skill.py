"""Video skill — AI video generation."""

import asyncio
import uuid
from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="video", description="AI video generation from text prompts")


async def _poll_job(job_id: str, timeout: int = 180) -> dict[str, Any]:
    """Poll a job until completion or timeout."""
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
            result = getattr(job_info, "result", None)
            return {"result": result or {}}
        elif status_val == "failed":
            error = getattr(job_info, "error", "Job failed")
            return {"error": str(error)}

        await asyncio.sleep(interval)
        elapsed += interval

    return {"error": f"Job timed out after {timeout}s"}


async def _generate_video(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.job_queue import job_queue
    from app.models import JobType
    from app.routes.video.generate import process_video_generation_wrapper

    job_id = str(uuid.uuid4())
    provider = args.get("provider", "wavespeed")

    data: dict[str, Any] = {
        "prompt": args["prompt"],
        "provider": provider,
        "negative_prompt": args.get("negative_prompt", ""),
        "width": args.get("width", 704),
        "height": args.get("height", 480),
    }

    if provider == "wavespeed":
        data["duration"] = args.get("duration", 5)
    elif provider == "pollinations":
        data["video_model"] = args.get("video_model", "veo")
        data["audio"] = args.get("audio", False)
        data["duration"] = args.get("duration", 5)
    else:
        data["num_frames"] = args.get("num_frames", 150)
        data["num_inference_steps"] = args.get("num_inference_steps", 200)
        data["guidance_scale"] = args.get("guidance_scale", 4.5)

    if args.get("seed") is not None:
        data["seed"] = args["seed"]

    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.VIDEO_GENERATION,
        process_func=process_video_generation_wrapper,
        data=data,
    )

    result = await _poll_job(job_id, timeout=180)
    if result.get("error"):
        return {**result, "job_id": job_id}

    video_url = result.get("result", {}).get("video_url")
    if video_url:
        return {"video_url": video_url, "prompt": args["prompt"], "provider": provider}
    return {"error": "Video generation completed but no URL returned", "job_id": job_id}


skill.action(
    name="generate_video",
    description="Generate a short AI video from a text description. Returns the video URL.",
    handler=_generate_video,
    properties={
        "prompt": {
            "type": "string",
            "description": "Description of the video to generate",
        },
        "provider": {
            "type": "string",
            "enum": ["wavespeed", "pollinations", "ltx_video", "comfyui"],
            "description": "Video generation provider",
            "default": "wavespeed",
        },
        "width": {
            "type": "integer",
            "description": "Video width in pixels (256-1024, divisible by 32)",
            "default": 704,
        },
        "height": {
            "type": "integer",
            "description": "Video height in pixels (256-1024, divisible by 32)",
            "default": 480,
        },
        "duration": {
            "type": "integer",
            "description": "Video duration in seconds (5 or 8 for wavespeed)",
            "default": 5,
        },
        "negative_prompt": {
            "type": "string",
            "description": "What to avoid in the video",
        },
        "seed": {
            "type": "integer",
            "description": "Seed for reproducible results",
        },
    },
    required=["prompt"],
)
