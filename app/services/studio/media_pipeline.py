"""Media Pipeline: Source or generate visual media for each scene.

Supports stock footage (Pexels/Pixabay), AI-generated images/videos
(Pollinations, WaveSpeed), and user uploads.
"""
from __future__ import annotations

import os
import tempfile
import uuid

from loguru import logger

from app.services.s3.s3 import s3_service


async def source_scene_media(
    scene: dict,
    settings: dict,
) -> dict:
    """Source or generate media for a single scene.

    Returns {"media_url": str, "media_provider": str}
    """
    source_type = scene.get("media_source_type") or settings.get("media_type", "video")
    search_terms = scene.get("media_search_terms") or []
    prompt = scene.get("media_prompt") or scene.get("script_text", "")
    duration = scene.get("duration", 3.0)

    # Generate search terms from script if none provided
    if not search_terms and prompt:
        from app.services.studio.ai_scene_generator import _extract_search_terms_simple
        search_terms = _extract_search_terms_simple(prompt)

    footage_provider = settings.get("footage_provider", "pexels")

    # For AI media, wrap raw script text into a visual prompt (works for any language)
    if source_type in ("ai_video", "ai_image") and prompt and not scene.get("media_prompt"):
        prompt = f"cinematic, high quality, {prompt[:300]}"

    try:
        if source_type in ("stock_video", "video") and footage_provider in ("pexels", "pixabay"):
            return await _search_stock_video(search_terms, duration, footage_provider)
        elif source_type in ("stock_image", "image") and footage_provider in ("pexels", "pixabay"):
            return await _search_stock_image(search_terms, footage_provider)
        elif source_type == "ai_video":
            ai_provider = settings.get("ai_video_provider", "pollinations")
            return await _generate_ai_video(prompt, duration, ai_provider, settings)
        elif source_type == "ai_image":
            ai_provider = settings.get("ai_image_provider", "pollinations")
            return await _generate_ai_image(prompt, ai_provider, settings)
        else:
            # Default: try stock video
            return await _search_stock_video(search_terms, duration, "pexels")
    except Exception as e:
        logger.error(f"Media sourcing failed for scene: {e}")
        # Return empty — scene will render with a blank/placeholder
        return {"media_url": None, "media_provider": "failed"}


async def _search_stock_video(search_terms: list[str], duration: float, provider: str) -> dict:
    """Search for stock video from Pexels or Pixabay."""
    query = " ".join(search_terms[:3]) if search_terms else "nature"

    try:
        if provider == "pexels":
            from app.services.media.pexels_service import pexels_service
            result = await pexels_service.search_videos({
                "query": query,
                "per_page": 5,
                "min_duration": max(1, int(duration) - 2),
            })
            videos = result.get("videos", [])
            if videos:
                video = videos[0]
                video_url = video.get("download_url") or video.get("url")
                if video_url:
                    return {"media_url": video_url, "media_provider": "pexels"}

        elif provider == "pixabay":
            from app.services.media.pixabay_service import pixabay_service
            videos = await pixabay_service.search_videos(
                query=query,
                per_page=5,
                min_duration=max(1, int(duration) - 2),
            )
            if videos:
                video = videos[0]
                video_url = video.get("url")
                if video_url:
                    return {"media_url": video_url, "media_provider": "pixabay"}

    except Exception as e:
        logger.warning(f"Stock video search failed ({provider}): {e}")

    return {"media_url": None, "media_provider": provider}


async def _search_stock_image(search_terms: list[str], provider: str) -> dict:
    """Search for stock images from Pexels or Pixabay."""
    query = " ".join(search_terms[:3]) if search_terms else "nature"

    try:
        if provider == "pexels":
            from app.services.media.pexels_image_service import pexels_image_service
            result = await pexels_image_service.search_images({
                "query": query,
                "per_page": 5,
            })
            images = result.get("images", [])
            if images:
                image = images[0]
                image_url = image.get("download_url") or image.get("url")
                if image_url:
                    return {"media_url": image_url, "media_provider": "pexels"}

        elif provider == "pixabay":
            from app.services.media.pixabay_image_service import pixabay_image_service
            images = await pixabay_image_service.search_images(
                query=query,
                per_page=5,
            )
            if images:
                image = images[0]
                image_url = image.get("download_url") or image.get("url")
                if image_url:
                    return {"media_url": image_url, "media_provider": "pixabay"}

    except Exception as e:
        logger.warning(f"Stock image search failed ({provider}): {e}")

    return {"media_url": None, "media_provider": provider}


