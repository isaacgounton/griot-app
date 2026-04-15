"""Transcription skill — audio/video transcription."""

from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="transcription", description="Transcribe audio and video files to text")


async def _transcribe_media(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.media.transcription import get_transcription_service

    service = get_transcription_service()

    # Download and transcribe
    media_url = args["media_url"]
    file_path, _ = await service.download_media(media_url)

    result = await service.transcribe(
        file_path=file_path,
        include_text=True,
        include_srt=args.get("include_srt", False),
        word_timestamps=args.get("word_timestamps", False),
        include_segments=args.get("include_segments", False),
        language=args.get("language"),
    )
    return result


skill.action(
    name="transcribe_media",
    description=(
        "Transcribe audio or video to text. Supports MP3, WAV, MP4, and other "
        "media formats. Returns plain text and optionally SRT subtitles."
    ),
    handler=_transcribe_media,
    properties={
        "media_url": {
            "type": "string",
            "description": "URL of the audio or video file to transcribe",
        },
        "language": {
            "type": "string",
            "description": "Source language code (e.g., 'en', 'fr'). Auto-detected if omitted.",
        },
        "include_srt": {
            "type": "boolean",
            "description": "Include SRT subtitle format in output",
            "default": False,
        },
        "word_timestamps": {
            "type": "boolean",
            "description": "Include word-level timestamps",
            "default": False,
        },
        "include_segments": {
            "type": "boolean",
            "description": "Include timestamped segments",
            "default": False,
        },
    },
    required=["media_url"],
)
