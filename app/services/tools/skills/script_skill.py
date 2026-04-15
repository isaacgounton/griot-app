"""Script skill — AI video script generation."""

from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="script", description="Generate AI-powered video scripts")


async def _generate_script(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.text.script_generator import script_generator

    result = await script_generator.generate_script({
        "topic": args["topic"],
        "script_type": args.get("script_type", "facts"),
        "language": args.get("language", "english"),
        "max_duration": args.get("max_duration", 60),
    })
    return result


skill.action(
    name="generate_script",
    description=(
        "Generate a video script from a topic. Supports multiple styles "
        "including facts, story, educational, and daily news formats."
    ),
    handler=_generate_script,
    properties={
        "topic": {
            "type": "string",
            "description": "The topic or subject for the script",
        },
        "script_type": {
            "type": "string",
            "enum": ["facts", "story", "educational", "entertaining", "daily_news"],
            "description": "Script style",
            "default": "facts",
        },
        "language": {
            "type": "string",
            "description": "Output language (e.g., 'english', 'french')",
            "default": "english",
        },
        "max_duration": {
            "type": "integer",
            "description": "Maximum duration in seconds",
            "default": 60,
        },
    },
    required=["topic"],
)
