"""
Library route for managing and browsing generated content.
Organizes content by type (audio, videos, images, etc.) with S3 direct access.
Uses persistent database storage instead of temporary job queue.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from sqlalchemy import select, func, and_, or_, desc

from app.utils.auth import get_current_user
from app.services.s3 import s3_upload_service, s3_service
from app.database import database_service, MediaRecord, MediaType, MediaCategory, utcnow
from app.utils.logging import get_logger

# Initialize logger
logger = get_logger(module="routes", component="library")

router = APIRouter(tags=["Storage & Jobs"])


class ContentType(str, Enum):
    """Content type enumeration for library organization."""

    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    TEXT = "text"
    ALL = "all"


class ContentItem(BaseModel):
    """Individual content item in the library."""

    job_id: str
    job_type: str
    content_type: ContentType
    title: Optional[str] = None
    description: Optional[str] = None
    file_url: str
    thumbnail_url: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[float] = None  # For video/audio
    dimensions: Optional[Dict[str, int]] = (
        None  # For images/videos {"width": 1920, "height": 1080}
    )
    created_at: str
    updated_at: str
    metadata: Dict[str, Any] = {}
    parameters: Dict[str, Any] = {}


class LibraryResponse(BaseModel):
    """Library response with organized content."""

    content: List[ContentItem]
    total_count: int
    content_type_filter: ContentType
    pagination: Dict[str, Any]


# Mapping of MediaType to ContentType
MEDIA_TYPE_TO_CONTENT_TYPE = {
    "video": ContentType.VIDEO,
    "audio": ContentType.AUDIO,
    "image": ContentType.IMAGE,
    "document": ContentType.TEXT,
    "other": ContentType.TEXT,
}


def get_content_type_from_media_type(media_type) -> ContentType:
    """Map database media type to API content type."""
    # Handle both string and enum values
    if hasattr(media_type, "value"):
        media_type_str = media_type.value
    else:
        media_type_str = str(media_type)

    # Make comparison case-insensitive to handle enum issues
    media_type_str = media_type_str.lower()

    return MEDIA_TYPE_TO_CONTENT_TYPE.get(media_type_str, ContentType.TEXT)


async def generate_presigned_url(s3_key: str, original_url: str = "") -> str:
    """Generate presigned URL for S3 content."""
    try:
        return await s3_service.generate_presigned_url(s3_key, expiration=3600)
    except Exception as e:
        logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
        # Return the original URL as fallback if available
        if original_url:
            logger.info(f"Using original URL as fallback: {original_url}")
            return original_url
        return ""


def extract_s3_key_from_url(s3_url: str) -> str:
    """Extract S3 key from S3 URL."""
    if s3_url.startswith("s3://"):
        # Remove s3:// prefix and bucket name
        parts = s3_url.replace("s3://", "").split("/", 1)
        if len(parts) > 1:
            return parts[1]
    elif s3_url.startswith("https://") and ".s3." in s3_url:
        # Handle HTTPS S3 URLs
        # Extract key from URL path
        from urllib.parse import urlparse

        parsed = urlparse(s3_url)
        return parsed.path.lstrip("/")
    return s3_url


@router.get("/content", response_model=LibraryResponse)
async def get_library_content(
    api_key: Dict[str, Any] = Depends(get_current_user),
    content_type: ContentType = Query(
        ContentType.ALL, description="Filter by content type"
    ),
    limit: int = Query(50, ge=1, le=200, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    search: Optional[str] = Query(
        None, description="Search in titles and descriptions"
    ),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format)"),
):
    """
    Retrieve content from the persistent media library with filtering, search, and pagination.

    Supports filtering by content type (video/audio/image/text), date range, project,
    and full-text search. Returns pre-signed S3 URLs for direct access.
    """
    try:
        async for session in database_service.get_session():
            try:
                # Build base query
                query = select(MediaRecord).where(MediaRecord.is_deleted == False)

                # Apply content type filter with string values to avoid enum issues
                if content_type != ContentType.ALL:
                    if content_type == ContentType.VIDEO:
                        query = query.where(MediaRecord.media_type == "video")
                    elif content_type == ContentType.AUDIO:
                        query = query.where(MediaRecord.media_type == "audio")
                    elif content_type == ContentType.IMAGE:
                        query = query.where(MediaRecord.media_type == "image")
                    elif content_type == ContentType.TEXT:
                        query = query.where(
                            MediaRecord.media_type.in_(["document", "other"])
                        )

                # Apply search filter
                if search:
                    search_term = f"%{search.lower()}%"
                    query = query.where(
                        or_(
                            func.lower(MediaRecord.title).like(search_term),
                            func.lower(MediaRecord.description).like(search_term),
                            func.lower(MediaRecord.text_content).like(search_term),
                            func.lower(MediaRecord.prompt).like(search_term),
                        )
                    )

                # Apply project filter
                if project_id:
                    try:
                        project_id_int = int(project_id)
                        query = query.where(MediaRecord.project_id == project_id_int)
                    except ValueError:
                        pass  # Invalid project ID, ignore filter

                # Apply date filters
                if date_from:
                    try:
                        date_from_dt = datetime.fromisoformat(
                            date_from.replace("Z", "+00:00")
                        )
                        query = query.where(MediaRecord.created_at >= date_from_dt)
                    except ValueError:
                        pass  # Invalid date format, ignore filter

                if date_to:
                    try:
                        date_to_dt = datetime.fromisoformat(
                            date_to.replace("Z", "+00:00")
                        )
                        query = query.where(MediaRecord.created_at <= date_to_dt)
                    except ValueError:
                        pass  # Invalid date format, ignore filter

                # Get total count with the same filters as the main query
                try:
                    # Start with the same base query
                    count_query = select(func.count(MediaRecord.id)).where(
                        MediaRecord.is_deleted == False
                    )

                    # Apply the same content type filter
                    if content_type != ContentType.ALL:
                        if content_type == ContentType.VIDEO:
                            count_query = count_query.where(
                                MediaRecord.media_type == "video"
                            )
                        elif content_type == ContentType.AUDIO:
                            count_query = count_query.where(
                                MediaRecord.media_type == "audio"
                            )
                        elif content_type == ContentType.IMAGE:
                            count_query = count_query.where(
                                MediaRecord.media_type == "image"
                            )
                        elif content_type == ContentType.TEXT:
                            count_query = count_query.where(
                                MediaRecord.media_type.in_(["document", "other"])
                            )

                    # Apply the same search filter
                    if search:
                        search_term = f"%{search.lower()}%"
                        count_query = count_query.where(
                            or_(
                                func.lower(MediaRecord.title).like(search_term),
                                func.lower(MediaRecord.description).like(search_term),
                                func.lower(MediaRecord.text_content).like(search_term),
                                func.lower(MediaRecord.prompt).like(search_term),
                            )
                        )

                    # Apply the same project filter
                    if project_id:
                        try:
                            project_id_int = int(project_id)
                            count_query = count_query.where(
                                MediaRecord.project_id == project_id_int
                            )
                        except ValueError:
                            pass  # Invalid project ID, ignore filter

                    # Apply the same date filters
                    if date_from:
                        try:
                            date_from_dt = datetime.fromisoformat(
                                date_from.replace("Z", "+00:00")
                            )
                            count_query = count_query.where(
                                MediaRecord.created_at >= date_from_dt
                            )
                        except ValueError:
                            pass  # Invalid date format, ignore filter

                    if date_to:
                        try:
                            date_to_dt = datetime.fromisoformat(
                                date_to.replace("Z", "+00:00")
                            )
                            count_query = count_query.where(
                                MediaRecord.created_at <= date_to_dt
                            )
                        except ValueError:
                            pass  # Invalid date format, ignore filter

                    count_result = await session.execute(count_query)
                    total_count = count_result.scalar() or 0
                except Exception as count_error:
                    logger.warning(f"Could not get filtered total count: {count_error}")
                    total_count = 0

                # Apply ordering and pagination
                query = query.order_by(desc(MediaRecord.created_at))
                query = query.offset(offset).limit(limit)

                logger.debug(
                    f"Executing library query with content_type={content_type}, limit={limit}, offset={offset}"
                )

                # Execute query with error handling
                try:
                    result = await session.execute(query)
                    media_records = result.scalars().all()
                except Exception as query_error:
                    logger.warning(
                        f"Query error, returning empty results: {query_error}"
                    )
                    media_records = []

                logger.debug(f"Found {len(media_records)} media records")

                # Convert to ContentItem objects
                content_items = []
                for record in media_records:
                    try:
                        # Use the direct URLs (assuming they are public)
                        file_url = record.primary_url
                        if file_url and file_url.count("https://") > 1:
                            parts = file_url.split("https://")
                            if len(parts) > 2:
                                file_url = "https://" + parts[-1]

                        thumbnail_url = record.thumbnail_url
                        if thumbnail_url and thumbnail_url.count("https://") > 1:
                            parts = thumbnail_url.split("https://")
                            if len(parts) > 2:
                                thumbnail_url = "https://" + parts[-1]

                        # Build dimensions dict if available
                        dimensions = None
                        if record.dimensions and isinstance(record.dimensions, dict):
                            dimensions = record.dimensions

                        # Convert file size from MB to bytes for consistency
                        file_size_bytes = None
                        if record.file_size_mb:
                            file_size_bytes = int(record.file_size_mb * 1024 * 1024)

                        content_item = ContentItem(
                            job_id=record.id,
                            job_type=record.category.value
                            if hasattr(record.category, "value")
                            else str(record.category),
                            content_type=get_content_type_from_media_type(
                                record.media_type
                            ),
                            title=record.title,
                            description=record.description,
                            file_url=file_url,
                            thumbnail_url=thumbnail_url,
                            file_size=file_size_bytes,
                            duration=record.duration_seconds,
                            dimensions=dimensions,
                            created_at=record.created_at.isoformat(),
                            updated_at=record.updated_at.isoformat(),
                            metadata={
                                "format": record.format,
                                "provider": record.provider,
                                "model_used": record.model_used,
                                "language": record.language,
                                "word_count": record.word_count,
                                "processing_time": record.processing_time_seconds,
                                "download_count": record.download_count,
                                "view_count": record.view_count,
                                "is_favorite": record.is_favorite,
                                "secondary_urls": record.secondary_urls or {},
                            },
                            parameters=record.generation_params or {},
                        )
                        content_items.append(content_item)

                    except Exception as e:
                        logger.warning(
                            f"Error processing media record {record.id}: {e}"
                        )
                        continue

                # Prepare pagination info
                current_page = (offset // limit) + 1 if limit > 0 else 1
                total_pages = (
                    (total_count // limit) + (1 if total_count % limit > 0 else 0)
                    if limit > 0
                    else 1
                )

                pagination = {
                    "page": current_page,
                    "total_pages": total_pages,
                    "limit": limit,
                    "offset": offset,
                    "total_count": total_count,
                    "has_next": offset + limit < (total_count or 0),
                    "has_previous": offset > 0,
                    "next_offset": offset + limit
                    if offset + limit < (total_count or 0)
                    else None,
                    "previous_offset": max(0, offset - limit) if offset > 0 else None,
                }

                return LibraryResponse(
                    content=content_items,
                    total_count=total_count or 0,
                    content_type_filter=content_type,
                    pagination=pagination,
                )
            except Exception as session_error:
                logger.error(
                    f"Session error in get_library_content: {session_error}",
                    exc_info=True,
                )
                # Return empty library instead of 500 error
                return LibraryResponse(
                    content=[],
                    total_count=0,
                    content_type_filter=content_type,
                    pagination={"limit": limit, "offset": offset, "total_count": 0},
                )

    except Exception as e:
        logger.error(f"Error fetching library content: {e}", exc_info=True)
        # Return empty library instead of 500 error
        return LibraryResponse(
            content=[],
            total_count=0,
            content_type_filter=content_type,
            pagination={"limit": limit, "offset": offset, "total_count": 0},
        )


@router.get("/content/{media_id}")
async def get_content_item(
    media_id: str, api_key: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific content item by media ID."""
    try:
        async for session in database_service.get_session():
            # Query for the media record
            query = select(MediaRecord).where(
                and_(MediaRecord.id == media_id, MediaRecord.is_deleted == False)
            )

            result = await session.execute(query)
            record = result.scalar_one_or_none()

            if not record:
                raise HTTPException(status_code=404, detail="Content item not found")

            # Update view count
            record.view_count += 1
            record.last_accessed = utcnow()
            await session.commit()

            # Use the direct URLs (assuming they are public)
            # Clean up any malformed URLs that might have double prefixes
            file_url = record.primary_url
            if file_url and file_url.count("https://") > 1:
                # Fix double-prefixed URLs
                parts = file_url.split("https://")
                if len(parts) > 2:
                    file_url = "https://" + parts[-1]  # Use the last part

            thumbnail_url = record.thumbnail_url
            if thumbnail_url and thumbnail_url.count("https://") > 1:
                # Fix double-prefixed URLs
                parts = thumbnail_url.split("https://")
                if len(parts) > 2:
                    thumbnail_url = "https://" + parts[-1]  # Use the last part

            # Build dimensions dict if available
            dimensions = None
            if record.dimensions and isinstance(record.dimensions, dict):
                dimensions = record.dimensions

            # Convert file size from MB to bytes for consistency
            file_size_bytes = None
            if record.file_size_mb:
                file_size_bytes = int(record.file_size_mb * 1024 * 1024)

            content_item = ContentItem(
                job_id=record.id,
                job_type=record.category.value
                if hasattr(record.category, "value")
                else str(record.category),
                content_type=get_content_type_from_media_type(record.media_type),
                title=record.title,
                description=record.description,
                file_url=file_url,
                thumbnail_url=thumbnail_url,
                file_size=file_size_bytes,
                duration=record.duration_seconds,
                dimensions=dimensions,
                created_at=record.created_at.isoformat(),
                updated_at=record.updated_at.isoformat(),
                metadata={
                    "format": record.format,
                    "provider": record.provider,
                    "model_used": record.model_used,
                    "language": record.language,
                    "word_count": record.word_count,
                    "processing_time": record.processing_time_seconds,
                    "download_count": record.download_count,
                    "view_count": record.view_count,
                    "is_favorite": record.is_favorite,
                    "secondary_urls": record.secondary_urls or {},
                },
                parameters=record.generation_params or {},
            )

            return content_item

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching content item {media_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch content item: {str(e)}"
        )


