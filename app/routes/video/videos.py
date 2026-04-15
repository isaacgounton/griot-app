"""
Video management API endpoints.
Provides endpoints for managing persistent video records.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, ConfigDict

from app.utils.auth import get_current_user
from app.services.video import video_service
from app.database import VideoType
from app.config import (
    get_caption_style_preset,
    get_available_caption_style_presets,
    apply_caption_style_preset,
    get_style_recommendations,
    get_caption_best_practices
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Video"])


class VideoInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: Optional[str]
    video_type: str
    final_video_url: str
    video_with_audio_url: Optional[str]
    audio_url: Optional[str]
    srt_url: Optional[str]
    thumbnail_url: Optional[str]
    duration_seconds: Optional[float]
    resolution: Optional[str]
    file_size_mb: Optional[float]
    word_count: Optional[int]
    segments_count: Optional[int]
    script_text: Optional[str]
    voice_provider: Optional[str]
    voice_name: Optional[str]
    language: Optional[str]
    processing_time_seconds: Optional[float]
    background_videos_used: Optional[List[str]]
    tags: Optional[List[str]]
    download_count: int
    last_accessed: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class VideoUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class VideoListResponse(BaseModel):
    videos: List[VideoInfo]
    total: int
    page: int
    limit: int


def _video_to_info(video: Any) -> VideoInfo:
    """Convert a VideoRecord ORM object to VideoInfo response model."""
    return VideoInfo(
        id=video.id,
        title=video.title,
        description=video.description,
        video_type=video.video_type.value,
        final_video_url=video.final_video_url,
        video_with_audio_url=video.video_with_audio_url,
        audio_url=video.audio_url,
        srt_url=video.srt_url,
        thumbnail_url=video.thumbnail_url,
        duration_seconds=video.duration_seconds,
        resolution=video.resolution,
        file_size_mb=video.file_size_mb,
        word_count=video.word_count,
        segments_count=video.segments_count,
        script_text=video.script_text,
        voice_provider=video.voice_provider,
        voice_name=video.voice_name,
        language=video.language,
        processing_time_seconds=video.processing_time_seconds,
        background_videos_used=video.background_videos_used,
        tags=video.tags,
        download_count=video.download_count,
        last_accessed=video.last_accessed,
        created_at=video.created_at,
        updated_at=video.updated_at
    )


@router.get("/", response_model=VideoListResponse)
async def list_videos(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Videos per page"),
    video_type: Optional[str] = Query(None, description="Filter by video type"),
    search: Optional[str] = Query(None, description="Search in title, description, and script"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List videos with optional filtering by type and search query, with pagination."""
    try:
        offset = (page - 1) * limit

        parsed_video_type = None
        if video_type:
            try:
                parsed_video_type = VideoType(video_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid video type: {video_type}"
                )

        videos = await video_service.get_all_videos(
            limit=limit,
            offset=offset,
            video_type=parsed_video_type,
            search_query=search
        )

        video_infos = [_video_to_info(v) for v in videos]
        total = len(video_infos) + offset

        return VideoListResponse(
            videos=video_infos,
            total=total,
            page=page,
            limit=limit
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list videos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve videos"
        )


@router.get("/{video_id}", response_model=VideoInfo)
async def get_video(
    video_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed video information by ID."""
    try:
        video = await video_service.get_video(video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )

        await video_service.update_video_access(video_id)
        return _video_to_info(video)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve video"
        )


@router.put("/{video_id}", response_model=VideoInfo)
async def update_video(
    video_id: str,
    updates: VideoUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update video metadata (title, description, tags)."""
    try:
        video = await video_service.get_video(video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )

        update_data = {}
        if updates.title is not None:
            update_data['title'] = updates.title
        if updates.description is not None:
            update_data['description'] = updates.description
        if updates.tags is not None:
            update_data['tags'] = updates.tags

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided"
            )

        success = await video_service.update_video(video_id, update_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update video"
            )

        updated_video = await video_service.get_video(video_id)
        if not updated_video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found after update"
            )

        return _video_to_info(updated_video)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update video {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update video"
        )


