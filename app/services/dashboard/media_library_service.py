"""
Comprehensive media library service for managing all types of generated content.
Handles videos, audio, images, and documents in a unified system.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Union
from sqlalchemy import select, update, delete, func, and_, or_
from app.database import MediaRecord, MediaType, MediaCategory, VideoRecord, database_service
from app.models import Job, JobStatus
from loguru import logger

class MediaLibraryService:
    """Service for managing all media types in a unified library."""
    
    def _ensure_timezone_aware(self, dt: datetime) -> datetime:
        """Ensure datetime is timezone-aware (UTC)."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    
    def _utcnow(self) -> datetime:
        """Get current UTC time as timezone-naive datetime for database compatibility."""
        return datetime.now(timezone.utc).replace(tzinfo=None)
    
    async def save_media_from_job(self, job: Job) -> Optional[MediaRecord]:
        """
        Create and save a media record from a completed job.
        
        Args:
            job: Completed job with media generation results
        
        Returns:
            MediaRecord if successful, None otherwise
        """
        if job.status != JobStatus.COMPLETED or not job.result:
            logger.warning(f"Job {job.id} is not completed or has no result")
            return None
        
        # Determine media type and category from job operation
        media_info = self._get_media_info_from_job(job)
        if not media_info:
            logger.warning(f"Job {job.id} operation '{job.operation}' not supported for media library")
            return None
        
        media_type, category = media_info
        
        # Extract primary URL and metadata from job result
        result = job.result
        primary_url = self._extract_primary_url(result, media_type)
        
        if not primary_url:
            # For DOCUMENT type, try to persist text content as a text file to S3 and use that as primary URL
            if media_type == MediaType.DOCUMENT and (result.get('text') or result.get('transcript') or result.get('script')):
                try:
                    from app.services.pollinations import pollinations_service
                    text_content = (result.get('text') or result.get('transcript') or result.get('script'))
                    if not text_content:
                        raise ValueError("No text content to persist")
                    filename = f"document-{job.id}.txt"
                    # Convert text to bytes
                    text_bytes = text_content.encode('utf-8')
                    file_url = await pollinations_service.save_generated_content_to_s3(
                        text_bytes,
                        filename,
                        "text/plain"
                    )
                    primary_url = file_url
                except Exception as e:
                    logger.warning(f"Failed to persist document text for job {job.id} to S3: {e}")
            if not primary_url:
                logger.error(f"No primary URL found in job {job.id} result for media type {media_type}")
                return None
        
        # Generate title from content or operation
        title = self._generate_media_title(result, job.operation, job.params)
        
        # Create media record
        media_record = MediaRecord(
            id=job.id,
            title=title,
            description=self._generate_description(result, job.params, media_type),
            media_type=media_type,
            category=category,
            
            # URLs
            primary_url=primary_url,
            secondary_urls=self._extract_secondary_urls(result, media_type),
            thumbnail_url=result.get('thumbnail_url'),
            
            # Media metadata
            duration_seconds=result.get('duration_seconds') or result.get('video_duration') or result.get('estimated_duration'),
            dimensions=self._extract_dimensions(result),
            file_size_mb=result.get('file_size_mb'),
            format=self._extract_format(result, media_type),
            
            # Content metadata
            word_count=result.get('word_count'),
            text_content=self._extract_text_content(result, job.params),
            
            # Generation metadata
            prompt=self._extract_prompt(job.params),
            model_used=result.get('model_used') or job.params.get('model'),
            provider=job.params.get('provider') or job.params.get('tts_provider') or job.params.get('voice_provider'),
            language=job.params.get('language', 'en'),
            
            # Processing metadata
            processing_time_seconds=result.get('processing_time'),
            generation_params=job.params,
            
            # Organization
            project_id=getattr(job, 'project_id', None),
            
            created_at=self._ensure_timezone_aware(
                datetime.fromisoformat(job.created_at) if isinstance(job.created_at, str) else job.created_at
            ).replace(tzinfo=None)  # Convert to naive datetime for database compatibility
        )
        
        try:
            async for session in database_service.get_session():
                session.add(media_record)
                await session.commit()
                logger.info(f"Saved media record for job {job.id}: {media_record.title}")
                return media_record
        except Exception as e:
            logger.error(f"Failed to save media record for job {job.id}: {e}")
            return None
    
    def _get_media_info_from_job(self, job: Job) -> Optional[tuple[MediaType, MediaCategory]]:
        """Determine media type and category from job operation."""
        operation = job.operation.lower()
        
        # Video operations
        video_mapping = {
            'footage_to_video': MediaCategory.FOOTAGE_TO_VIDEO,
            'aiimage_to_video': MediaCategory.AIIMAGE_TO_VIDEO,
            'scenes_to_video': MediaCategory.SCENES_TO_VIDEO,
            'short_video_creation': MediaCategory.SHORT_VIDEO_CREATION,
            'image_to_video': MediaCategory.IMAGE_TO_VIDEO,
            'video_generation': MediaCategory.VIDEO_GENERATION,
            'video_from_image': MediaCategory.VIDEO_FROM_IMAGE,
            'wavespeed_text_to_video': MediaCategory.VIDEO_GENERATION,
            'wavespeed_image_to_video': MediaCategory.IMAGE_TO_VIDEO,
            'video_concatenation': MediaCategory.VIDEO_GENERATION,
            'video_add_audio': MediaCategory.VIDEO_GENERATION,
            'video_add_captions': MediaCategory.VIDEO_GENERATION,
            'video_overlay': MediaCategory.VIDEO_GENERATION,
            'text_overlay': MediaCategory.VIDEO_GENERATION,
            'ffmpeg_compose': MediaCategory.VIDEO_GENERATION,
            'youtube_shorts': MediaCategory.SHORT_VIDEO_CREATION
        }
        if operation in video_mapping:
            return MediaType.VIDEO, video_mapping[operation]
        
        # Audio operations
        audio_mapping = {
            'text_to_speech': MediaCategory.TEXT_TO_SPEECH,
            'tts': MediaCategory.TEXT_TO_SPEECH,
            'music_generation': MediaCategory.MUSIC_GENERATION,
            'generate_music': MediaCategory.MUSIC_GENERATION,
            'audio_transcription': MediaCategory.AUDIO_TRANSCRIPTION,
            'transcribe': MediaCategory.AUDIO_TRANSCRIPTION,
            'voice_cloning': MediaCategory.VOICE_CLONING,
            'pollinations_audio': MediaCategory.TEXT_TO_SPEECH,
            'media_audio_analysis': MediaCategory.AUDIO_TRANSCRIPTION
        }
        if operation in audio_mapping:
            return MediaType.AUDIO, audio_mapping[operation]
        
        # Image operations
        image_mapping = {
            'image_generation': MediaCategory.IMAGE_GENERATION,
            'generate_image': MediaCategory.IMAGE_GENERATION,
            'image_editing': MediaCategory.IMAGE_EDITING,
            'edit_image': MediaCategory.IMAGE_EDITING,
            'image_upscaling': MediaCategory.IMAGE_UPSCALING,
            'upscale_image': MediaCategory.IMAGE_UPSCALING,
            'pollinations_image': MediaCategory.IMAGE_GENERATION,
            'image_overlay': MediaCategory.IMAGE_EDITING,
            'video_thumbnails': MediaCategory.IMAGE_GENERATION,
            'video_frames': MediaCategory.IMAGE_GENERATION,
            'image_search': MediaCategory.IMAGE_GENERATION,
            'image_enhancement': MediaCategory.IMAGE_EDITING,
            'web_screenshot': MediaCategory.IMAGE_GENERATION  # Web page screenshots
        }
        if operation in image_mapping:
            return MediaType.IMAGE, image_mapping[operation]
        
        # Media processing operations
        processing_mapping = {
            'media_download': MediaCategory.MEDIA_DOWNLOAD,
            'download_media': MediaCategory.MEDIA_DOWNLOAD,
            'media_conversion': MediaCategory.MEDIA_CONVERSION,
            'convert_media': MediaCategory.MEDIA_CONVERSION,
            'metadata_extraction': MediaCategory.METADATA_EXTRACTION,
            'extract_metadata': MediaCategory.METADATA_EXTRACTION,
            'youtube_transcript': MediaCategory.YOUTUBE_TRANSCRIPT,
            'youtube_transcripts': MediaCategory.YOUTUBE_TRANSCRIPT,
            'media_transcription': MediaCategory.AUDIO_TRANSCRIPTION,
            'video_clips': MediaCategory.VIDEO_GENERATION,
            's3_upload': MediaCategory.MEDIA_DOWNLOAD,
            'code_execution': MediaCategory.METADATA_EXTRACTION
        }
        if operation in processing_mapping:
            # Determine media type from result
            result = job.result or {}
            if result.get('video_url') or result.get('final_video_url') or result.get('clip_urls'):
                return MediaType.VIDEO, processing_mapping[operation]
            elif result.get('audio_url') or result.get('pollinations_audio'):
                return MediaType.AUDIO, processing_mapping[operation]
            elif result.get('image_url') or result.get('content_url') or result.get('thumbnail_urls') or result.get('frame_urls'):
                return MediaType.IMAGE, processing_mapping[operation]
            elif result.get('text') or result.get('transcript') or result.get('markdown'):
                return MediaType.DOCUMENT, processing_mapping[operation]
            else:
                return MediaType.DOCUMENT, processing_mapping[operation]
        
        # Document operations
        document_mapping = {
            'document_to_markdown': MediaCategory.METADATA_EXTRACTION,
            'marker_document_conversion': MediaCategory.METADATA_EXTRACTION,
            'pollinations_text': MediaCategory.METADATA_EXTRACTION,
            'pollinations_video_analysis': MediaCategory.METADATA_EXTRACTION,
            'ai_script_generation': MediaCategory.METADATA_EXTRACTION,
            'research_news': MediaCategory.METADATA_EXTRACTION
        }
        if operation in document_mapping:
            return MediaType.DOCUMENT, document_mapping[operation]
        
        return None
    
    def _extract_primary_url(self, result: Dict[str, Any], media_type: MediaType) -> Optional[str]:
        """Extract the primary URL based on media type."""
        if media_type == MediaType.VIDEO:
            # Check various video URL keys in priority order
            video_url = (
                result.get('final_video_url') or 
                result.get('video_url') or 
                result.get('url') or  # Some services return just 'url'
                result.get('file_url')
            )
            if video_url:
                return video_url
            # Check clip_urls list
            clip_urls = result.get('clip_urls')
            if isinstance(clip_urls, list) and clip_urls:
                return clip_urls[0]
            return None
        elif media_type == MediaType.AUDIO:
            return (result.get('audio_url') or 
                   result.get('file_url'))
        elif media_type == MediaType.IMAGE:
            thumbnail_list = result.get('thumbnail_urls')
            thumbnail_url = (thumbnail_list[0] if isinstance(thumbnail_list, list) and thumbnail_list else None)
            frame_list = result.get('frame_urls')
            frame_url = (frame_list[0] if isinstance(frame_list, list) and frame_list else None)
            return (result.get('image_url') or 
                   result.get('screenshot_url') or  # Web screenshot support
                   result.get('content_url') or 
                   result.get('file_url') or
                   thumbnail_url or
                   frame_url)
        elif media_type == MediaType.DOCUMENT:
            # Documents may have a file_url (converted document), or be derived from an image analysis
            # In that case the image_url or content_url should be considered the primary URL.
            return (result.get('file_url') or
                   result.get('image_url') or
                   result.get('content_url') or
                   result.get('url'))
        else:
            return result.get('file_url')
    
    def _extract_secondary_urls(self, result: Dict[str, Any], media_type: MediaType) -> Optional[Dict[str, str]]:
        """Extract secondary URLs (related files)."""
        secondary = {}
        
        if media_type == MediaType.VIDEO:
            if result.get('video_with_audio_url'):
                secondary['video_no_captions'] = result['video_with_audio_url']
            if result.get('audio_url'):
                secondary['audio'] = result['audio_url']
            if result.get('srt_url'):
                secondary['captions'] = result['srt_url']
            if result.get('background_music_url'):
                secondary['background_music'] = result['background_music_url']
        
        elif media_type == MediaType.AUDIO:
            if result.get('srt_url'):
                secondary['transcript'] = result['srt_url']
        
        return secondary if secondary else None
    
    def _extract_dimensions(self, result: Dict[str, Any]) -> Optional[Dict[str, int]]:
        """Extract dimensions from result."""
        if result.get('width') and result.get('height'):
            return {'width': result['width'], 'height': result['height']}
        elif result.get('dimensions'):
            # Handle string format like "512x512"
            dimensions_str = result['dimensions']
            if isinstance(dimensions_str, str):
                try:
                    width, height = map(int, dimensions_str.split('x'))
                    return {'width': width, 'height': height}
                except:
                    pass
            # If it's already a dict, return it
            elif isinstance(dimensions_str, dict):
                return dimensions_str
        elif result.get('resolution'):
            # Parse resolution string like "1080x1920"
            try:
                width, height = map(int, result['resolution'].split('x'))
                return {'width': width, 'height': height}
            except:
                pass
        return None
    
    def _extract_format(self, result: Dict[str, Any], media_type: MediaType) -> Optional[str]:
        """Extract file format."""
        if result.get('format'):
            return result['format']
        elif result.get('response_format'):
            return result['response_format']
        else:
            # Guess from media type
            if media_type == MediaType.VIDEO:
                return 'mp4'
            elif media_type == MediaType.AUDIO:
                return 'mp3'
            elif media_type == MediaType.IMAGE:
                return 'png'
        return None
    
    def _extract_text_content(self, result: Dict[str, Any], params: Dict[str, Any]) -> Optional[str]:
        """Extract text content (script, transcript, etc.)."""
        return (result.get('script_generated') or 
               result.get('transcript') or 
               result.get('text') or 
               params.get('script') or 
               params.get('text'))
    
    def _extract_prompt(self, params: Dict[str, Any]) -> Optional[str]:
        """Extract the original prompt/input."""
        return (params.get('prompt') or 
               params.get('topic') or 
               params.get('text') or 
               params.get('url'))
    
    def _generate_media_title(self, result: Dict[str, Any], operation: str, params: Dict[str, Any]) -> str:
        """Generate a meaningful title for the media."""
        # Try to extract title from content
        content = self._extract_text_content(result, params)
        if content:
            # Take first sentence or first 50 characters
            first_sentence = content.split('.')[0].strip()
            if len(first_sentence) > 10 and len(first_sentence) <= 100:
                return first_sentence
            elif len(content) <= 100:
                return content.strip()
            else:
                return content[:97] + "..."
        
        # Try prompt-based title
        prompt = self._extract_prompt(params)
        if prompt:
            if len(prompt) <= 100:
                return prompt.strip()
            else:
                return prompt[:97] + "..."
        
        # Fallback to operation-based title
        operation_titles = {
            'footage_to_video': 'AI Generated Video',
            'aiimage_to_video': 'Script-Based Video',
            'image_to_video': 'Image to Video',
            'text_to_speech': 'Text-to-Speech Audio',
            'music_generation': 'AI Generated Music',
            'image_generation': 'AI Generated Image',
            'media_download': 'Downloaded Media',
            'media_conversion': 'Converted Media',
            'youtube_transcript': 'YouTube Transcript',
            'pollinations_image': 'Pollinations AI Image',
            'pollinations_audio': 'Pollinations AI Audio',
            'pollinations_text': 'Pollinations AI Text',
            'pollinations_video_analysis': 'Pollinations AI Video Analysis',
            'video_thumbnails': 'Video Thumbnails',
            'video_frames': 'Video Frames',
            'video_clips': 'Video Clips',
            'image_overlay': 'Image Overlay',
            'video_overlay': 'Video Overlay',
            'video_concatenation': 'Video Concatenation',
            'video_add_audio': 'Video with Audio',
            'video_add_captions': 'Video with Captions',
            'ffmpeg_compose': 'FFmpeg Composed Media',
            'document_to_markdown': 'Document to Markdown',
            'ai_script_generation': 'AI Generated Script',
            'research_news': 'Research News'
        }
        
        base_title = operation_titles.get(operation.lower(), 'Generated Media')
        timestamp = self._utcnow().strftime("%Y-%m-%d %H:%M")
        return f"{base_title} - {timestamp}"
    
    def _generate_description(self, result: Dict[str, Any], params: Dict[str, Any], media_type: MediaType) -> Optional[str]:
        """Generate a description for the media."""
        description_parts = []
        
        # Add type-specific info
        if media_type == MediaType.VIDEO:
            if result.get('video_duration'):
                duration = result['video_duration']
                description_parts.append(f"Duration: {duration:.1f}s")
            if params.get('voice_provider') and params.get('voice'):
                description_parts.append(f"Voice: {params['voice_provider']} - {params['voice']}")
        elif media_type == MediaType.AUDIO:
            if result.get('estimated_duration'):
                duration = result['estimated_duration']
                description_parts.append(f"Duration: {duration:.1f}s")
            if params.get('voice') or params.get('tts_provider'):
                voice_info = f"{params.get('tts_provider', '')} - {params.get('voice', '')}".strip(' -')
                if voice_info:
                    description_parts.append(f"Voice: {voice_info}")
        elif media_type == MediaType.IMAGE:
            dimensions = self._extract_dimensions(result)
            if dimensions:
                description_parts.append(f"Size: {dimensions['width']}x{dimensions['height']}")
            if params.get('model'):
                description_parts.append(f"Model: {params['model']}")
        
        # Add common metadata
        if result.get('word_count'):
            description_parts.append(f"Words: {result['word_count']}")
        
        if params.get('language'):
            description_parts.append(f"Language: {params['language'].upper()}")
        
        return " | ".join(description_parts) if description_parts else None
    
    async def get_media(self, media_id: str) -> Optional[MediaRecord]:
        """Get a media record by ID."""
        async for session in database_service.get_session():
            result = await session.execute(
                select(MediaRecord).where(
                    and_(MediaRecord.id == media_id, MediaRecord.is_deleted == False)
                )
            )
            return result.scalar_one_or_none()
    
    async def get_all_media(self,
                           limit: int = 50,
                           offset: int = 0,
                           media_type: Optional[MediaType] = None,
                           category: Optional[MediaCategory] = None,
                           search_query: Optional[str] = None) -> List[MediaRecord]:
        """Get all media with optional filtering."""
        async for session in database_service.get_session():
            query = select(MediaRecord).where(MediaRecord.is_deleted == False)
            
            # Filter by media type
            if media_type:
                query = query.where(MediaRecord.media_type == media_type)
            
            # Filter by category
            if category:
                query = query.where(MediaRecord.category == category)
            
            # Search functionality
            if search_query:
                search_pattern = f"%{search_query}%"
                query = query.where(
                    or_(
                        MediaRecord.title.ilike(search_pattern),
                        MediaRecord.description.ilike(search_pattern),
                        MediaRecord.text_content.ilike(search_pattern),
                        MediaRecord.prompt.ilike(search_pattern)
                    )
                )
            
            query = query.order_by(MediaRecord.created_at.desc()).limit(limit).offset(offset)
            
            result = await session.execute(query)
            return list(result.scalars().all())
        
        return []
    
    async def update_media_access(self, media_id: str, is_download: bool = False) -> bool:
        """Update last accessed time and increment view/download count."""
        async for session in database_service.get_session():
            updates = {
                'last_accessed': self._utcnow(),
                'view_count': MediaRecord.view_count + 1
            }
            if is_download:
                updates['download_count'] = MediaRecord.download_count + 1
            
            result = await session.execute(
                update(MediaRecord)
                .where(MediaRecord.id == media_id)
                .values(**updates)
            )
            await session.commit()
            return getattr(result, 'rowcount', 0) > 0
        
        return False
    
    async def soft_delete_media(self, media_id: str) -> bool:
        """Soft delete a media record (mark as deleted)."""
        async for session in database_service.get_session():
            result = await session.execute(
                update(MediaRecord)
                .where(MediaRecord.id == media_id)
                .values(is_deleted=True, updated_at=self._utcnow())
            )
            await session.commit()
            return getattr(result, 'rowcount', 0) > 0
        
        return False
    
    async def update_media(self, media_id: str, updates: Dict[str, Any]) -> bool:
        """Update media metadata."""
        if not updates:
            return False
        
        # Add updated timestamp
        updates['updated_at'] = self._utcnow()
        
        async for session in database_service.get_session():
            result = await session.execute(
                update(MediaRecord)
                .where(and_(MediaRecord.id == media_id, MediaRecord.is_deleted == False))
                .values(**updates)
            )
            await session.commit()
            return getattr(result, 'rowcount', 0) > 0
        
        return False
    
    async def get_media_stats(self) -> Dict[str, Any]:
        """Get media statistics for dashboard."""
        async for session in database_service.get_session():
            # Total media
            total_result = await session.execute(
                select(func.count(MediaRecord.id)).where(MediaRecord.is_deleted == False)
            )
            total_media = total_result.scalar() or 0
            
            # Media by type
            type_result = await session.execute(
                select(MediaRecord.media_type, func.count(MediaRecord.id))
                .where(MediaRecord.is_deleted == False)
                .group_by(MediaRecord.media_type)
            )
            media_by_type = {str(media_type): count for media_type, count in type_result}
            
            # Media by category
            category_result = await session.execute(
                select(MediaRecord.category, func.count(MediaRecord.id))
                .where(MediaRecord.is_deleted == False)
                .group_by(MediaRecord.category)
            )
            media_by_category = {str(category): count for category, count in category_result}
            
            # Recent media (last 7 days)
            week_ago = self._utcnow() - timedelta(days=7)
            recent_result = await session.execute(
                select(func.count(MediaRecord.id))
                .where(and_(
                    MediaRecord.is_deleted == False,
                    MediaRecord.created_at >= week_ago
                ))
            )
            recent_media = recent_result.scalar() or 0
            
            return {
                "total_media": total_media,
                "media_by_type": media_by_type,
                "media_by_category": media_by_category,
                "recent_media": recent_media
            }
        
        return {
            "total_media": 0,
            "media_by_type": {},
            "media_by_category": {},
            "recent_media": 0
        }

# Global media library service instance
media_library_service = MediaLibraryService()
