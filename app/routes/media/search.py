"""
Media search API routes for stock videos and images.
"""
import logging
from typing import Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.services.media.pexels_service import pexels_service
from app.services.media.pixabay_service import pixabay_service
from app.services.media.pexels_image_service import pexels_image_service
from app.services.media.pixabay_image_service import pixabay_image_service
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["Media"])


class VideoSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for videos")
    orientation: str = Field("landscape", description="Video orientation: landscape, portrait, square")
    min_duration: int = Field(3, description="Minimum video duration in seconds")
    max_duration: int = Field(30, description="Maximum video duration in seconds")
    per_page: int = Field(20, ge=1, le=50, description="Number of results per page")


class ImageSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for images")
    orientation: str = Field("landscape", description="Image orientation: landscape, portrait, square")
    per_page: int = Field(20, ge=1, le=50, description="Number of results per page")


class MediaResult(BaseModel):
    id: str
    url: str
    thumbnail: str
    duration: int | None = None
    width: int
    height: int
    tags: list[str] = []


class SearchResponse(BaseModel):
    results: list[MediaResult]
    total_results: int
    provider: str


@router.post("/search/videos", response_model=SearchResponse)
async def search_videos(
    request: VideoSearchRequest,
    provider: str = Query("pexels", description="Video provider: pexels, pixabay"),
    _: dict[str, Any] = Depends(get_current_user)
):
    """Search for stock videos from Pexels or Pixabay."""
    try:
        if provider == "pexels":
            service = pexels_service
            provider_name = "pexels"
        elif provider == "pixabay":
            service = pixabay_service
            provider_name = "pixabay"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

        # Search for videos
        videos = await service.search_videos(
            query=request.query,
            orientation=request.orientation,
            min_duration=request.min_duration,
            max_duration=request.max_duration,
            per_page=request.per_page
        )

        # Convert to standardized format
        results = []
        for video in videos:
            results.append(MediaResult(
                id=str(video.get("id", "")),
                url=video.get("url", ""),
                thumbnail=video.get("thumbnail", ""),
                duration=video.get("duration"),
                width=video.get("width", 1920),
                height=video.get("height", 1080),
                tags=video.get("tags", [])
            ))

        return SearchResponse(
            results=results,
            total_results=len(results),
            provider=provider_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching videos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Video search failed: {str(e)}")


@router.post("/search/images", response_model=SearchResponse)
async def search_images(
    request: ImageSearchRequest,
    provider: str = Query("pexels", description="Image provider: pexels, pixabay"),
    _: dict[str, Any] = Depends(get_current_user)
):
    """Search for stock images from Pexels or Pixabay."""
    try:
        if provider == "pexels":
            service = pexels_image_service
            provider_name = "pexels"
        elif provider == "pixabay":
            service = pixabay_image_service
            provider_name = "pixabay"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

        # Search for images
        images = await service.search_images(
            query=request.query,
            orientation=request.orientation,
            per_page=request.per_page
        )

        # Convert to standardized format
        results = []
        for image in images:
            results.append(MediaResult(
                id=str(image.get("id", "")),
                url=image.get("url", ""),
                thumbnail=image.get("thumbnail", ""),
                width=image.get("width", 1920),
                height=image.get("height", 1080),
                tags=image.get("tags", [])
            ))

        return SearchResponse(
            results=results,
            total_results=len(results),
            provider=provider_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching images: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")


@router.get("/providers")
async def get_media_providers():
    """List available media search providers and their capabilities."""
    return {
        "video_providers": [
            {
                "name": "pexels",
                "description": "High-quality stock videos from Pexels",
                "features": ["HD videos", "multiple orientations", "duration filtering"]
            },
            {
                "name": "pixabay",
                "description": "Free stock videos from Pixabay",
                "features": ["free license", "multiple formats", "duration filtering"]
            }
        ],
        "image_providers": [
            {
                "name": "pexels",
                "description": "High-quality stock images from Pexels",
                "features": ["HD images", "multiple orientations", "free for commercial use"]
            },
            {
                "name": "pixabay",
                "description": "Free stock images from Pixabay",
                "features": ["free license", "multiple orientations", "no attribution required"]
            }
        ]
    }