"""Vision skill — AI image analysis."""

from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="vision", description="Analyze images with AI vision models")


async def _analyze_image(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.pollinations.pollinations_service import pollinations_service

    image_url = args["image_url"]
    question = args.get("question", "Describe this image in detail.")

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        }
    ]

    response = await pollinations_service.generate_text_chat(
        messages=messages,
        model=args.get("model"),
    )
    return {"analysis": response, "image_url": image_url}


skill.action(
    name="analyze_image",
    description=(
        "Analyze an image using AI vision. Can describe images, answer questions "
        "about visual content, read text in images, and more."
    ),
    handler=_analyze_image,
    properties={
        "image_url": {
            "type": "string",
            "description": "URL of the image to analyze",
        },
        "question": {
            "type": "string",
            "description": "Question to ask about the image (default: describe it)",
            "default": "Describe this image in detail.",
        },
        "model": {
            "type": "string",
            "description": "AI model to use (optional, auto-selected by default)",
        },
    },
    required=["image_url"],
)
