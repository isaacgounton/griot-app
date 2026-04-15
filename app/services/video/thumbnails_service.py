"""
Service for generating video thumbnails.
"""
import asyncio
import logging
import os
import tempfile
from typing import Dict, Any, List, Optional
import uuid
from pydantic import AnyUrl

from app.utils.media import download_media_file, get_media_info, media_utils
from app.services.s3.s3 import s3_service
from app.services.job_queue import job_queue
from app.models import JobStatus
from app.models import VideoThumbnailsResult

logger = logging.getLogger(__name__)


class VideoThumbnailsService:
    """Service for generating thumbnails from videos."""
    
    async def process_thumbnails_job(self, job_id: str, params: Dict[str, Any]) -> dict[str, Any]:
        """
        Process a video thumbnails generation job.
        
        Args:
            job_id: The job identifier
            params: Job parameters containing video_url, timestamps, count, format, quality
        """
        try:
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=0)
            
            video_url = params["video_url"]
            timestamps = params.get("timestamps")
            count = params["count"]
            format_type = params["format"]
            quality = params.get("quality", 85)
            
            # Convert Pydantic URL objects to strings
            video_url = str(video_url)
            
            logger.info(f"Starting thumbnail generation for job {job_id}")
            
            # Download the video file
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=10)
            video_path, _ = await download_media_file(video_url, job_id)
            
            try:
                # Get video metadata to determine duration and optimal timestamps
                await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=20)
                video_info = await get_media_info(video_path)
                video_duration = video_info.get("duration", 0)
                
                # Determine timestamps for thumbnails
                if not timestamps:
                    timestamps = self._generate_optimal_timestamps(video_duration, count)
                else:
                    # Validate provided timestamps against video duration
                    timestamps = [min(ts, video_duration) for ts in timestamps if ts >= 0]
                
                if not timestamps:
                    raise ValueError("No valid timestamps available for thumbnail generation")
                
                # Generate thumbnails
                await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=30)
                thumbnail_urls = await self._generate_thumbnails(
                    video_path, timestamps, format_type, quality, job_id
                )
                
                await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=90)
                
                # Create result (convert string URLs to AnyUrl)
                thumbnail_anyurls = [AnyUrl(url) for url in thumbnail_urls]
                result = VideoThumbnailsResult(
                    thumbnail_urls=thumbnail_anyurls,
                    timestamps_used=timestamps,
                    count=len(thumbnail_urls)
                )
                
                await job_queue.update_job_status(
                    job_id, 
                    JobStatus.COMPLETED, 
                    result=result.model_dump(),
                    progress=100
                )
                
                logger.info(f"Successfully generated {len(thumbnail_urls)} thumbnails for job {job_id}")
                
                return result.model_dump()
                
            finally:
                # Clean up video file
                if os.path.exists(video_path):
                    os.unlink(video_path)
                    
        except Exception as e:
            logger.error(f"Error processing thumbnails job {job_id}: {str(e)}")
            await job_queue.update_job_status(
                job_id, 
                JobStatus.FAILED, 
                error=str(e)
            )
            raise e
    
    def _generate_optimal_timestamps(self, duration: float, count: int) -> List[float]:
        """
        Generate optimal timestamps for thumbnail extraction.
        
        Args:
            duration: Video duration in seconds
            count: Number of thumbnails to generate
            
        Returns:
            List of timestamp values in seconds
        """
        if duration <= 0 or count <= 0:
            return []
        
        if count == 1:
            # Single thumbnail at middle of video
            return [duration / 2]
        
        # Generate evenly spaced timestamps, avoiding very beginning and end
        start_offset = max(1.0, duration * 0.05)  # Skip first 5% or 1 second
        end_offset = max(1.0, duration * 0.05)    # Skip last 5% or 1 second
        
        available_duration = duration - start_offset - end_offset
        
        if available_duration <= 0:
            # Very short video, just use the middle
            return [duration / 2]
        
        # Calculate interval between thumbnails
        if count > 1:
            interval = available_duration / (count - 1)
            timestamps = [start_offset + (i * interval) for i in range(count)]
        else:
            timestamps = [start_offset + available_duration / 2]
        
        return timestamps
    
    async def _generate_thumbnails(
        self, 
        video_path: str, 
        timestamps: List[float], 
        format_type: str,
        quality: int,
        job_id: str
    ) -> List[str]:
        """
        Generate thumbnail images at specified timestamps.
        
        Args:
            video_path: Path to the video file
            timestamps: List of timestamps to extract
            format_type: Image format (jpg, png, webp)
            quality: Image quality for JPG
            job_id: Job identifier for unique naming
            
        Returns:
            List of S3 URLs for the generated thumbnails
        """
        thumbnail_urls = []
        temp_dir = tempfile.mkdtemp()
        
        try:
            for i, timestamp in enumerate(timestamps):
                # Generate unique filename
                filename = f"thumbnail_{job_id}_{i:03d}.{format_type}"
                temp_thumbnail_path = os.path.join(temp_dir, filename)
                
                try:
                    # Extract frame at timestamp using MediaUtils
                    success = await media_utils.extract_frame(
                        video_path=video_path,
                        output_path=temp_thumbnail_path,
                        time_seconds=timestamp
                    )
                    
                    # Upload to S3
                    if success and os.path.exists(temp_thumbnail_path) and os.path.getsize(temp_thumbnail_path) > 0:
                        s3_key = f"video_thumbnails/{job_id}/{filename}"
                        s3_url = await s3_service.upload_file(temp_thumbnail_path, s3_key)
                        thumbnail_urls.append(s3_url)
                        logger.debug(f"Generated thumbnail {i+1}/{len(timestamps)} at {timestamp}s")
                    else:
                        logger.warning(f"Failed to generate thumbnail at timestamp {timestamp}")
                        
                except Exception as e:
                    logger.error(f"Error generating thumbnail at timestamp {timestamp}: {str(e)}")
                    continue
                finally:
                    # Clean up temp thumbnail file
                    if os.path.exists(temp_thumbnail_path):
                        os.unlink(temp_thumbnail_path)
                
                # Update progress
                progress = 30 + int((i + 1) / len(timestamps) * 60)
                await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=progress)
            
            return thumbnail_urls
            
        finally:
            # Clean up temp directory
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass  # Directory not empty or other error


# Global service instance
video_thumbnails_service = VideoThumbnailsService()