"""Topic-to-video skill — generate complete videos from a topic using the AI pipeline."""

import asyncio
import uuid
from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(
    name="topic_to_video",
    description="Generate a complete video from a topic with AI script, TTS, visuals, and captions",
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

    return {"error": f"Job timed out after {timeout}s", "job_id": job_id}


async def _generate_topic_video(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.job_queue import job_queue
    from app.models import JobType
    from app.routes.ai.footage_to_video import process_unified_video_wrapper

    job_id = str(uuid.uuid4())

    data: dict[str, Any] = {
        "topic": args.get("topic"),
        "custom_script": args.get("custom_script"),
        "auto_topic": args.get("auto_topic", False),
        "language": args.get("language", "en"),
        "script_type": args.get("script_type", "facts"),
        "script_provider": args.get("script_provider", "auto"),
        "max_duration": args.get("max_duration", 50),
        "voice": args.get("voice", "af_alloy"),
        "tts_provider": args.get("tts_provider"),
        "tts_speed": args.get("tts_speed", 1.0),
        "video_orientation": args.get("orientation", "portrait"),
        "footage_provider": args.get("footage_provider", "pexels"),
        "footage_quality": args.get("footage_quality", "high"),
        "media_type": args.get("media_type", "video"),
        "ai_video_provider": args.get("ai_video_provider", "pollinations"),
        "ai_video_model": args.get("ai_video_model", "veo"),
        "ai_image_provider": args.get("ai_image_provider", "together"),
        "ai_image_model": args.get("ai_image_model"),
        "add_captions": args.get("add_captions", True),
        "caption_style": args.get("caption_style", "viral_bounce"),
        "caption_color": args.get("caption_color"),
        "highlight_color": args.get("highlight_color"),
        "caption_position": args.get("caption_position"),
        "font_size": args.get("font_size"),
        "font_family": args.get("font_family"),
        "words_per_line": args.get("words_per_line"),
        "background_music": args.get("background_music", "none"),
        "background_music_volume": args.get("background_music_volume"),
        "background_music_mood": args.get("background_music_mood"),
        "enable_voice_over": args.get("enable_voice_over", True),
        "effect_type": args.get("effect_type"),
        "zoom_speed": args.get("zoom_speed"),
        "pan_direction": args.get("pan_direction"),
    }

    # Remove None values so API defaults apply
    data = {k: v for k, v in data.items() if v is not None}

    if not data.get("topic") and not data.get("auto_topic") and not data.get("custom_script"):
        return {"error": "Provide a 'topic', set 'auto_topic' to true, or provide 'custom_script'"}

    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.FOOTAGE_TO_VIDEO,
        process_func=process_unified_video_wrapper,
        data=data,
    )

    result = await _poll_job(job_id, timeout=600)
    if result.get("error"):
        return {**result, "job_id": job_id}

    video_url = result.get("result", {}).get("video_url") or result.get("result", {}).get("final_video_url")
    if video_url:
        return {"video_url": video_url, "topic": data.get("topic", "auto"), "job_id": job_id}
    return {"error": "Video generation completed but no URL returned", "job_id": job_id}


skill.action(
    name="generate_topic_video",
    description=(
        "Generate a complete video from a topic. The AI pipeline writes a script, "
        "generates TTS narration, finds background visuals, adds captions, and renders the final video. "
        "Returns the video URL."
    ),
    handler=_generate_topic_video,
    properties={
        "topic": {
            "type": "string",
            "description": "Video topic (e.g., 'amazing ocean facts', '5 tips for productivity')",
        },
        "custom_script": {
            "type": "string",
            "description": "Custom script text to use instead of AI-generated script",
        },
        "auto_topic": {
            "type": "boolean",
            "description": "Auto-discover trending topics based on script_type",
            "default": False,
        },
        "script_type": {
            "type": "string",
            "enum": ["facts", "story", "educational", "motivation", "prayer", "pov",
                     "conspiracy", "life_hacks", "would_you_rather", "daily_news"],
            "description": "Type of script to generate",
            "default": "facts",
        },
        "language": {
            "type": "string",
            "description": "Language code (e.g., 'en', 'fr', 'es')",
            "default": "en",
        },
        "max_duration": {
            "type": "integer",
            "description": "Max video duration in seconds (5-900)",
            "default": 50,
        },
        "voice": {
            "type": "string",
            "description": "TTS voice name (e.g., 'af_alloy', 'fr-FR-HenriNeural')",
            "default": "af_alloy",
        },
        "tts_provider": {
            "type": "string",
            "enum": ["kokoro", "edge"],
            "description": "TTS provider",
        },
        "orientation": {
            "type": "string",
            "enum": ["portrait", "landscape", "square"],
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
            "description": "Media type for background: video clips or images with motion",
            "default": "video",
        },
        "ai_video_model": {
            "type": "string",
            "description": "AI video generation model (e.g., 'veo')",
            "default": "veo",
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
        "background_music": {
            "type": "string",
            "description": "Background music: 'none', 'ai_generate', or mood name like 'chill', 'happy', 'dark'",
            "default": "none",
        },
        "background_music_volume": {
            "type": "number",
            "description": "Background music volume (0.0 to 1.0)",
        },
        "effect_type": {
            "type": "string",
            "enum": ["ken_burns", "zoom_in", "zoom_out", "pan", "none"],
            "description": "Motion effect for image backgrounds",
        },
        "zoom_speed": {
            "type": "integer",
            "description": "Zoom speed for motion effects (1-20)",
        },
        "pan_direction": {
            "type": "string",
            "enum": ["left_to_right", "right_to_left", "top_to_bottom", "bottom_to_top"],
            "description": "Pan direction for pan motion effect",
        },
        "script_provider": {
            "type": "string",
            "description": "Script generation provider ('auto', 'openai', etc.)",
            "default": "auto",
        },
    },
    required=[],
)
