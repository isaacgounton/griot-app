"""
Colorkey Overlay Service - Apply green screen effects to videos.
"""
import os
import tempfile
import uuid
from typing import Dict, Any

from loguru import logger

from app.services.s3.s3 import s3_service
from app.services.job_queue import job_queue
from app.models import JobStatus
from app.utils.media import download_media_file, media_utils


class ColorkeyOverlayService:
    """
    Service for applying colorkey (green screen) overlay effects to videos.
    """

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="colorkey_overlay_")
        logger.info("ColorkeyOverlayService initialized")

    async def process_colorkey_overlay_job(self, job_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a colorkey overlay job.

        Args:
            job_id: The job ID
            data: Job data containing overlay parameters

        Returns:
            Result dictionary with output video URL
        """
        try:
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=0)

            # Extract parameters
            video_url = data.get("video_url")
            overlay_video_url = data.get("overlay_video_url")
            color = data.get("color", "green")
            similarity = data.get("similarity", 0.3)
            blend = data.get("blend", 0.1)

            # Convert Pydantic URL objects to strings
            video_url = str(video_url) if video_url else None
            overlay_video_url = str(overlay_video_url) if overlay_video_url else None

            logger.info(f"Starting colorkey overlay job {job_id}")

            # Download input videos
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=10)
            video_path, _ = await download_media_file(video_url, f"base_video_{job_id}")
            overlay_path, _ = await download_media_file(overlay_video_url, f"overlay_video_{job_id}")

            # Apply colorkey overlay
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=30)
            output_path = await self._apply_colorkey_overlay(
                job_id, video_path, overlay_path, color, similarity, blend
            )

            # Upload to S3
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=90)
            s3_url = await self._upload_result(output_path, job_id, "mp4")

            # Clean up
            await self._cleanup_files([video_path, overlay_path, output_path])

            result = {
                "video_url": s3_url,
                "color": color,
                "similarity": similarity,
                "blend": blend,
            }

            await job_queue.update_job_status(job_id, JobStatus.COMPLETED, progress=100)
            logger.info(f"Colorkey overlay job {job_id} completed successfully")

            return result

        except Exception as e:
            logger.error(f"Error in colorkey overlay job {job_id}: {str(e)}")
            await job_queue.update_job_status(job_id, JobStatus.FAILED, error=str(e))
            raise

    async def _apply_colorkey_overlay(
        self,
        job_id: str,
        video_path: str,
        overlay_path: str,
        color: str,
        similarity: float,
        blend: float
    ) -> str:
        """
        Apply colorkey overlay effect using MediaUtils.

        Args:
            job_id: Job ID for temporary files
            video_path: Path to base video
            overlay_path: Path to overlay video
            color: Color to key out
            similarity: Similarity threshold
            blend: Blend amount

        Returns:
            Path to output video
        """
        output_path = os.path.join(self.temp_dir, f"colorkey_overlay_{job_id}.mp4")

        success = media_utils.colorkey_overlay(
            input_video_path=video_path,
            overlay_video_path=overlay_path,
            output_video_path=output_path,
            color=color,
            similarity=similarity,
            blend=blend,
        )

        if not success:
            raise ValueError("Failed to apply colorkey overlay")

        return output_path

    async def _upload_result(self, output_path: str, job_id: str, format_type: str) -> str:
        """Upload result to S3 and return URL."""
        s3_key = f"video-processing/colorkey_overlay_{job_id}.{format_type}"
        s3_url = await s3_service.upload_file(output_path, s3_key)
        return s3_url

    async def _cleanup_files(self, file_paths: list[str]) -> None:
        """Clean up temporary files."""
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.warning(f"Failed to clean up {path}: {e}")


# Create service instance
colorkey_overlay_service = ColorkeyOverlayService()