@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Soft delete a video by ID."""
    try:
        success = await video_service.soft_delete_video(video_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )

        return {"message": f"Video {video_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete video {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete video"
        )


@router.get("/{video_id}/download")
async def download_video(
    video_id: str,
    format: str = Query("mp4", description="Download format (mp4, mp4_no_captions, audio, srt)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a download URL for a video or its related files (audio, SRT)."""
    try:
        video = await video_service.get_video(video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )

        await video_service.update_video_access(video_id)

        url_map = {
            "mp4": video.final_video_url,
            "mp4_no_captions": video.video_with_audio_url,
            "audio": video.audio_url,
            "srt": video.srt_url,
        }

        if format not in url_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format. Supported: mp4, mp4_no_captions, audio, srt"
            )

        url = url_map[format]
        if not url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Format '{format}' not available for this video"
            )

        return {"download_url": url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get download URL for video {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get download URL"
        )


@router.get("/stats/overview")
async def get_video_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get aggregate video statistics overview."""
    try:
        stats = await video_service.get_video_stats()
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve video statistics"
        )


# Caption Style Presets Endpoints

@router.get("/caption-styles/presets")
async def get_caption_style_presets(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get all available caption style presets with their default configurations."""
    try:
        available_styles = get_available_caption_style_presets()
        presets = {}

        for style_name in available_styles:
            try:
                preset = get_caption_style_preset(style_name)
                presets[style_name] = preset
            except KeyError:
                logger.warning(f"Style preset not found: {style_name}")
                continue

        return {
            "presets": presets,
            "available_styles": available_styles,
            "total_styles": len(available_styles)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get caption style presets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve caption style presets"
        )


@router.get("/caption-styles/presets/{style_name}")
async def get_caption_style_preset_endpoint(
    style_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get the preset configuration for a specific caption style by name."""
    try:
        preset = get_caption_style_preset(style_name)
        return {
            "style_name": style_name,
            "preset": preset
        }
    except HTTPException:
        raise
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Caption style preset '{style_name}' not found"
        )
    except Exception as e:
        logger.error(f"Failed to get caption style preset '{style_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve caption style preset"
        )


@router.post("/caption-styles/apply-preset")
async def apply_caption_style_preset_endpoint(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Apply a caption style preset to parameters, preserving user overrides. Expects style_name and current_params."""
    style_name = None
    try:
        style_name = request.get("style_name")
        current_params = request.get("current_params", {})

        if not style_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="style_name is required"
            )

        result_params = apply_caption_style_preset(style_name, current_params)

        return {
            "style_name": style_name,
            "applied_params": result_params,
            "preset_applied": True
        }
    except HTTPException:
        raise
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Caption style preset '{style_name or 'unknown'}' not found"
        )
    except Exception as e:
        logger.error(f"Failed to apply caption style preset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply caption style preset"
        )


@router.get("/caption-styles/recommendations")
async def get_style_recommendations_endpoint(
    content_type: str = Query(default="youtube_shorts", description="Content type for recommendations"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get caption style recommendations for a specific content type (tiktok_viral, youtube_shorts, etc.)."""
    try:
        recommendations = get_style_recommendations(content_type)

        return {
            "content_type": content_type,
            "recommended_styles": recommendations,
            "total_recommendations": len(recommendations)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get style recommendations for '{content_type}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve style recommendations"
        )


@router.get("/caption-styles/best-practices")
async def get_caption_best_practices_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get caption best practices and guidelines for styling, positioning, and platform optimization."""
    try:
        best_practices = get_caption_best_practices()

        return {
            "best_practices": best_practices,
            "last_updated": "2025",
            "version": "2025"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get caption best practices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve caption best practices"
        )
