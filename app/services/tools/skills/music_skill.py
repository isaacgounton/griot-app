"""Music skill — AI music generation from text descriptions."""

import uuid
from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="music", description="AI music generation from text descriptions")


async def _generate_music(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.audio.music_generation import music_generation_service

    data = {
        "description": args["description"],
        "duration": args.get("duration", 8),
        "model_size": "small",
        "output_format": args.get("output_format", "wav"),
    }

    result = await music_generation_service.process_music_generation(
        job_id=uuid.uuid4().hex, data=data
    )
    return {"audio_url": result["audio_url"], "duration": result.get("duration")}


skill.action(
    name="generate_music",
    description="Generate music from a text description. Returns an audio URL.",
    handler=_generate_music,
    properties={
        "description": {
            "type": "string",
            "description": "Description of the music to generate (e.g., 'lo-fi hip-hop with chill vibes')",
        },
        "duration": {
            "type": "integer",
            "description": "Duration in seconds (1-30)",
            "default": 8,
        },
        "output_format": {
            "type": "string",
            "enum": ["wav", "mp3"],
            "description": "Audio output format",
            "default": "wav",
        },
    },
    required=["description"],
)