@router.get("/stats")
async def get_library_stats(api_key: Dict[str, Any] = Depends(get_current_user)):
    """Get library statistics grouped by content type."""
    try:
        async for session in database_service.get_session():
            try:
                # Initialize stats with default values
                stats = {"video": 0, "audio": 0, "image": 0, "text": 0, "total": 0}

                # Try to get counts, but fallback gracefully if table doesn't exist
                try:
                    # Base query for non-deleted items
                    base_query = select(func.count(MediaRecord.id)).where(
                        MediaRecord.is_deleted == False
                    )

                    # Get counts by media type
                    video_count_query = base_query.where(
                        MediaRecord.media_type == "video"
                    )
                    video_result = await session.execute(video_count_query)
                    stats["video"] = video_result.scalar() or 0

                    audio_count_query = base_query.where(
                        MediaRecord.media_type == "audio"
                    )
                    audio_result = await session.execute(audio_count_query)
                    stats["audio"] = audio_result.scalar() or 0

                    image_count_query = base_query.where(
                        MediaRecord.media_type == "image"
                    )
                    image_result = await session.execute(image_count_query)
                    stats["image"] = image_result.scalar() or 0

                    text_count_query = base_query.where(
                        MediaRecord.media_type.in_(["document", "other"])
                    )
                    text_result = await session.execute(text_count_query)
                    stats["text"] = text_result.scalar() or 0

                    # Get total count
                    total_query = select(func.count(MediaRecord.id)).where(
                        MediaRecord.is_deleted == False
                    )
                    total_result = await session.execute(total_query)
                    stats["total"] = total_result.scalar() or 0

                except Exception as count_error:
                    logger.warning(
                        f"Could not get detailed stats, returning zeros: {count_error}"
                    )
                    # Return default stats
                    pass

                return {"stats": stats, "total_items": stats["total"]}
            except Exception as db_error:
                logger.error(
                    f"Database error in get_library_stats: {db_error}", exc_info=True
                )
                # Return default stats instead of failing completely
                return {
                    "stats": {
                        "video": 0,
                        "audio": 0,
                        "image": 0,
                        "text": 0,
                        "total": 0,
                    },
                    "total_items": 0,
                }

    except Exception as e:
        logger.error(f"Error fetching library stats: {e}", exc_info=True)
        # Return default stats instead of 500 error
        return {
            "stats": {"video": 0, "audio": 0, "image": 0, "text": 0, "total": 0},
            "total_items": 0,
        }


