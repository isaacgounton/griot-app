"""
Video persistence service for managing video records and metadata.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, func, and_, or_
from app.database import VideoRecord, VideoType, database_service
from app.models import Job, JobStatus
from loguru import logger

class VideoService:
    """Service for managing video records in the database."""
    
    def _ensure_timezone_aware(self, dt: datetime) -> datetime:
        """Ensure datetime is timezone-aware (UTC)."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    
    def _utcnow(self) -> datetime:
        """Get current UTC time as timezone-naive datetime for database compatibility."""
        return datetime.now(timezone.utc).replace(tzinfo=None)
    
    async def save_video_from_job(self, job: Job) -> Optional[VideoRecord]:
        """
        Create and save a video record from a completed job.
        
        Args:
            job: Completed job with video generation results
        
        Returns:
            VideoRecord if successful, None otherwise
        """
        if job.status != JobStatus.COMPLETED or not job.result:
            logger.warning(f"Job {job.id} is not completed or has no result")
            return None
        
        # Map job operation to video type
        video_type_mapping = {
            "footage_to_video": VideoType.FOOTAGE_TO_VIDEO,
            "aiimage_to_video": VideoType.AIIMAGE_TO_VIDEO,
            "scenes_to_video": VideoType.SCENES_TO_VIDEO,
            "short_video_creation": VideoType.SHORT_VIDEO_CREATION,
            "image_to_video": VideoType.IMAGE_TO_VIDEO
        }
        
        video_type = video_type_mapping.get(job.operation.lower(), VideoType.OTHER)
        
        # Extract video URLs and metadata from job result
        result = job.result
        final_video_url = result.get('final_video_url') or result.get('video_url')
        
        if not final_video_url:
            logger.error(f"No video URL found in job {job.id} result")
            return None
        
        # Generate title from script or operation
        title = self._generate_video_title(result, job.operation)
        
        # Create video record
        video_record = VideoRecord(
            id=job.id,
            title=title,
            description=self._generate_description(result, job.params),
            video_type=video_type,
            
            # Video URLs
            final_video_url=final_video_url,
            video_with_audio_url=result.get('video_with_audio_url'),
            audio_url=result.get('audio_url'),
            srt_url=result.get('srt_url'),
            thumbnail_url=result.get('thumbnail_url'),
            
            # Video metadata
            duration_seconds=result.get('video_duration'),
            resolution=job.params.get('resolution') or result.get('resolution'),
            word_count=result.get('word_count'),
            segments_count=result.get('segments_count'),
            
            # Generation metadata
            script_text=result.get('script_generated') or job.params.get('script'),
            voice_provider=job.params.get('voice_provider'),
            voice_name=job.params.get('voice_name'),
            language=job.params.get('language', 'en'),
            
            # Processing metadata
            processing_time_seconds=result.get('processing_time'),
            background_videos_used=result.get('background_videos_used'),
            generation_params=job.params,
            
            # Organization
            project_id=getattr(job, 'project_id', None),
            
            created_at=self._ensure_timezone_aware(
                datetime.fromisoformat(job.created_at) if isinstance(job.created_at, str) else job.created_at
            ).replace(tzinfo=None)  # Convert to naive datetime for database compatibility
        )
        
        try:
            async for session in database_service.get_session():
                session.add(video_record)
                await session.commit()
                logger.info(f"Saved video record for job {job.id}")
                return video_record
        except Exception as e:
            logger.error(f"Failed to save video record for job {job.id}: {e}")
            return None
    
    def _generate_video_title(self, result: Dict[str, Any], operation: str) -> str:
        """Generate a meaningful title for the video."""
        # Try to extract title from script
        script = result.get('script_generated') or result.get('script', '')
        if script:
            # Take first sentence or first 50 characters
            first_sentence = script.split('.')[0].strip()
            if len(first_sentence) > 10 and len(first_sentence) <= 100:
                return first_sentence
            elif len(script) <= 100:
                return script.strip()
            else:
                return script[:97] + "..."
        
        # Fallback to operation-based title
        operation_titles = {
            "footage_to_video": "AI Generated Video",
            "aiimage_to_video": "Script-Based Video", 
            "scenes_to_video": "Scene-Based Video",
            "short_video_creation": "Short Form Video",
            "image_to_video": "Image to Video"
        }
        
        base_title = operation_titles.get(operation.lower(), "Generated Video")
        timestamp = self._utcnow().strftime("%Y-%m-%d %H:%M")
        return f"{base_title} - {timestamp}"
    
    def _generate_description(self, result: Dict[str, Any], params: Dict[str, Any]) -> Optional[str]:
        """Generate a description for the video."""
        description_parts = []
        
        # Add topic or theme if available
        if params.get('topic'):
            description_parts.append(f"Topic: {params['topic']}")
        
        # Add duration if available
        if result.get('video_duration'):
            duration = result['video_duration']
            description_parts.append(f"Duration: {duration:.1f}s")
        
        # Add voice info if available
        if params.get('voice_provider') and params.get('voice_name'):
            description_parts.append(f"Voice: {params['voice_provider']} - {params['voice_name']}")
        
        # Add segments info if available
        if result.get('segments_count'):
            description_parts.append(f"Segments: {result['segments_count']}")
        
        return " | ".join(description_parts) if description_parts else None
    
    async def get_video(self, video_id: str) -> Optional[VideoRecord]:
        """Get a video record by ID."""
        async for session in database_service.get_session():
            result = await session.execute(
                select(VideoRecord).where(
                    and_(VideoRecord.id == video_id, VideoRecord.is_deleted == False)
                )
            )
            return result.scalar_one_or_none()
    
    async def get_all_videos(self,
                           limit: int = 50,
                           offset: int = 0,
                           video_type: Optional[VideoType] = None,
                           search_query: Optional[str] = None) -> List[VideoRecord]:
        """Get all videos with optional filtering."""
        async for session in database_service.get_session():
            query = select(VideoRecord).where(VideoRecord.is_deleted == False)
            
            # Filter by video type
            if video_type:
                query = query.where(VideoRecord.video_type == video_type)
            
            # Search functionality
            if search_query:
                search_pattern = f"%{search_query}%"
                query = query.where(
                    or_(
                        VideoRecord.title.ilike(search_pattern),
                        VideoRecord.description.ilike(search_pattern),
                        VideoRecord.script_text.ilike(search_pattern)
                    )
                )
            
            query = query.order_by(VideoRecord.created_at.desc()).limit(limit).offset(offset)
            
            result = await session.execute(query)
            return list(result.scalars().all())
        
        # Fallback return if no session is available
        return []
    
    async def get_videos_by_type(self, video_type: VideoType) -> List[VideoRecord]:
        """Get all videos of a specific type."""
        return await self.get_all_videos(video_type=video_type)
    
    async def update_video_access(self, video_id: str) -> bool:
        """Update last accessed time and increment download count."""
        async for session in database_service.get_session():
            result = await session.execute(
                update(VideoRecord)
                .where(VideoRecord.id == video_id)
                .values(
                    last_accessed=self._utcnow(),
                    download_count=VideoRecord.download_count + 1
                )
            )
            await session.commit()
            return result.rowcount > 0
        
        # Fallback return if no session is available
        return False
    
    async def soft_delete_video(self, video_id: str) -> bool:
        """Soft delete a video (mark as deleted)."""
        async for session in database_service.get_session():
            result = await session.execute(
                update(VideoRecord)
                .where(VideoRecord.id == video_id)
                .values(is_deleted=True, updated_at=self._utcnow())
            )
            await session.commit()
            return result.rowcount > 0
        
        # Fallback return if no session is available
        return False
    
    async def update_video(self, video_id: str, updates: Dict[str, Any]) -> bool:
        """Update video metadata."""
        if not updates:
            return False
        
        # Add updated timestamp
        updates['updated_at'] = self._utcnow()
        
        async for session in database_service.get_session():
            result = await session.execute(
                update(VideoRecord)
                .where(and_(VideoRecord.id == video_id, VideoRecord.is_deleted == False))
                .values(**updates)
            )
            await session.commit()
            return result.rowcount > 0
        
        # Fallback return if no session is available
        return False
    
    async def get_video_stats(self) -> Dict[str, Any]:
        """Get video statistics for dashboard."""
        async for session in database_service.get_session():
            # Total videos
            total_result = await session.execute(
                select(func.count(VideoRecord.id)).where(VideoRecord.is_deleted == False)
            )
            total_videos = total_result.scalar() or 0
            
            # Videos by type
            type_result = await session.execute(
                select(VideoRecord.video_type, func.count(VideoRecord.id))
                .where(VideoRecord.is_deleted == False)
                .group_by(VideoRecord.video_type)
            )
            videos_by_type = {str(video_type): count for video_type, count in type_result}
            
            # Recent videos (last 7 days)
            week_ago = self._utcnow() - timedelta(days=7)
            recent_result = await session.execute(
                select(func.count(VideoRecord.id))
                .where(and_(
                    VideoRecord.is_deleted == False,
                    VideoRecord.created_at >= week_ago
                ))
            )
            recent_videos = recent_result.scalar() or 0
            
            # Total duration
            duration_result = await session.execute(
                select(func.sum(VideoRecord.duration_seconds))
                .where(VideoRecord.is_deleted == False)
            )
            total_duration = duration_result.scalar() or 0
            
            return {
                "total_videos": total_videos,
                "videos_by_type": videos_by_type,
                "recent_videos": recent_videos,
                "total_duration_hours": round(total_duration / 3600, 2) if total_duration else 0,
                "avg_duration_seconds": round(total_duration / total_videos, 1) if total_videos > 0 else 0
            }
        
        # Fallback return if no session is available
        return {
            "total_videos": 0,
            "videos_by_type": {},
            "recent_videos": 0,
            "total_duration_hours": 0,
            "avg_duration_seconds": 0
        }
    
    async def cleanup_old_videos(self, days_old: int = 90) -> int:
        """Clean up very old deleted videos."""
        cutoff_date = self._utcnow() - timedelta(days=days_old)
        
        async for session in database_service.get_session():
            result = await session.execute(
                delete(VideoRecord).where(
                    and_(
                        VideoRecord.is_deleted == True,
                        VideoRecord.updated_at < cutoff_date
                    )
                )
            )
            await session.commit()
            
            deleted_count = result.rowcount
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old deleted videos")
            return deleted_count
        
        # Fallback return if no session is available
        return 0

# Global video service instance
video_service = VideoService()