"""Image skill — AI image generation."""

import asyncio
import uuid
from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="image", description="AI image generation from text prompts")


async def _poll_job(job_id: str, timeout: int = 120) -> dict[str, Any]:
    from app.services.job_queue import job_queue

    elapsed = 0
    interval = 2
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


async def _generate_image(args: dict[str, Any]) -> dict[str, Any]:
    provider = args.get("provider", "pollinations")

    if provider == "pollinations":
        from app.services.pollinations.pollinations_service import pollinations_service

        result = await pollinations_service.generate_image(
            prompt=args["prompt"],
            width=args.get("width", 1024),
            height=args.get("height", 1024),
            model=args.get("model", "flux"),
        )
        image_url = result.get("url") or result.get("image_url")
        if not image_url:
            return {"error": "Image generation returned no URL"}
        return {"image_url": image_url, "prompt": args["prompt"], "provider": "pollinations"}

    else:
        # Together.ai or Modal — use the job-based route
        from app.services.job_queue import job_queue
        from app.models import JobType
        from app.routes.image.generate import process_image_generation_wrapper

        job_id = str(uuid.uuid4())
        data = {
            "prompt": args["prompt"],
            "provider": provider,
            "model": args.get("model", "black-forest-labs/FLUX.1-schnell"),
            "width": args.get("width", 576),
            "height": args.get("height", 1024),
            "steps": args.get("steps", 4),
        }

        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.IMAGE_GENERATION,
            process_func=process_image_generation_wrapper,
            data=data,
        )

        result = await _poll_job(job_id, timeout=120)
        if result.get("error"):
            return {**result, "job_id": job_id}

        image_url = result.get("result", {}).get("image_url")
        if image_url:
            return {"image_url": image_url, "prompt": args["prompt"], "provider": provider}
        return {"error": "Image generation completed but no URL returned", "job_id": job_id}


skill.action(
    name="generate_image",
    description="Generate an image from a text description. Returns the image URL.",
    handler=_generate_image,
    properties={
        "prompt": {
            "type": "string",
            "description": "Detailed description of the image to generate",
        },
        "provider": {
            "type": "string",
            "enum": ["pollinations", "together", "modal_image"],
            "description": "Image generation provider",
            "default": "pollinations",
        },
        "model": {
            "type": "string",
            "description": "Model name (e.g., 'flux' for Pollinations, 'black-forest-labs/FLUX.1-schnell' for Together)",
        },
        "width": {
            "type": "integer",
            "description": "Image width in pixels (256-2048)",
            "default": 1024,
        },
        "height": {
            "type": "integer",
            "description": "Image height in pixels (256-2048)",
            "default": 1024,
        },
    },
    required=["prompt"],
)
