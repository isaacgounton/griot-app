"""Media download skill — download media from URLs (YouTube, TikTok, etc.)."""

import uuid
from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(
    name="media_download",
    description="Download media from URLs (YouTube, TikTok, Instagram, and 700+ platforms)",
)


async def _download_media(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.media.download_service import download_service

    url = args["url"]
    format_param = args.get("format", "best")
    cookies_url = args.get("cookies_url")

    result = await download_service.process_enhanced_media_download(
        job_id=uuid.uuid4().hex,
        params={
            "url": url,
            "format": format_param,
            "file_name": None,
            "cookies_url": cookies_url,
        },
    )

    file_url = result.get("file_url", "")
    title = result.get("title", "Downloaded media")
    duration = result.get("duration")

    # Map to the key the chat frontend expects
    is_audio = format_param == "mp3" or file_url.endswith((".mp3", ".wav", ".ogg"))
    if is_audio:
        return {"audio_url": file_url, "title": title, "duration": duration}
    return {"video_url": file_url, "title": title, "duration": duration}


skill.action(
    name="download_media",
    description=(
        "Download media from a URL. Supports YouTube, TikTok, Instagram, "
        "Vimeo, Twitter/X, SoundCloud, and 700+ platforms. "
        "Returns a downloadable media URL."
    ),
    handler=_download_media,
    properties={
        "url": {
            "type": "string",
            "description": "URL of the media to download",
        },
        "format": {
            "type": "string",
            "description": "Desired format: 'best', 'mp4', 'mp3', '720p', '480p'",
            "default": "best",
        },
        "cookies_url": {
            "type": "string",
            "description": "URL to a cookies.txt file for authenticated downloads (required for restricted YouTube videos)",
        },
    },
    required=["url"],
)