@router.post("/fix-enum-values")
async def fix_enum_values(api_key: Dict[str, Any] = Depends(get_current_user)):
    """
    Fix incorrect enum values in the media library.
    This endpoint fixes records that have uppercase enum values instead of lowercase.
    """
    try:
        async for session in database_service.get_session():
            from sqlalchemy import text

            # Check for problematic records
            check_query = text("""
                SELECT id, category::text as category_text, media_type::text as media_type_text
                FROM media_library
                WHERE category::text LIKE '%_GENERATION%'
                   OR category::text LIKE '%_EDITING%'
                   OR category::text LIKE '%_UPSCALING%'
                   OR media_type::text IN ('VIDEO', 'AUDIO', 'IMAGE', 'DOCUMENT', 'OTHER')
                LIMIT 100;
            """)

            result = await session.execute(check_query)
            problematic_records = result.fetchall()

            if not problematic_records:
                return {
                    "message": "No records found with incorrect enum values",
                    "fixed_count": 0,
                    "problematic_records": [],
                }

            logger.info(
                f"Found {len(problematic_records)} records with incorrect enum values"
            )

            # Define the mapping for fixes
            category_fixes = {
                "IMAGE_GENERATION": "image_generation",
                "IMAGE_EDITING": "image_editing",
                "IMAGE_UPSCALING": "image_upscaling",
                "TEXT_TO_SPEECH": "text_to_speech",
                "MUSIC_GENERATION": "music_generation",
                "AUDIO_TRANSCRIPTION": "audio_transcription",
                "VOICE_CLONING": "voice_cloning",
                "FOOTAGE_TO_VIDEO": "footage_to_video",
                "AIIMAGE_TO_VIDEO": "aiimage_to_video",
                "SCENES_TO_VIDEO": "scenes_to_video",
                "SHORT_VIDEO_CREATION": "short_video_creation",
                "IMAGE_TO_VIDEO": "image_to_video",
                "MEDIA_DOWNLOAD": "media_download",
                "MEDIA_CONVERSION": "media_conversion",
                "METADATA_EXTRACTION": "metadata_extraction",
                "YOUTUBE_TRANSCRIPT": "youtube_transcript",
            }

            media_type_fixes = {
                "VIDEO": "video",
                "AUDIO": "audio",
                "IMAGE": "image",
                "DOCUMENT": "document",
                "OTHER": "other",
            }

            fixed_count = 0
            fixed_records = []

            # Fix category values
            for old_val, new_val in category_fixes.items():
                try:
                    update_query = text("""
                        UPDATE media_library
                        SET category = :new_val::mediacategory,
                            updated_at = NOW()
                        WHERE category::text = :old_val
                        RETURNING id, title;
                    """)
                    update_result = await session.execute(update_query, {"new_val": new_val, "old_val": old_val})
                    updated_records = update_result.fetchall()

                    if updated_records:
                        fixed_count += len(updated_records)
                        for record in updated_records:
                            fixed_records.append(
                                {
                                    "id": record[0],
                                    "title": record[1],
                                    "field": "category",
                                    "old_value": old_val,
                                    "new_value": new_val,
                                }
                            )
                        logger.info(
                            f"Fixed {len(updated_records)} records: category {old_val} → {new_val}"
                        )

                except Exception as e:
                    logger.error(f"Failed to fix category {old_val}: {e}")

            # Fix media_type values
            for old_val, new_val in media_type_fixes.items():
                try:
                    update_query = text("""
                        UPDATE media_library
                        SET media_type = :new_val::mediatype,
                            updated_at = NOW()
                        WHERE media_type::text = :old_val
                        RETURNING id, title;
                    """)
                    update_result = await session.execute(update_query, {"new_val": new_val, "old_val": old_val})
                    updated_records = update_result.fetchall()

                    if updated_records:
                        fixed_count += len(updated_records)
                        for record in updated_records:
                            fixed_records.append(
                                {
                                    "id": record[0],
                                    "title": record[1],
                                    "field": "media_type",
                                    "old_value": old_val,
                                    "new_value": new_val,
                                }
                            )
                        logger.info(
                            f"Fixed {len(updated_records)} records: media_type {old_val} → {new_val}"
                        )

                except Exception as e:
                    logger.error(f"Failed to fix media_type {old_val}: {e}")

            await session.commit()

            return {
                "message": f"Successfully fixed {fixed_count} records with incorrect enum values",
                "fixed_count": fixed_count,
                "fixed_records": fixed_records[:10],  # Return first 10 for brevity
                "total_problematic_found": len(problematic_records),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fixing enum values: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fix enum values: {str(e)}"
        )


