"""Social media skill — post, schedule, and manage social media via Postiz."""

from datetime import datetime
from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(
    name="social",
    description="Post, schedule, and manage social media content via Postiz",
)


# ---------------------------------------------------------------------------
# Helper: resolve platform names to integration IDs
# ---------------------------------------------------------------------------

async def _resolve_integration_ids(
    platforms: list[str],
) -> tuple[list[str], list[dict[str, str]]]:
    """Resolve friendly platform names to Postiz integration IDs.

    Returns (integration_ids, integrations_info) where integrations_info is a
    list of {id, name, provider} dicts for the matched integrations.
    """
    from app.services.postiz.postiz_service import get_postiz_service

    service = get_postiz_service()
    available = await service.get_integrations()

    matched_ids: list[str] = []
    matched_info: list[dict[str, str]] = []

    for platform in platforms:
        platform_lower = platform.lower().strip()
        for integration in available:
            # Match by provider name or integration name (case-insensitive)
            if (
                platform_lower in integration.provider.lower()
                or platform_lower in integration.name.lower()
                or platform_lower == integration.id
            ):
                if integration.id not in matched_ids:
                    matched_ids.append(integration.id)
                    matched_info.append({
                        "id": integration.id,
                        "name": integration.name,
                        "provider": integration.provider,
                    })

    return matched_ids, matched_info


# ---------------------------------------------------------------------------
# List platforms
# ---------------------------------------------------------------------------

async def _list_social_platforms(_args: dict[str, Any]) -> dict[str, Any]:
    from app.services.postiz.postiz_service import get_postiz_service

    service = get_postiz_service()
    try:
        integrations = await service.get_integrations()
        return {
            "platforms": [
                {"id": i.id, "name": i.name, "provider": i.provider}
                for i in integrations
            ],
            "total": len(integrations),
        }
    except Exception as e:
        return {"error": f"Failed to list platforms: {e}"}


skill.action(
    name="list_social_platforms",
    description=(
        "List all connected social media platforms/accounts available for posting. "
        "Returns platform names, providers, and IDs."
    ),
    handler=_list_social_platforms,
    properties={},
    required=[],
)


# ---------------------------------------------------------------------------
# Post immediately
# ---------------------------------------------------------------------------

async def _post_to_social_media(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.postiz.postiz_service import get_postiz_service

    content = args.get("content", "")
    platforms = args.get("platforms", [])
    media_urls = args.get("media_urls") or None
    tags = args.get("tags") or None

    if not content:
        return {"error": "Content is required"}
    if not platforms:
        return {"error": "At least one platform is required. Use list_social_platforms to see available platforms."}

    integration_ids, matched = await _resolve_integration_ids(platforms)
    if not integration_ids:
        return {
            "error": f"No matching platforms found for: {platforms}. Use list_social_platforms to see available platforms.",
        }

    service = get_postiz_service()
    try:
        result = await service.schedule_post_now(
            content=content,
            integrations=integration_ids,
            media_paths=media_urls,
            tags=tags,
        )
        return {
            "success": True,
            "message": f"Posted to {len(matched)} platform(s)",
            "platforms": matched,
            "response": result,
        }
    except Exception as e:
        return {"error": f"Failed to post: {e}"}


skill.action(
    name="post_to_social_media",
    description=(
        "Publish content immediately to one or more social media platforms. "
        "Use list_social_platforms first to see available platforms."
    ),
    handler=_post_to_social_media,
    properties={
        "content": {
            "type": "string",
            "description": "The post content/caption text",
        },
        "platforms": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Platform names to post to (e.g. ['twitter', 'linkedin'])",
        },
        "media_urls": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional media URLs (images/videos) to attach to the post",
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional tags/hashtags for the post",
        },
    },
    required=["content", "platforms"],
)


# ---------------------------------------------------------------------------
# Schedule for later
# ---------------------------------------------------------------------------

async def _schedule_social_post(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.postiz.postiz_service import get_postiz_service

    content = args.get("content", "")
    platforms = args.get("platforms", [])
    schedule_date_str = args.get("schedule_date", "")
    media_urls = args.get("media_urls") or None
    tags = args.get("tags") or None

    if not content:
        return {"error": "Content is required"}
    if not platforms:
        return {"error": "At least one platform is required"}
    if not schedule_date_str:
        return {"error": "schedule_date is required (ISO 8601 format, e.g. '2026-02-20T14:00:00Z')"}

    try:
        schedule_date = datetime.fromisoformat(schedule_date_str.replace("Z", "+00:00"))
    except ValueError:
        return {"error": f"Invalid date format: {schedule_date_str}. Use ISO 8601 (e.g. '2026-02-20T14:00:00Z')"}

    integration_ids, matched = await _resolve_integration_ids(platforms)
    if not integration_ids:
        return {"error": f"No matching platforms found for: {platforms}"}

    service = get_postiz_service()
    try:
        result = await service.schedule_post_later(
            content=content,
            integrations=integration_ids,
            schedule_date=schedule_date,
            media_paths=media_urls,
            tags=tags,
        )
        return {
            "success": True,
            "message": f"Scheduled for {schedule_date_str} on {len(matched)} platform(s)",
            "platforms": matched,
            "scheduled_date": schedule_date_str,
            "response": result,
        }
    except Exception as e:
        return {"error": f"Failed to schedule: {e}"}


skill.action(
    name="schedule_social_post",
    description=(
        "Schedule content to be published at a specific future date and time. "
        "Use list_social_platforms first to see available platforms."
    ),
    handler=_schedule_social_post,
    properties={
        "content": {
            "type": "string",
            "description": "The post content/caption text",
        },
        "platforms": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Platform names to post to (e.g. ['twitter', 'linkedin'])",
        },
        "schedule_date": {
            "type": "string",
            "description": "ISO 8601 date/time to publish (e.g. '2026-02-20T14:00:00Z')",
        },
        "media_urls": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional media URLs (images/videos) to attach",
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional tags/hashtags for the post",
        },
    },
    required=["content", "platforms", "schedule_date"],
)


# ---------------------------------------------------------------------------
# Create draft
# ---------------------------------------------------------------------------

async def _create_social_draft(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.postiz.postiz_service import get_postiz_service

    content = args.get("content", "")
    platforms = args.get("platforms", [])
    media_urls = args.get("media_urls") or None
    tags = args.get("tags") or None

    if not content:
        return {"error": "Content is required"}
    if not platforms:
        return {"error": "At least one platform is required"}

    integration_ids, matched = await _resolve_integration_ids(platforms)
    if not integration_ids:
        return {"error": f"No matching platforms found for: {platforms}"}

    service = get_postiz_service()
    try:
        result = await service.create_draft_post(
            content=content,
            integrations=integration_ids,
            media_paths=media_urls,
            tags=tags,
        )
        return {
            "success": True,
            "message": f"Draft created for {len(matched)} platform(s)",
            "platforms": matched,
            "response": result,
        }
    except Exception as e:
        return {"error": f"Failed to create draft: {e}"}


skill.action(
    name="create_social_draft",
    description=(
        "Save content as a draft post for later editing and publishing. "
        "Use list_social_platforms first to see available platforms."
    ),
    handler=_create_social_draft,
    properties={
        "content": {
            "type": "string",
            "description": "The post content/caption text",
        },
        "platforms": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Platform names to save draft for (e.g. ['twitter', 'linkedin'])",
        },
        "media_urls": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional media URLs (images/videos) to attach",
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional tags/hashtags for the post",
        },
    },
    required=["content", "platforms"],
)
