"""Convert skill — convert media between formats using FFmpeg."""

import asyncio
import uuid
from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="convert", description="Convert media between audio, video, and image formats")


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


async def _convert_media(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.job_queue import job_queue
    from app.models import JobType
    from app.services.media.media_conversion_service import media_conversion_service

    input_url = args.get("input_url")
    output_format = args.get("output_format")

    if not input_url:
        return {"error": "input_url is required"}
    if not output_format:
        return {"error": "output_format is required"}

    job_data = {
        "input_type": "url",
        "input_url": input_url,
        "output_format": output_format.lower(),
        "quality": args.get("quality", "medium"),
        "custom_options": args.get("custom_options"),
    }

    job_id = str(uuid.uuid4())

    async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return await media_conversion_service.process_conversion(data)

    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.MEDIA_CONVERSION,
        process_func=process_wrapper,
        data=job_data,
    )

    result = await _poll_job(job_id, timeout=300)
    if result.get("error"):
        return {**result, "job_id": job_id}

    res = result.get("result", {})
    output_url = res.get("output_url") or res.get("url")
    if output_url:
        return {"output_url": output_url, "format": output_format, "job_id": job_id}
    return {"error": "Conversion completed but no URL returned", "job_id": job_id}


skill.action(
    name="convert_media",
    description=(
        "Convert media files between formats (e.g., MP4 to WebM, WAV to MP3, PNG to JPEG). "
        "Provide a URL and target format. Returns the converted file URL."
    ),
    handler=_convert_media,
    properties={
        "input_url": {
            "type": "string",
            "description": "URL of the media file to convert",
        },
        "output_format": {
            "type": "string",
            "description": "Target format (e.g., 'mp4', 'webm', 'mp3', 'wav', 'png', 'jpeg')",
        },
        "quality": {
            "type": "string",
            "enum": ["low", "medium", "high", "ultra"],
            "description": "Output quality preset",
            "default": "medium",
        },
    },
    required=["input_url", "output_format"],
)
