"""
Service for extracting frames from videos.
"""
import asyncio
import logging
import os
import tempfile
from typing import Dict, Any, List, Optional
import uuid
from pydantic import AnyUrl
import math

from app.utils.media import download_media_file, get_media_info, media_utils
from app.services.s3.s3 import s3_service
from app.services.job_queue import job_queue
from app.models import JobStatus
from app.models import VideoFramesResult

logger = logging.getLogger(__name__)


class VideoFramesService:
    """Service for extracting frames from videos."""
    
    async def process_frames_job(self, job_id: str, params: Dict[str, Any]) -> dict[str, Any]:
        """
        Process a video frames extraction job.
        
        Args:
            job_id: The job identifier
            params: Job parameters containing video_url, interval, format, quality, max_frames
        """
        try:
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=0)
            
            video_url = params["video_url"]
            interval = params["interval"]
            format_type = params["format"]
            quality = params.get("quality", 85)
            max_frames = params.get("max_frames")
            
            # Convert Pydantic URL objects to strings
            video_url = str(video_url)
            
            logger.info(f"Starting frame extraction for job {job_id}")
            
            # Download the video file
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=10)
            video_path, _ = await download_media_file(video_url, job_id)
            
            try:
                # Get video metadata
                await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=20)
                video_info = await get_media_info(video_path)
                video_duration = video_info.get("duration", 0)
                
                # Calculate number of frames to extract
                if video_duration <= 0:
                    raise ValueError("Unable to determine video duration")
                
                # Calculate total frames based on interval
                total_possible_frames = math.floor(video_duration / interval) + 1
                
                # Apply max_frames limit if specified
                if max_frames and total_possible_frames > max_frames:
                    # Adjust interval to fit within max_frames
                    adjusted_interval = video_duration / (max_frames - 1) if max_frames > 1 else video_duration
                    total_frames = max_frames
                else:
                    adjusted_interval = interval
                    total_frames = total_possible_frames
                
                logger.info(f"Extracting {total_frames} frames at {adjusted_interval:.2f}s intervals")
                
                # Extract frames
                await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=30)
                frame_urls = await self._extract_frames(
                    video_path, adjusted_interval, total_frames, format_type, quality, job_id, video_duration
                )
                
                await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=90)
                
                # Create result (convert string URLs to AnyUrl)
                frame_anyurls = [AnyUrl(url) for url in frame_urls]
                result = VideoFramesResult(
                    frame_urls=frame_anyurls,
                    total_frames=len(frame_urls),
                    interval_used=adjusted_interval,
                    video_duration=video_duration
                )
                
                await job_queue.update_job_status(
                    job_id, 
                    JobStatus.COMPLETED, 
                    result=result.model_dump(),
                    progress=100
                )
                
                logger.info(f"Successfully extracted {len(frame_urls)} frames for job {job_id}")
                
                return result.model_dump()
                
            finally:
                # Clean up video file
                if os.path.exists(video_path):
                    os.unlink(video_path)
                    
        except Exception as e:
            logger.error(f"Error processing frames job {job_id}: {str(e)}")
            await job_queue.update_job_status(
                job_id, 
                JobStatus.FAILED, 
                error=str(e)
            )
            raise e
    
    async def _extract_frames(
        self, 
        video_path: str, 
        interval: float,
        total_frames: int,
        format_type: str,
        quality: int,
        job_id: str,
        video_duration: float
    ) -> List[str]:
        """
        Extract frames from video at specified interval.
        
        Args:
            video_path: Path to the video file
            interval: Time interval between frames
            total_frames: Total number of frames to extract
            format_type: Image format (jpg, png, webp)
            quality: Image quality for JPG
            job_id: Job identifier for unique naming
            video_duration: Total video duration
            
        Returns:
            List of S3 URLs for the extracted frames
        """
        frame_urls = []
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Method 1: Extract all frames at once using FFmpeg filter
            if total_frames <= 100:  # For smaller frame counts, extract individually for better control
                frame_urls = await self._extract_frames_individually(
                    video_path, interval, total_frames, format_type, quality, job_id, temp_dir, video_duration
                )
            else:
                # For larger frame counts, use batch extraction
                frame_urls = await self._extract_frames_batch(
                    video_path, interval, total_frames, format_type, quality, job_id, temp_dir
                )
            
            return frame_urls
            
        finally:
            # Clean up temp directory
            try:
                # Remove any remaining files in temp directory
                for file in os.listdir(temp_dir):
                    try:
                        os.unlink(os.path.join(temp_dir, file))
                    except:
                        pass
                os.rmdir(temp_dir)
            except OSError:
                pass  # Directory not empty or other error
    
    async def _extract_frames_individually(
        self,
        video_path: str,
        interval: float,
        total_frames: int,
        format_type: str,
        quality: int,
        job_id: str,
        temp_dir: str,
        video_duration: float
    ) -> List[str]:
        """Extract frames one by one for better control."""
        frame_urls = []
        
        for i in range(total_frames):
            timestamp = min(i * interval, video_duration - 0.1)  # Ensure we don't exceed video duration
            
            # Generate unique filename
            filename = f"frame_{job_id}_{i:06d}.{format_type}"
            temp_frame_path = os.path.join(temp_dir, filename)
            
            try:
                # Extract frame at timestamp using MediaUtils
                success = await media_utils.extract_frame(
                    video_path=video_path,
                    output_path=temp_frame_path,
                    time_seconds=timestamp
                )
                
                # Upload to S3 if frame was generated successfully
                if success and os.path.exists(temp_frame_path) and os.path.getsize(temp_frame_path) > 0:
                    s3_key = f"video_frames/{job_id}/{filename}"
                    s3_url = await s3_service.upload_file(temp_frame_path, s3_key)
                    frame_urls.append(s3_url)
                    
                    logger.debug(f"Extracted frame {i+1}/{total_frames} at {timestamp:.2f}s")
                else:
                    logger.warning(f"Failed to extract frame at timestamp {timestamp}")
                    
            except Exception as e:
                logger.error(f"Error extracting frame at timestamp {timestamp}: {str(e)}")
                continue
            finally:
                # Clean up temp frame file
                if os.path.exists(temp_frame_path):
                    os.unlink(temp_frame_path)
            
            # Update progress
            progress = 30 + int((i + 1) / total_frames * 60)
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=progress)
        
        return frame_urls
    
    async def _extract_frames_batch(
        self,
        video_path: str,
        interval: float,
        total_frames: int,
        format_type: str,
        quality: int,
        job_id: str,
        temp_dir: str
    ) -> List[str]:
        """Extract frames in batch using MediaUtils."""
        frame_urls = []
        
        try:
            # Generate pattern for output files compatible with MediaUtils
            pattern = os.path.join(temp_dir, f"frame_{job_id}_%03d.{format_type}")
            
            # Use MediaUtils.extract_frames for batch extraction
            success = await media_utils.extract_frames(
                video_path=video_path,
                output_template=pattern,
                amount=total_frames
            )
            
            if not success:
                logger.error("MediaUtils.extract_frames failed")
                return frame_urls
            
            # Upload generated frames to S3
            frame_files = sorted([
                f for f in os.listdir(temp_dir) 
                if f.startswith(f"frame_{job_id}_") and f.endswith(f".{format_type}")
            ])
            
            # Limit to requested number of frames
            frame_files = frame_files[:total_frames]
            
            for i, filename in enumerate(frame_files):
                temp_frame_path = os.path.join(temp_dir, filename)
                
                try:
                    if os.path.exists(temp_frame_path) and os.path.getsize(temp_frame_path) > 0:
                        s3_key = f"video_frames/{job_id}/{filename}"
                        s3_url = await s3_service.upload_file(temp_frame_path, s3_key)
                        frame_urls.append(s3_url)
                        
                        logger.debug(f"Uploaded frame {i+1}/{len(frame_files)}")
                        
                except Exception as e:
                    logger.error(f"Error uploading frame {filename}: {str(e)}")
                    continue
                
                # Update progress
                progress = 30 + int((i + 1) / len(frame_files) * 60)
                await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=progress)
            
            return frame_urls
            
        except Exception as e:
            logger.error(f"Error in batch frame extraction: {str(e)}")
            return frame_urls


# Global service instance
video_frames_service = VideoFramesService()