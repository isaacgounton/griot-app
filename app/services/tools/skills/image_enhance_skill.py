"""Image enhance skill — enhance and stylize images."""

from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="image_enhance", description="Image enhancement and stylization")


async def _enhance_image(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.image.enhancement_service import image_enhancement_service

    params = {
        "image_url": args["image_url"],
        "enhance_color": args.get("enhance_color", 1.0),
        "enhance_contrast": args.get("enhance_contrast", 1.0),
        "noise_strength": args.get("noise_strength", 10),
        "remove_artifacts": args.get("remove_artifacts", True),
        "add_film_grain": args.get("add_film_grain", False),
        "vintage_effect": args.get("vintage_effect", 0.0),
        "output_format": args.get("output_format", "png"),
        "output_quality": args.get("output_quality", 90),
    }

    result = await image_enhancement_service.enhance_image(params)
    return {"image_url": str(result["image_url"])}


skill.action(
    name="enhance_image",
    description=(
        "Enhance an image by adjusting color, contrast, removing AI artifacts, "
        "or adding film grain and vintage effects. Returns the enhanced image URL."
    ),
    handler=_enhance_image,
    properties={
        "image_url": {
            "type": "string",
            "description": "URL of the image to enhance",
        },
        "enhance_color": {
            "type": "number",
            "description": "Color saturation (0.0=B&W, 1.0=unchanged, 2.0=vivid)",
            "default": 1.0,
        },
        "enhance_contrast": {
            "type": "number",
            "description": "Contrast level (0.0=flat, 1.0=unchanged, 2.0=high)",
            "default": 1.0,
        },
        "add_film_grain": {
            "type": "boolean",
            "description": "Add analog film grain effect",
            "default": False,
        },
        "vintage_effect": {
            "type": "number",
            "description": "Vintage/analog color effect strength (0.0-1.0)",
            "default": 0.0,
        },
    },
    required=["image_url"],
)