@router.post("/scan-s3")
async def scan_s3_for_content(api_key: Dict[str, Any] = Depends(get_current_user)):
    """
    Scan S3 bucket for content that might not be in the database.
    This is a utility endpoint for discovering existing content.
    """
    try:
        # Note: S3 bucket listing feature not yet implemented
        # TODO: Implement s3_service.list_objects method
        bucket_contents = []  # await s3_service.list_objects("")

        if not bucket_contents:
            return {
                "message": "No content found in S3 bucket",
                "files_found": 0,
                "already_in_library": 0,
                "new_discoveries": 0,
            }

        async for session in database_service.get_session():
            # Get existing media record IDs
            existing_query = select(MediaRecord.id).where(
                MediaRecord.is_deleted == False
            )
            result = await session.execute(existing_query)
            existing_ids = {row[0] for row in result}

            files_found = len(bucket_contents)
            already_in_library = 0
            new_discoveries = []

            for obj in bucket_contents:
                key = obj.get("Key", "")

                # Extract potential job ID from S3 key path
                # Assuming structure like: "jobs/job-uuid/output.mp4"
                if "/jobs/" in key or "/media/" in key:
                    path_parts = key.split("/")
                    potential_job_id = None

                    for part in path_parts:
                        # Look for UUID-like strings
                        if len(part) >= 32 and "-" in part:
                            potential_job_id = part
                            break

                    if potential_job_id:
                        if potential_job_id in existing_ids:
                            already_in_library += 1
                        else:
                            new_discoveries.append(
                                {
                                    "s3_key": key,
                                    "potential_job_id": potential_job_id,
                                    "file_size": obj.get("Size", 0),
                                    "last_modified": obj.get(
                                        "LastModified", ""
                                    ).isoformat()
                                    if obj.get("LastModified")
                                    else None,
                                }
                            )

            return {
                "message": f"S3 scan completed. Found {files_found} files in bucket.",
                "files_found": files_found,
                "already_in_library": already_in_library,
                "new_discoveries": len(new_discoveries),
                "discovery_details": new_discoveries[
                    :50
                ],  # Limit to first 50 for response size
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning S3 for content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to scan S3: {str(e)}")


@router.post("/favorite/{media_id}")
async def toggle_favorite(
    media_id: str, api_key: Dict[str, Any] = Depends(get_current_user)
):
    """Toggle favorite status for a media item."""
    try:
        async for session in database_service.get_session():
            query = select(MediaRecord).where(
                and_(MediaRecord.id == media_id, MediaRecord.is_deleted == False)
            )

            result = await session.execute(query)
            record = result.scalar_one_or_none()

            if not record:
                raise HTTPException(status_code=404, detail="Content item not found")

            # Toggle favorite status
            record.is_favorite = not record.is_favorite
            record.updated_at = utcnow()

            await session.commit()

            return {
                "media_id": media_id,
                "is_favorite": record.is_favorite,
                "message": f"Item {'added to' if record.is_favorite else 'removed from'} favorites",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling favorite for {media_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to toggle favorite: {str(e)}"
        )


@router.delete("/content/{media_id}")
async def delete_content_item(
    media_id: str, api_key: Dict[str, Any] = Depends(get_current_user)
):
    """Soft delete a content item (marks as deleted, doesn't remove from S3)."""
    try:
        async for session in database_service.get_session():
            query = select(MediaRecord).where(
                and_(MediaRecord.id == media_id, MediaRecord.is_deleted == False)
            )

            result = await session.execute(query)
            record = result.scalar_one_or_none()

            if not record:
                raise HTTPException(status_code=404, detail="Content item not found")

            # Soft delete
            record.is_deleted = True
            record.updated_at = utcnow()

            await session.commit()

            return {
                "media_id": media_id,
                "message": "Content item deleted successfully",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting content item {media_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete content item: {str(e)}"
        )


@router.delete("/content/all/everything")
async def delete_all_content(
    confirm: bool = Query(False, description="Must be set to true to confirm deletion"),
    api_key: Dict[str, Any] = Depends(get_current_user),
):
    """
    Delete ALL content from the library AND S3.
    DANGER: This action is irreversible. It will delete all library records and their associated S3 files.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Confirmation required. Set 'confirm=true' parameter.",
        )

    try:
        async for session in database_service.get_session():
            # Get all media records (including soft deleted ones)
            query = select(MediaRecord)
            result = await session.execute(query)
            records = result.scalars().all()

            deleted_count = 0
            s3_files_deleted = 0
            errors = 0

            for record in records:
                try:
                    # Delete from S3 if URL exists
                    if record.primary_url:
                        s3_key = extract_s3_key_from_url(record.primary_url)
                        if s3_key:
                            # Delete from S3
                            await s3_service.delete_file(s3_key)
                            s3_files_deleted += 1

                    # Delete secondary files if any
                    if record.secondary_urls:
                        for _, url in record.secondary_urls.items():
                            s3_key = extract_s3_key_from_url(url)
                            if s3_key:
                                await s3_service.delete_file(s3_key)
                                s3_files_deleted += 1

                    # Delete thumbnails
                    if record.thumbnail_url:
                        s3_key = extract_s3_key_from_url(record.thumbnail_url)
                        if s3_key:
                            await s3_service.delete_file(s3_key)
                            s3_files_deleted += 1

                    # Hard delete from database
                    await session.delete(record)
                    deleted_count += 1

                except Exception as e:
                    logger.error(f"Error deleting record {record.id}: {e}")
                    errors += 1

            await session.commit()

            return {
                "message": f"Successfully deleted {deleted_count} library items and {s3_files_deleted} S3 files.",
                "deleted_records": deleted_count,
                "deleted_s3_files": s3_files_deleted,
                "errors": errors,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting all content: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete all content: {str(e)}"
        )


@router.post("/cleanup/orphaned-files")
async def cleanup_orphaned_files(
    confirm: bool = Query(
        False, description="Confirm deletion of records with missing S3 files"
    ),
    dry_run: bool = Query(
        True, description="If true, only counts missing files without deleting"
    ),
    api_key: Dict[str, Any] = Depends(get_current_user),
):
    """
    Scan library for records pointing to missing S3 files and delete them.
    This fixes 'broken' library entries that no longer have a corresponding file.
    """
    try:
        async for session in database_service.get_session():
            # Get all media records
            query = select(MediaRecord)
            result = await session.execute(query)
            records = result.scalars().all()

            checked_count = 0
            missing_files_count = 0
            records_to_delete = []

            for record in records:
                try:
                    checked_count += 1

                    # Check primary URL
                    if record.primary_url:
                        s3_key = extract_s3_key_from_url(record.primary_url)
                        if s3_key:
                            exists = await s3_service.check_file_exists(s3_key)
                            if not exists:
                                logger.info(
                                    f"Missing S3 file for record {record.id}: {s3_key}"
                                )
                                missing_files_count += 1
                                records_to_delete.append(
                                    {
                                        "id": record.id,
                                        "title": record.title,
                                        "reason": "Missing primary file",
                                        "key": s3_key,
                                    }
                                )
                                continue  # Skip checking others if primary is missing

                    # Note: We could check thumbnail/secondary too, but missing primary is the main issue

                except Exception as e:
                    logger.error(f"Error checking record {record.id}: {e}")

            # Delete records if confirmed and not dry run
            deleted_count = 0
            if not dry_run and confirm and records_to_delete:
                for item in records_to_delete:
                    # Fetch record again to ensure it's attached to session
                    rec_query = select(MediaRecord).where(MediaRecord.id == item["id"])
                    rec_result = await session.execute(rec_query)
                    rec = rec_result.scalar_one_or_none()

                    if rec:
                        await session.delete(rec)
                        deleted_count += 1

                await session.commit()

            return {
                "message": f"Scan complete. Found {missing_files_count} records with missing files.",
                "total_checked": checked_count,
                "missing_files_found": missing_files_count,
                "deleted_records": deleted_count,
                "dry_run": dry_run,
                "details": records_to_delete[:50],  # Limit response size
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning orphaned files: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to cleanup orphaned files: {str(e)}"
        )


@router.post("/content/{media_id}/schedule")
async def schedule_content_item(
    media_id: str, request: dict, api_key: Dict[str, Any] = Depends(get_current_user)
):
    """Schedule a library content item to social media via Postiz."""
    try:
        async for session in database_service.get_session():
            # Get the media record
            query = select(MediaRecord).where(
                and_(MediaRecord.id == media_id, MediaRecord.is_deleted == False)
            )

            result = await session.execute(query)
            record = result.scalar_one_or_none()

            if not record:
                raise HTTPException(status_code=404, detail="Content item not found")

            # Import postiz_service here to avoid circular imports
            from app.services.postiz import postiz_service

            # Extract parameters from request
            content = request.get("content", "")
            integrations = request.get("integrations", [])
            post_type = request.get("post_type", "now")
            schedule_date = request.get("schedule_date")
            tags = request.get("tags", [])

            if not integrations:
                raise HTTPException(
                    status_code=400, detail="At least one integration must be selected"
                )

            # Generate default content if not provided
            if not content:
                content_type_name = get_content_type_from_media_type(
                    record.media_type
                ).value
                content = f"✨ Check out this amazing {content_type_name} from my library! Created with AI automation. #AI #automation #content"

            # Clean up any malformed URLs that might have double prefixes
            file_url = record.primary_url
            if file_url and file_url.count("https://") > 1:
                parts = file_url.split("https://")
                if len(parts) > 2:
                    file_url = "https://" + parts[-1]

            # Debug logging for media URL resolution
            logger.info(f"Postiz scheduling debug - Media ID: {media_id}")
            logger.info(f"  Original URL: {record.primary_url}")
            logger.info(f"  Cleaned URL: {file_url}")
            logger.info(f"  Media Type: {record.media_type}")
            logger.info(
                f"  URL valid: {bool(file_url and (file_url.startswith('http://') or file_url.startswith('https://')))}"
            )

            # Convert schedule_date string to datetime if provided
            schedule_datetime = None
            if schedule_date and post_type == "schedule":
                try:
                    if isinstance(schedule_date, str):
                        # Handle ISO format datetime string
                        schedule_datetime = datetime.fromisoformat(
                            schedule_date.replace("Z", "+00:00")
                        )
                    else:
                        schedule_datetime = schedule_date
                except ValueError as e:
                    raise HTTPException(
                        status_code=400, detail=f"Invalid schedule date format: {e}"
                    )

            # Choose scheduling method based on content type
            if record.media_type == MediaType.VIDEO and file_url:
                # For videos, download from URL and upload to Postiz
                logger.info(f"Scheduling video post with file_url: {file_url}")
                result = await postiz_service.schedule_video_post(
                    video_url=file_url,
                    content=content,
                    integrations=integrations,
                    post_type=post_type,
                    schedule_date=schedule_datetime,
                    tags=tags,
                )
            elif record.media_type == MediaType.IMAGE and file_url:
                # For images, download from URL and upload to Postiz
                logger.info(f"Scheduling image post with file_url: {file_url}")
                result = await postiz_service.schedule_post(
                    content=content,
                    integrations=integrations,
                    post_type=post_type,
                    schedule_date=schedule_datetime,
                    media_paths=[file_url]
                    if file_url
                    and (
                        file_url.startswith("http://")
                        or file_url.startswith("https://")
                    )
                    else None,
                    tags=tags,
                )
            elif record.media_type == MediaType.AUDIO and file_url:
                # For audio, download from URL and upload to Postiz
                logger.info(f"Scheduling audio post with file_url: {file_url}")
                result = await postiz_service.schedule_post(
                    content=content,
                    integrations=integrations,
                    post_type=post_type,
                    schedule_date=schedule_datetime,
                    media_paths=[file_url]
                    if file_url
                    and (
                        file_url.startswith("http://")
                        or file_url.startswith("https://")
                    )
                    else None,
                    tags=tags,
                )
            else:
                # For other content types or when no file_url, use regular posting
                logger.info(
                    f"Scheduling text-only post (media_type: {record.media_type}, file_url: {'present' if file_url else 'missing'})"
                )
                enhanced_content = content
                if file_url and record.media_type in ["document", "text"]:
                    # Only add URL to content for document/text types
                    enhanced_content += f"\n\n🔗 {file_url}"

                result = await postiz_service.schedule_post(
                    content=enhanced_content,
                    integrations=integrations,
                    post_type=post_type,
                    schedule_date=schedule_datetime,
                    tags=tags,
                )

            logger.info(f"Successfully scheduled content item {media_id} to Postiz")
            logger.debug(f"Postiz scheduling result: {result}")

            return {
                "success": True,
                "message": f"Content scheduled successfully to {len(integrations)} platform(s)",
                "media_id": media_id,
                "postiz_result": result,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling content item {media_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to schedule content: {str(e)}"
        )


@router.get("/debug/status")
async def get_library_debug_status():
    """Debug endpoint to check library database status."""
    try:
        async for session in database_service.get_session():
            # Check if table exists and get basic stats
            try:
                total_count_query = select(func.count(MediaRecord.id))
                total_result = await session.execute(total_count_query)
                total_count = total_result.scalar()

                deleted_count_query = select(func.count(MediaRecord.id)).where(
                    MediaRecord.is_deleted == True
                )
                deleted_result = await session.execute(deleted_count_query)
                deleted_count = deleted_result.scalar()

                # Get a sample record if any exist
                sample_query = select(MediaRecord).limit(1)
                sample_result = await session.execute(sample_query)
                sample_record = sample_result.scalar_one_or_none()

                sample_data = None
                if sample_record:
                    sample_data = {
                        "id": sample_record.id,
                        "title": sample_record.title,
                        "media_type": str(sample_record.media_type),
                        "category": str(sample_record.category),
                        "primary_url": sample_record.primary_url,
                        "created_at": sample_record.created_at.isoformat(),
                    }

                return {
                    "status": "ok",
                    "table_exists": True,
                    "total_records": total_count,
                    "active_records": (total_count or 0) - (deleted_count or 0),
                    "deleted_records": deleted_count,
                    "sample_record": sample_data,
                }

            except Exception as e:
                logger.error(f"Database query error: {e}")
                return {"status": "error", "table_exists": False, "error": str(e)}

    except Exception as e:
        logger.error(f"Database connection error: {e}")


@router.post("/debug/save-job/{job_id}")
async def debug_save_job_to_library(
    job_id: str, _: Dict[str, Any] = Depends(get_current_user)
):
    """Debug endpoint to manually save a completed job to the library."""
    try:
        from app.services.job_queue.job_queue import job_queue
        from app.services.dashboard.media_library_service import media_library_service
        from app.models import Job, JobStatus

        # Get the job
        job = await job_queue.get_job_info(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Log job object structure for debugging
        logger.info(f"Job object attributes: {dir(job)}")

        # Get operation from JobInfo object
        operation = getattr(job, "job_type", None)
        status = getattr(job, "status", None)
        params = getattr(job, "data", {})

        # Check if job is completed and has result
        if status != "completed":
            return {
                "success": False,
                "message": f"Job is not completed (status: {status})",
                "job_operation": operation,
                "job_status": status,
                "has_result": bool(getattr(job, "result", None)),
            }

        result = getattr(job, "result", None)
        if not result:
            return {
                "success": False,
                "message": "Job has no result data",
                "job_operation": operation,
                "job_status": status,
                "has_result": False,
            }

        job_model = Job(
            id=job_id,
            operation=operation or "unknown",
            params=params,
            status=JobStatus(status) if status else JobStatus.PENDING,
            result=result,
            error=getattr(job, "error", None),
            created_at=getattr(job, "created_at", ""),
            updated_at=getattr(job, "updated_at", ""),
        )

        logger.info(
            f"Created Job model: operation={job_model.operation}, status={job_model.status}, has_result={bool(job_model.result)}"
        )

        # Try to save to library
        media_record = await media_library_service.save_media_from_job(job_model)

        if media_record:
            return {
                "success": True,
                "message": "Job successfully saved to library",
                "media_id": media_record.id,
                "media_type": media_record.media_type,
                "title": media_record.title,
            }
        else:
            return {
                "success": False,
                "message": "Failed to save job to library",
                "job_operation": operation,
                "job_status": status,
                "has_result": bool(result),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in debug save job: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error saving job to library: {str(e)}"
        )
