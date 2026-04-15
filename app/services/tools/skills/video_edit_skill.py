"""Video edit skill — add text overlays to videos."""

from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="video_edit", description="Video editing — text overlays and effects")


async def _add_text_overlay(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.video.text_overlay import TextOverlayOptions, text_overlay_service

    options = TextOverlayOptions(
        text=args["text"],
        font_size=args.get("font_size", 48),
        font_color=args.get("font_color", "white"),
        position=args.get("position", "bottom-center"),
        box_color=args.get("box_color", "black"),
        box_opacity=args.get("box_opacity", 0.8),
        box_padding=args.get("box_padding", 10),
        start_time=args.get("start_time", 0.0),
        duration=args.get("duration", 5.0),
    )

    result = await text_overlay_service.create_text_overlay(
        video_url=args["video_url"], options=options
    )

    if not result.get("success"):
        return {"error": result.get("error", "Text overlay failed")}

    return {"video_url": result["video_url"]}


skill.action(
    name="add_text_overlay",
    description=(
        "Add text overlay to a video. Supports positioning, colors, "
        "background boxes, and timing. Returns the edited video URL."
    ),
    handler=_add_text_overlay,
    properties={
        "video_url": {
            "type": "string",
            "description": "URL of the video to edit",
        },
        "text": {
            "type": "string",
            "description": "Text to overlay on the video (1-500 characters)",
        },
        "position": {
            "type": "string",
            "enum": [
                "top-left", "top-center", "top-right",
                "center-left", "center", "center-right",
                "bottom-left", "bottom-center", "bottom-right",
            ],
            "description": "Text position on the video",
            "default": "bottom-center",
        },
        "font_size": {
            "type": "integer",
            "description": "Font size in pixels",
            "default": 48,
        },
        "font_color": {
            "type": "string",
            "description": "Text color (e.g., 'white', 'yellow', '#FF0000')",
            "default": "white",
        },
        "box_color": {
            "type": "string",
            "description": "Background box color (e.g., 'black', 'red')",
            "default": "black",
        },
        "start_time": {
            "type": "number",
            "description": "When to start showing text (seconds)",
            "default": 0.0,
        },
        "duration": {
            "type": "number",
            "description": "How long to show text (seconds)",
            "default": 5.0,
        },
    },
    required=["video_url", "text"],
)
