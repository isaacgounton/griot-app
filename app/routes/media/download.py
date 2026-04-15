"""
Routes for downloading media with enhanced yt-dlp capabilities.
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models import MediaDownloadRequest, JobResponse, JobType
from app.services.media.download_service import download_service
from app.services.job_queue import job_queue
from app.utils.auth import get_current_user
import uuid
import logging
import yt_dlp

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Media"])


@router.post("/download", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def download_media(
    request: MediaDownloadRequest,
    _: dict[str, Any] = Depends(get_current_user),  # API key validation (not used in function)
):
    """Download media from URLs using yt-dlp. Supports video platforms and direct file downloads with subtitle extraction, thumbnail generation, and metadata embedding."""
    try:
        # Validate URL
        if not request.url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL is required"
            )

        # Prepare job data with all enhanced features
        job_id = str(uuid.uuid4())
        job_data = {
            "url": str(request.url),
            "format": request.format,
            "file_name": request.file_name,
            "cookies_url": request.cookies_url,
            "extract_subtitles": request.extract_subtitles,
            "subtitle_languages": request.subtitle_languages,
            "subtitle_formats": request.subtitle_formats,
            "extract_thumbnail": request.extract_thumbnail,
            "embed_metadata": request.embed_metadata,
            "thumbnail_format": request.thumbnail_format
        }

        # Handle sync vs async processing
        if request.sync:
            # Process synchronously
            try:
                # Use enhanced download method for sync mode too
                result = await download_service.process_enhanced_media_download(job_id, job_data)
                logger.info(f"Completed synchronous enhanced media download for URL: {request.url}")
                return JobResponse(
                    job_id=job_id,
                    status="completed"
                )
            except Exception as e:
                logger.error(f"Error in synchronous enhanced media download: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Enhanced media download failed: {str(e)}"
                )
        else:
            # Create async job for enhanced download
            async def process_enhanced_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
                return await download_service.process_enhanced_media_download(job_id, data)

            # Queue the job using consistent pattern
            await job_queue.add_job(
                job_id=job_id,
                job_type=JobType.MEDIA_DOWNLOAD,
                process_func=process_enhanced_wrapper,
                data=job_data
            )

            logger.info(f"Created enhanced media download job {job_id} for URL: {request.url}")

            return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating media download job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create media download job"
        )


@router.get("/info")
async def get_media_info(
    url: str = Query(..., description="URL to extract information from"),
    _: dict[str, Any] = Depends(get_current_user),
):
    """Extract media information (formats, subtitles, duration, metadata) without downloading."""
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)

                # Extract available formats
                formats = []
                if info.get('formats'):
                    for fmt in info['formats']:
                        if fmt.get('vcodec') != 'none':  # Video formats
                            format_info = {
                                'format_id': fmt.get('format_id'),
                                'ext': fmt.get('ext'),
                                'resolution': fmt.get('resolution'),
                                'fps': fmt.get('fps'),
                                'filesize': fmt.get('filesize'),
                                'quality': fmt.get('format_note'),
                            }
                            formats.append(format_info)

                # Extract subtitle information
                subtitles = {}
                if info.get('subtitles'):
                    for lang, subs in info['subtitles'].items():
                        subtitles[lang] = [sub.get('ext') for sub in subs]

                return {
                    "id": info.get('id'),
                    "title": info.get('title'),
                    "description": info.get('description'),
                    "uploader": info.get('uploader'),
                    "duration": info.get('duration'),
                    "upload_date": info.get('upload_date'),
                    "view_count": info.get('view_count'),
                    "like_count": info.get('like_count'),
                    "thumbnail": info.get('thumbnail'),
                    "formats": formats,
                    "subtitles": subtitles,
                    "has_chapters": bool(info.get('chapters')),
                    "webpage_url": info.get('webpage_url'),
                }

            except Exception as e:
                logger.error(f"Error extracting info for {url}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to extract media info: {str(e)}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_media_info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract media information"
        )

@router.get("/extractors")
async def get_supported_extractors(_: dict[str, Any] = Depends(get_current_user)):
    """List supported yt-dlp extractors/platforms grouped by category."""
    try:
        ydl_opts = {"quiet": True, "no_warnings": True}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            extractors = ydl._ies  # Internal list of extractors

            # Group extractors by category
            categories = {
                "video": [],
                "music": [],
                "social": [],
                "general": []
            }

            for extractor in sorted(extractors, key=lambda x: x.IE_NAME.lower()):
                name = extractor.IE_NAME
                desc = getattr(extractor, 'IE_DESC', name)

                extractor_info = {
                    "name": name,
                    "description": desc,
                }

                # Categorize based on name
                if any(platform in name.lower() for platform in ['youtube', 'vimeo', 'dailymotion']):
                    categories["video"].append(extractor_info)
                elif any(platform in name.lower() for platform in ['soundcloud', 'spotify', 'bandcamp']):
                    categories["music"].append(extractor_info)
                elif any(platform in name.lower() for platform in ['twitter', 'instagram', 'facebook', 'tiktok']):
                    categories["social"].append(extractor_info)
                else:
                    categories["general"].append(extractor_info)

            return {
                "total_extractors": len(extractors),
                "categories": categories
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting extractors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get supported extractors"
        )
