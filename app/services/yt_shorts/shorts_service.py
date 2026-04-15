"""
Clean YouTube Shorts generation service.

Simple, reliable implementation using only proven working components:
- FFmpeg for all video processing
- Direct file operations
- Smart segment selection algorithm
- No complex dependencies or fallbacks
"""
import os
import json
import uuid
import logging
import asyncio
import subprocess
import tempfile
from typing import Any

from app.services.s3.s3 import s3_service
from app.services.media.download_service import download_service
from app.services.media.transcription import get_transcription_service

# Configure logging
logger = logging.getLogger(__name__)

class YouTubeShortsService:
    """Simple, reliable YouTube Shorts generation service."""

    async def process_shorts_job(self, job_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Process a YouTube Shorts generation job.

        Args:
            job_id: The ID of the job.
            data: The job data containing video URL and generation settings.

        Returns:
            Dictionary with the result.
        """
        # Use local variables for thread safety (this is a singleton)
        processing_stats: dict[str, Any] = {}

        with tempfile.TemporaryDirectory(prefix=f"yt_shorts_{job_id}_") as temp_dir:
            try:
                # Extract job parameters
                video_url = data.get("video_url")
                if not video_url:
                    raise ValueError("video_url is required")

                # Convert Pydantic URL objects to strings
                video_url = str(video_url)

                max_duration = data.get("max_duration", 60)
                quality = data.get("quality", "high")
                custom_start_time = data.get("custom_start_time")
                custom_end_time = data.get("custom_end_time")

                logger.info(f"Starting YouTube Shorts job {job_id}")

                # Step 1: Download YouTube video
                logger.info(f"Job {job_id}: Downloading YouTube video")
                video_path, video_title = await self._download_video(
                    video_url, data.get("cookies_url"), temp_dir, processing_stats
                )

                # Step 2: Get video information
                video_info = await self._get_video_info(video_path)
                original_duration = video_info.get('duration', 0)

                # Step 3: Extract audio for transcription
                logger.info(f"Job {job_id}: Extracting audio")
                audio_path = await self._extract_audio(video_path, temp_dir)

                # Step 4: Transcribe audio
                logger.info(f"Job {job_id}: Transcribing audio")
                transcriptions = await self._transcribe_audio(audio_path, processing_stats)

                # Step 5: Determine best segment
                start_time, end_time = self._select_best_segment(
                    transcriptions, custom_start_time, custom_end_time,
                    max_duration, original_duration
                )

                # Step 6: Extract video segment
                logger.info(f"Job {job_id}: Extracting segment ({start_time}s - {end_time}s)")
                segment_path = await self._extract_segment(video_path, start_time, end_time, temp_dir)

                # Step 7: Optimize for YouTube Shorts format
                logger.info(f"Job {job_id}: Optimizing for YouTube Shorts")
                final_path = await self._optimize_for_shorts(segment_path, quality, temp_dir)

                # Step 8: Upload to S3
                logger.info(f"Job {job_id}: Uploading to S3")
                video_s3_url = await self._upload_to_s3(final_path, job_id, processing_stats)

                # Step 9: Prepare result
                duration = end_time - start_time
                result = {
                    "url": video_s3_url,
                    "path": f"videos/yt-shorts/shorts_{job_id}_{uuid.uuid4().hex[:8]}.mp4",
                    "duration": duration,
                    "original_title": video_title,
                    "original_duration": original_duration,
                    "highlight_start": start_time,
                    "highlight_end": end_time,
                    "ai_generated": False,  # We use smart algorithm, not AI
                    "is_vertical": True,
                    "quality": quality,
                    "processing_stats": processing_stats,
                    "features_used": {
                        "smart_segment_selection": True,
                        "ffmpeg_processing": True,
                        "vertical_optimization": True,
                        "audio_transcription": len(transcriptions) > 0
                    }
                }

                logger.info(f"Successfully completed YouTube Shorts job {job_id}")
                return result

            except Exception as e:
                logger.error(f"Error in YouTube Shorts job {job_id}: {e}")
                raise

    async def _download_video(self, url: str, cookies_url: str | None,
                              temp_dir: str, processing_stats: dict[str, Any]) -> tuple[str, str]:
        """Download YouTube video."""
        download_job_id = f"temp_download_{uuid.uuid4()}"
        params = {"url": url, "file_name": "video", "cookies_url": cookies_url or ""}
        result = await download_service.process_media_download(download_job_id, params)

        if not result or not result.get("path"):
            raise RuntimeError("Video download failed")

        video_path = result["path"]
        video_title = result.get("title", "YouTube Video")

        # Move to our temp directory
        if not video_path.startswith(temp_dir):
            import shutil
            filename = os.path.basename(video_path)
            new_path = os.path.join(temp_dir, filename)
            shutil.move(video_path, new_path)
            video_path = new_path

        processing_stats["download_size"] = os.path.getsize(video_path)
        return video_path, video_title

    async def _get_video_info(self, video_path: str) -> dict[str, Any]:
        """Get video information using FFprobe."""
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', video_path
        ]

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)

        # Extract basic video info
        video_stream = next((s for s in data.get('streams', []) if s.get('codec_type') == 'video'), None)
        audio_stream = next((s for s in data.get('streams', []) if s.get('codec_type') == 'audio'), None)

        duration = float(data.get('format', {}).get('duration', 0))

        return {
            'duration': duration,
            'width': int(video_stream.get('width', 0)) if video_stream else 0,
            'height': int(video_stream.get('height', 0)) if video_stream else 0,
            'has_audio': audio_stream is not None,
            'file_size': os.path.getsize(video_path)
        }

    async def _extract_audio(self, video_path: str, temp_dir: str) -> str:
        """Extract audio using FFmpeg."""
        audio_path = os.path.join(temp_dir, "audio.wav")

        cmd = [
            'ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le',
            '-ar', '44100', '-ac', '2', '-y', audio_path
        ]

        await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, check=True
        )

        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            raise RuntimeError("Audio extraction failed")

        return audio_path

    async def _transcribe_audio(self, audio_path: str,
                                processing_stats: dict[str, Any]) -> list[tuple[str, float, float]]:
        """Transcribe audio to get text segments."""
        try:
            result = await get_transcription_service().transcribe(
                file_path=audio_path,
                include_text=True,
                include_srt=False,
                word_timestamps=False,
                include_segments=True,
                language="en",
                model_name="small"
            )

            transcriptions: list[tuple[str, float, float]] = []
            if "segments" in result:
                for segment in result["segments"]:
                    text = segment.get("text", "").strip()
                    start = segment.get("start", 0.0)
                    end = segment.get("end", 0.0)
                    if text:
                        transcriptions.append((text, start, end))

            processing_stats["transcription_segments"] = len(transcriptions)
            return transcriptions

        except Exception as e:
            logger.warning(f"Transcription failed: {e}")
            return []

    def _select_best_segment(self, transcriptions: list[tuple[str, float, float]],
                            custom_start: float | None, custom_end: float | None,
                            max_duration: int, original_duration: float) -> tuple[float, float]:
        """Select the best segment for the short."""

        # Use custom times if provided
        if custom_start is not None and custom_end is not None:
            return custom_start, custom_end

        # Use smart selection if we have transcriptions
        if transcriptions:
            return self._smart_segment_selection(transcriptions, max_duration)

        # Fallback: use first segment
        return 0, min(max_duration, original_duration)

    def _smart_segment_selection(self, transcriptions: list[tuple[str, float, float]],
                                max_duration: int) -> tuple[float, float]:
        """Smart algorithm to select the best segment."""
        if not transcriptions:
            return 0, max_duration

        total_duration = transcriptions[-1][2] if transcriptions else max_duration
        best_score = 0
        best_start = 0
        best_end = min(max_duration, total_duration)

        # Test segments every 5 seconds
        for start in range(0, int(total_duration), 5):
            end = min(start + max_duration, total_duration)
            if end - start < 10:  # Skip very short segments
                continue

            # Calculate segment score
            word_count = 0
            for text, t_start, t_end in transcriptions:
                if t_start < end and t_end > start:
                    word_count += len(text.split())

            # Prefer segments with more content and from middle of video
            content_score = word_count / max_duration
            middle_position = total_duration / 2
            position_score = 1 - abs(start + max_duration/2 - middle_position) / (total_duration / 2)

            total_score = content_score * 0.8 + position_score * 0.2

            if total_score > best_score:
                best_score = total_score
                best_start = start
                best_end = end

        logger.info(f"Smart selection: {best_start}s-{best_end}s (score: {best_score:.2f})")
        return best_start, best_end

    async def _extract_segment(self, video_path: str, start_time: float,
                               end_time: float, temp_dir: str) -> str:
        """Extract video segment using FFmpeg."""
        output_path = os.path.join(temp_dir, "segment.mp4")
        duration = end_time - start_time

        cmd = [
            'ffmpeg', '-i', video_path, '-ss', str(start_time),
            '-t', str(duration), '-c:v', 'libx264', '-c:a', 'aac',
            '-y', output_path
        ]

        await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, check=True
        )

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("Video segment extraction failed")

        return output_path

    async def _optimize_for_shorts(self, video_path: str, quality: str, temp_dir: str) -> str:
        """Optimize video for YouTube Shorts format using FFmpeg."""
        output_path = os.path.join(temp_dir, "optimized.mp4")

        # Quality settings
        quality_settings = {
            'low': ['-crf', '28', '-preset', 'fast', '-b:v', '1M'],
            'medium': ['-crf', '23', '-preset', 'medium', '-b:v', '2.5M'],
            'high': ['-crf', '18', '-preset', 'slow', '-b:v', '5M'],
            'ultra': ['-crf', '15', '-preset', 'slower', '-b:v', '8M']
        }

        settings = quality_settings.get(quality, quality_settings['high'])

        cmd = [
            'ffmpeg', '-i', video_path, '-c:v', 'libx264', '-c:a', 'aac',
            '-vf', 'scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280',
            '-r', '30', '-b:a', '128k'
        ] + settings + ['-y', output_path]

        await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, check=True
        )

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("Video optimization failed")

        return output_path

    async def _upload_to_s3(self, file_path: str, job_id: str,
                            processing_stats: dict[str, Any]) -> str:
        """Upload video to S3."""
        unique_suffix = uuid.uuid4().hex[:8]
        s3_object_name = f"videos/yt-shorts/shorts_{job_id}_{unique_suffix}.mp4"
        video_url = await s3_service.upload_file(
            file_path=file_path,
            object_name=s3_object_name
        )

        processing_stats["uploaded_to_s3"] = True
        return video_url

# Create service instance
youtube_shorts_service = YouTubeShortsService()
