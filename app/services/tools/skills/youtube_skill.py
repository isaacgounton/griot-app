"""YouTube skill — transcript extraction."""

from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="youtube", description="Extract transcripts from YouTube videos")


async def _get_transcript(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.media.youtube_transcript_service import youtube_transcript_service

    result = await youtube_transcript_service.process_transcript_generation({
        "video_url": args["video_url"],
        "languages": args.get("languages", ["en"]),
        "translate_to": args.get("translate_to"),
        "format": "json",
    })
    return result


skill.action(
    name="get_youtube_transcript",
    description=(
        "Get the transcript of a YouTube video. Returns the full text with timestamps. "
        "Supports language selection and translation."
    ),
    handler=_get_transcript,
    properties={
        "video_url": {
            "type": "string",
            "description": "YouTube video URL (e.g., https://www.youtube.com/watch?v=...)",
        },
        "languages": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Preferred language codes (e.g., ['en', 'fr'])",
            "default": ["en"],
        },
        "translate_to": {
            "type": "string",
            "description": "Translate transcript to this language code (optional)",
        },
    },
    required=["video_url"],
)
