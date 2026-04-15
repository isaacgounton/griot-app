"""Image-to-video skill — animate an image into a video with motion effects."""

from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="image_to_video", description="Convert a static image into a video with motion effects")


async def _image_to_video(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.image.image_to_video import image_to_video_service

    image_url = args.get("image_url")
    if not image_url:
        return {"error": "image_url is required"}

    video_params = {
        "image_url": image_url,
        "video_length": args.get("duration", 5.0),
        "zoom_speed": args.get("zoom_speed", 10.0),
        "frame_rate": args.get("frame_rate", 30),
        "should_add_captions": False,
        "match_length": "video",
        "effect_type": args.get("effect_type", "ken_burns"),
        "pan_direction": args.get("pan_direction", "left_to_right"),
    }

    try:
        result = await image_to_video_service.image_to_video(video_params)
        if result and (result.get("video_url") or result.get("final_video_url")):
            video_url = result.get("video_url") or result.get("final_video_url")
            return {"video_url": video_url}
        return {"error": "Image-to-video conversion returned no URL"}
    except Exception as e:
        return {"error": f"Image-to-video failed: {e}"}


skill.action(
    name="image_to_video",
    description=(
        "Convert a static image into a video with motion effects (ken burns, zoom, pan). "
        "Returns the video URL."
    ),
    handler=_image_to_video,
    properties={
        "image_url": {
            "type": "string",
            "description": "URL of the image to animate",
        },
        "effect_type": {
            "type": "string",
            "enum": ["ken_burns", "zoom", "pan", "fade", "none"],
            "description": "Motion effect to apply",
            "default": "ken_burns",
        },
        "duration": {
            "type": "number",
            "description": "Video duration in seconds",
            "default": 5.0,
        },
        "zoom_speed": {
            "type": "number",
            "description": "Zoom speed (1-100)",
            "default": 10.0,
        },
        "pan_direction": {
            "type": "string",
            "enum": ["left_to_right", "right_to_left", "top_to_bottom", "bottom_to_top"],
            "description": "Pan direction for pan effect",
            "default": "left_to_right",
        },
    },
    required=["image_url"],
)
