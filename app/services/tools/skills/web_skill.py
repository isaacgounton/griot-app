"""Web skill — webpage screenshot capture."""

from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="web", description="Web page screenshot capture")


async def _capture_screenshot(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.web_screenshot import (
        web_screenshot_service,
        ScreenshotRequest,
        DeviceType,
    )

    device_map = {
        "desktop": DeviceType.DESKTOP,
        "mobile": DeviceType.MOBILE,
        "tablet": DeviceType.TABLET,
    }

    request = ScreenshotRequest(
        url=args["url"],
        full_page=args.get("full_page", False),
        device_type=device_map.get(args.get("device_type", "desktop"), DeviceType.DESKTOP),
    )

    result = await web_screenshot_service.take_screenshot(request)
    if result.success and result.screenshot_url:
        return {"screenshot_url": result.screenshot_url, "url": args["url"]}
    return {"error": result.error or "Screenshot capture failed"}


skill.action(
    name="capture_screenshot",
    description="Capture a screenshot of a webpage. Returns the screenshot image URL.",
    handler=_capture_screenshot,
    properties={
        "url": {
            "type": "string",
            "description": "The URL of the webpage to screenshot",
        },
        "full_page": {
            "type": "boolean",
            "description": "Whether to capture the full scrollable page",
            "default": False,
        },
        "device_type": {
            "type": "string",
            "enum": ["desktop", "mobile", "tablet"],
            "description": "Device type for viewport emulation",
            "default": "desktop",
        },
    },
    required=["url"],
)
