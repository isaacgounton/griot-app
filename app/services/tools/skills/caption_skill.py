"""Caption skill — add captions to videos with multiple styles."""

import asyncio
import uuid
from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="caption", description="Add captions to videos with multiple styles and auto-transcription")


async def _poll_job(job_id: str, timeout: int = 300) -> dict[str, Any]:
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


async def _add_captions(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.job_queue import job_queue
    from app.models import JobType
    from app.services.video.caption_service import advanced_caption_service

    video_url = args.get("video_url")
    if not video_url:
        return {"error": "video_url is required"}

    settings: dict[str, Any] = {}
    if args.get("style"):
        settings["style"] = args["style"]
    if args.get("font_size"):
        settings["font_size"] = args["font_size"]
    if args.get("font_family"):
        settings["font_family"] = args["font_family"]
    if args.get("word_color"):
        settings["word_color"] = args["word_color"]
    if args.get("line_color"):
        settings["line_color"] = args["line_color"]
    if args.get("position"):
        settings["position"] = args["position"]
    if args.get("all_caps") is not None:
        settings["all_caps"] = args["all_caps"]
    if args.get("max_words_per_line"):
        settings["max_words_per_line"] = args["max_words_per_line"]

    job_data = {
        "video_url": video_url,
        "captions": args.get("captions"),
        "settings": settings,
        "replace": [],
        "exclude_time_ranges": [],
        "language": args.get("language", "auto"),
    }

    job_id = str(uuid.uuid4())
    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.VIDEO_ADD_CAPTIONS,
        process_func=advanced_caption_service.process_caption_job,
        data=job_data,
    )

    result = await _poll_job(job_id, timeout=300)
    if result.get("error"):
        return {**result, "job_id": job_id}

    res = result.get("result", {})
    video_url_out = res.get("video_url") or res.get("output_url")
    if video_url_out:
        return {"video_url": video_url_out, "job_id": job_id}
    return {"error": "Captioning completed but no URL returned", "job_id": job_id}


skill.action(
    name="add_captions",
    description=(
        "Add captions to a video. Supports auto-transcription, multiple styles "
        "(classic, karaoke, highlight, underline, word_by_word), and custom SRT/ASS text. "
        "Returns the captioned video URL."
    ),
    handler=_add_captions,
    properties={
        "video_url": {
            "type": "string",
            "description": "URL of the video to caption",
        },
        "captions": {
            "type": "string",
            "description": "SRT/ASS caption text or URL. Omit for auto-transcription",
        },
        "style": {
            "type": "string",
            "enum": ["classic", "karaoke", "highlight", "underline", "word_by_word"],
            "description": "Caption style",
            "default": "classic",
        },
        "language": {
            "type": "string",
            "description": "Language for auto-transcription (e.g., 'en', 'fr', 'auto')",
            "default": "auto",
        },
        "font_size": {
            "type": "integer",
            "description": "Font size in pixels",
            "default": 24,
        },
        "word_color": {
            "type": "string",
            "description": "Highlighted word color (e.g., '#FFFF00')",
        },
        "line_color": {
            "type": "string",
            "description": "Base text color (e.g., '#FFFFFF')",
        },
        "position": {
            "type": "string",
            "enum": ["bottom_center", "top_center", "center"],
            "description": "Caption position on screen",
            "default": "bottom_center",
        },
        "all_caps": {
            "type": "boolean",
            "description": "Convert text to uppercase",
            "default": False,
        },
    },
    required=["video_url"],
)