async def _save_video_bytes_to_s3(video_bytes: bytes, provider: str) -> str | None:
    """Save raw video bytes to S3 and return the URL."""
    if not video_bytes or len(video_bytes) < 100:
        return None

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        s3_key = f"studio/media/{provider}/{uuid.uuid4()}.mp4"
        result = await s3_service.upload_file_with_metadata(
            tmp_path, s3_key, content_type="video/mp4", public=True
        )
        return result.get("file_url")
    except Exception as e:
        logger.warning(f"Failed to upload video to S3: {e}")
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def _generate_ai_video(prompt: str, duration: float, provider: str, settings: dict) -> dict:
    """Generate AI video from Pollinations or WaveSpeed."""
    try:
        if provider == "pollinations":
            from app.services.pollinations.pollinations_service import pollinations_service
            model = settings.get("ai_video_model", "veo")
            res = settings.get("resolution", {"width": 1080, "height": 1920})
            video_bytes = await pollinations_service.generate_video(
                prompt=prompt,
                model=model,
                duration=min(int(duration), 8),
                width=res.get("width", 1080),
                height=res.get("height", 1920),
            )
            video_url = await _save_video_bytes_to_s3(video_bytes, "pollinations")
            if video_url:
                return {"media_url": video_url, "media_provider": "pollinations"}

        elif provider == "wavespeed":
            from app.services.video.wavespeed_service import wavespeed_service
            model = settings.get("ai_video_model", "wan-2.2")
            video_bytes = await wavespeed_service.text_to_video(
                prompt=prompt,
                model=model,
                duration=5 if duration <= 5 else 8,
            )
            video_url = await _save_video_bytes_to_s3(video_bytes, "wavespeed")
            if video_url:
                return {"media_url": video_url, "media_provider": "wavespeed"}

    except Exception as e:
        logger.warning(f"AI video generation failed ({provider}): {e}")

    return {"media_url": None, "media_provider": provider}


async def _generate_ai_image(prompt: str, provider: str, settings: dict) -> dict:
    """Generate AI image from Pollinations, Together, or Modal."""
    try:
        if provider in ("pollinations", "together"):
            from app.services.pollinations.pollinations_service import pollinations_service
            res = settings.get("resolution", {"width": 1080, "height": 1920})
            model = settings.get("ai_image_model", "flux")
            result = await pollinations_service.generate_image(
                prompt=prompt,
                width=res.get("width", 1080),
                height=res.get("height", 1920),
                model=model,
            )
            image_url = result.get("url")
            if image_url:
                return {"media_url": image_url, "media_provider": provider}

    except Exception as e:
        logger.warning(f"AI image generation failed ({provider}): {e}")

    return {"media_url": None, "media_provider": provider}


async def source_project_media(
    scenes: list[dict],
    settings: dict,
) -> list[dict]:
    """Source media for all scenes in a project.

    Returns list of {"scene_id": str, "media_url": str, "media_provider": str}.
    """
    results = []
    for scene in scenes:
        result = await source_scene_media(scene, settings)
        result["scene_id"] = scene["id"]
        results.append(result)
    return results


async def search_stock_results(
    search_terms: list[str],
    source_type: str,
    provider: str = "pexels",
    duration: float = 5.0,
    orientation: str = "portrait",
) -> list[dict]:
    """Search stock video/image and return ALL results for the user to pick from.

    Returns list of dicts with id, url, thumbnail, download_url, duration,
    photographer, and provider.
    """
    query = " ".join(search_terms[:3]) if search_terms else "nature"

    try:
        if source_type in ("stock_video", "video"):
            if provider == "pexels":
                from app.services.media.pexels_service import pexels_service
                result = await pexels_service.search_videos({
                    "query": query,
                    "per_page": 30,
                    "min_duration": max(1, int(duration) - 2),
                    "orientation": orientation,
                })
                return [
                    {
                        "id": v.get("id"),
                        "url": v.get("download_url") or v.get("url"),
                        "thumbnail": v.get("image") or v.get("url"),
                        "download_url": v.get("download_url") or v.get("url"),
                        "duration": v.get("duration"),
                        "photographer": v.get("user", {}).get("name"),
                        "provider": "pexels",
                        "type": "video",
                    }
                    for v in result.get("videos", [])
                ]
            elif provider == "pixabay":
                from app.services.media.pixabay_service import pixabay_service
                videos = await pixabay_service.search_videos(
                    query=query, per_page=30,
                    min_duration=max(1, int(duration) - 2),
                    orientation=orientation,
                )
                return [
                    {
                        "id": v.get("id"),
                        "url": v.get("url"),
                        "thumbnail": v.get("thumbnail") or v.get("url"),
                        "download_url": v.get("url"),
                        "duration": v.get("duration"),
                        "photographer": v.get("user"),
                        "provider": "pixabay",
                        "type": "video",
                    }
                    for v in (videos or [])
                ]

        elif source_type in ("stock_image", "image"):
            if provider == "pexels":
                from app.services.media.pexels_image_service import pexels_image_service
                result = await pexels_image_service.search_images({
                    "query": query,
                    "per_page": 30,
                    "orientation": orientation,
                })
                return [
                    {
                        "id": img.get("id"),
                        "url": img.get("download_url") or img.get("url"),
                        "thumbnail": img.get("url") or img.get("download_url"),
                        "download_url": img.get("download_url") or img.get("url"),
                        "photographer": img.get("photographer"),
                        "provider": "pexels",
                        "type": "image",
                    }
                    for img in result.get("images", [])
                ]
            elif provider == "pixabay":
                from app.services.media.pixabay_image_service import pixabay_image_service
                images = await pixabay_image_service.search_images(
                    query=query, per_page=30,
                )
                return [
                    {
                        "id": img.get("id"),
                        "url": img.get("download_url") or img.get("url"),
                        "thumbnail": img.get("url") or img.get("download_url"),
                        "download_url": img.get("download_url") or img.get("url"),
                        "photographer": img.get("user"),
                        "provider": "pixabay",
                        "type": "image",
                    }
                    for img in (images or [])
                ]

    except Exception as e:
        logger.warning(f"Stock search failed ({provider}): {e}")

    return []
