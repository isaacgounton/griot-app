"""Audio skill — text-to-speech generation."""

import os
import tempfile
import uuid
from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="audio", description="Text-to-speech audio generation")


async def _text_to_speech(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.audio.tts_service import tts_service
    from app.services.s3 import s3_service

    text = args["text"]
    voice = args.get("voice", "af_heart")
    provider = args.get("provider", "kokoro")
    speed = args.get("speed", 1.0)
    response_format = args.get("response_format", "mp3")
    lang_code = args.get("lang_code")

    audio_bytes, provider_used = await tts_service.generate_speech(
        text=text,
        voice=voice,
        provider=provider,
        response_format=response_format,
        speed=speed,
    )

    # Write to temp file and upload to S3
    object_name = f"tts/{uuid.uuid4().hex}.{response_format}"
    mime_types = {
        "mp3": "audio/mpeg", "wav": "audio/wav", "opus": "audio/ogg",
        "aac": "audio/mp4", "flac": "audio/flac", "pcm": "audio/wav",
    }
    content_type = mime_types.get(response_format, "audio/mpeg")

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=f".{response_format}")
    try:
        os.write(tmp_fd, audio_bytes)
        os.close(tmp_fd)
        audio_url = await s3_service.upload_file(tmp_path, object_name, content_type=content_type)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return {"audio_url": audio_url, "provider": provider_used}


skill.action(
    name="text_to_speech",
    description="Convert text to spoken audio. Returns an audio URL.",
    handler=_text_to_speech,
    properties={
        "text": {
            "type": "string",
            "description": "The text to convert to speech",
        },
        "voice": {
            "type": "string",
            "description": "Voice name (e.g., 'af_heart', 'af_bella', 'fr-FR-HenriNeural')",
            "default": "af_heart",
        },
        "provider": {
            "type": "string",
            "enum": ["kokoro", "edge", "piper", "kitten"],
            "description": "TTS provider",
            "default": "kokoro",
        },
        "speed": {
            "type": "number",
            "description": "Speech speed multiplier (0.5-2.0)",
            "default": 1.0,
        },
        "response_format": {
            "type": "string",
            "enum": ["mp3", "wav", "opus", "aac", "flac"],
            "description": "Audio output format",
            "default": "mp3",
        },
        "lang_code": {
            "type": "string",
            "description": "Language code for multilingual voices (e.g., 'en', 'fr', 'es')",
        },
    },
    required=["text"],
)
