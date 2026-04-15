"""Scenes-to-video skill — create videos from individually defined scenes."""

import asyncio
import uuid
from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(
    name="scenes_to_video",
    description="Create a video from individually defined scenes with narration and background media",
)


async def _poll_job(job_id: str, timeout: int = 600) -> dict[str, Any]:
    """Poll a job until completion or timeout."""
    from app.services.job_queue import job_queue

    elapsed = 0
    interval = 5
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


async def _create_scenes_video(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.job_queue import job_queue
    from app.models import JobType
    from app.routes.ai.scenes_to_video import process_scenes_to_video_wrapper

    scenes_raw = args.get("scenes", [])
    if not scenes_raw:
        return {"error": "At least one scene is required"}

    # Build scenes list
    scenes = []
    for s in scenes_raw:
        scene = {
            "text": s.get("text", ""),
            "searchTerms": s.get("searchTerms", s.get("search_terms", [])),
            "duration": s.get("duration", 3.0),
        }
        if not scene["text"].strip():
            continue
        scenes.append(scene)

    if not scenes:
        return {"error": "At least one scene with text is required"}

    # Build config — keys use camelCase to match scenes_video_service expectations
    config: dict[str, Any] = {
        "voice": args.get("voice", "af_heart"),
        "provider": args.get("tts_provider", "kokoro"),
        "ttsSpeed": args.get("tts_speed", 1.0),
        "captionStyle": args.get("caption_style", "viral_bounce"),
        "enableCaptions": args.get("enable_captions", True),
        "music": args.get("music", "chill"),
        "musicVolume": args.get("music_volume", "medium"),
        "orientation": args.get("orientation", "portrait"),
        "resolution": args.get("resolution", "1080x1920"),
        "language": args.get("language", "en"),
        "footageProvider": args.get("footage_provider", "pexels"),
        "footageQuality": args.get("footage_quality", "high"),
        "mediaType": args.get("media_type", "video"),
        "aiVideoProvider": args.get("ai_video_provider", "pollinations"),
        "aiVideoModel": args.get("ai_video_model", "veo"),
        "aiImageProvider": args.get("ai_image_provider", "together"),
        "aiImageModel": args.get("ai_image_model", ""),
        "effect_type": args.get("effect_type", "ken_burns"),
        "zoom_speed": args.get("zoom_speed", 10),
        "pan_direction": args.get("pan_direction", "left_to_right"),
    }

    # Optional caption customization
    if args.get("caption_color"):
        config["captionColor"] = args["caption_color"]
    if args.get("highlight_color"):
        config["highlightColor"] = args["highlight_color"]
    if args.get("caption_position"):
        config["captionPosition"] = args["caption_position"]
    if args.get("font_size"):
        config["fontSize"] = args["font_size"]
    if args.get("font_family"):
        config["fontFamily"] = args["font_family"]
    if args.get("words_per_line"):
        config["wordsPerLine"] = args["words_per_line"]

    job_id = str(uuid.uuid4())
    job_data = {"scenes": scenes, "config": config}

    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.SCENES_TO_VIDEO,
        process_func=process_scenes_to_video_wrapper,
        data=job_data,
    )

    result = await _poll_job(job_id, timeout=600)
    if result.get("error"):
        return {**result, "job_id": job_id}

    video_url = result.get("result", {}).get("video_url") or result.get("result", {}).get("final_video_url")
    if video_url:
        return {"video_url": video_url, "scenes_count": len(scenes), "job_id": job_id}
    return {"error": "Video generation completed but no URL returned", "job_id": job_id}


skill.action(
    name="create_scenes_video",
    description=(
        "Create a video from individually defined scenes. Each scene has narration text, "
        "search terms for background media, and a duration. Returns the video URL."
    ),
    handler=_create_scenes_video,
    properties={
        "scenes": {
            "type": "array",
            "description": "List of scenes. Each scene: {text, searchTerms, duration}",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Narration text for this scene"},
                    "searchTerms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Search terms for background media",
                    },
                    "duration": {
                        "type": "number",
                        "description": "Scene duration in seconds (1-30)",
                        "default": 3.0,
                    },
                },
                "required": ["text"],
            },
        },
        "voice": {
            "type": "string",
            "description": "TTS voice name (e.g., 'af_heart', 'fr-FR-HenriNeural')",
            "default": "af_heart",
        },
        "tts_provider": {
            "type": "string",
            "enum": ["kokoro", "edge"],
            "description": "TTS provider",
            "default": "kokoro",
        },
        "language": {
            "type": "string",
            "description": "Language code (e.g., 'en', 'fr')",
            "default": "en",
        },
        "orientation": {
            "type": "string",
            "enum": ["portrait", "landscape"],
            "description": "Video orientation",
            "default": "portrait",
        },
        "footage_provider": {
            "type": "string",
            "enum": ["pexels", "pixabay", "ai_generated"],
            "description": "Background footage provider",
            "default": "pexels",
        },
        "footage_quality": {
            "type": "string",
            "enum": ["high", "medium", "low"],
            "description": "Footage quality preference",
            "default": "high",
        },
        "media_type": {
            "type": "string",
            "enum": ["video", "image"],
            "description": "Background media type",
            "default": "video",
        },
        "ai_video_provider": {
            "type": "string",
            "enum": ["pollinations", "wavespeed", "modal"],
            "description": "AI video generation provider",
            "default": "pollinations",
        },
        "ai_video_model": {
            "type": "string",
            "description": "AI video generation model (e.g., 'veo')",
            "default": "veo",
        },
        "ai_image_provider": {
            "type": "string",
            "enum": ["together", "pollinations", "modal"],
            "description": "AI image generation provider",
            "default": "together",
        },
        "ai_image_model": {
            "type": "string",
            "description": "AI image generation model",
        },
        "caption_style": {
            "type": "string",
            "enum": ["classic", "viral_bounce", "karaoke", "highlight", "word_by_word"],
            "description": "Caption style preset",
            "default": "viral_bounce",
        },
        "caption_color": {
            "type": "string",
            "description": "Caption text color (e.g., '#FFFFFF')",
        },
        "highlight_color": {
            "type": "string",
            "description": "Active word highlight color (e.g., '#FFD700')",
        },
        "caption_position": {
            "type": "string",
            "enum": ["top", "center", "bottom"],
            "description": "Caption vertical position",
        },
        "font_size": {
            "type": "integer",
            "description": "Caption font size in pixels",
        },
        "font_family": {
            "type": "string",
            "description": "Caption font family name",
        },
        "words_per_line": {
            "type": "integer",
            "description": "Max words per caption line",
        },
        "music": {
            "type": "string",
            "description": "Background music mood (e.g., 'chill', 'happy', 'dark', 'none')",
            "default": "chill",
        },
        "effect_type": {
            "type": "string",
            "enum": ["ken_burns", "zoom_in", "zoom_out", "pan", "none"],
            "description": "Motion effect for image backgrounds",
            "default": "ken_burns",
        },
        "zoom_speed": {
            "type": "integer",
            "description": "Zoom speed for motion effects (1-20)",
            "default": 10,
        },
        "pan_direction": {
            "type": "string",
            "enum": ["left_to_right", "right_to_left", "top_to_bottom", "bottom_to_top"],
            "description": "Pan direction for pan motion effect",
            "default": "left_to_right",
        },
    },
    required=["scenes"],
)
