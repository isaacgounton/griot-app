"""
Video Builder Service - Create videos from backgrounds, audio, and captions.

Enhanced version using AI agents VideoBuilder for advanced video creation.
"""
import asyncio
import os
import tempfile
import time
import uuid
from typing import Dict, Any, Optional, Tuple, List
from loguru import logger

from app.services.s3.s3 import s3_service
from app.services.job_queue import job_queue
from app.models import JobStatus
from app.utils.media import download_media_file, media_utils
from app.utils.video_builder import VideoBuilder


class VideoBuilderService:
    """
    Service for building videos from backgrounds, audio, and captions.

    Based on the AI agents VideoBuilder but enhanced with:
    - Job queue integration
    - S3 storage
    - Async processing
    - Progress tracking
    - Error handling
    """

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="video_builder_")
        logger.info("VideoBuilderService initialized")

    async def process_job(self, job_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a video building job.

        Args:
            job_id: The job ID
            data: Job data containing video building parameters

        Returns:
            VideoBuilderResult dictionary
        """
        try:
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=0)

            # Extract parameters
            dimensions = data.get("dimensions", (1920, 1080))
            background_config = data.get("background", {})
            audio_url = data.get("audio_url")
            captions_config = data.get("captions", {})
            output_format = data.get("output_format", "mp4")

            logger.info(f"Starting video build job {job_id}")

            # Download required files
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=10)
            downloaded_files = await self._download_files(
                background_config, audio_url, captions_config
            )

            # Build the video
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=30)
            output_path = await self._build_video(
                job_id,
                dimensions,
                background_config,
                downloaded_files,
                captions_config,
                output_format
            )

            # Upload to S3
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=90)
            s3_url = await self._upload_result(output_path, job_id, output_format)

            # Clean up
            await self._cleanup_files(downloaded_files, output_path)

            result = {
                "video_url": s3_url,
                "dimensions": dimensions,
                "duration": self._calculate_duration(downloaded_files.get("audio_path")),
                "format": output_format,
                "background_type": background_config.get("type", "image"),
                "has_audio": bool(audio_url),
                "has_captions": bool(captions_config.get("file")),
            }

            await job_queue.update_job_status(job_id, JobStatus.COMPLETED, progress=100)
            logger.info(f"Video build job {job_id} completed successfully")

            return result

        except Exception as e:
            logger.error(f"Error in video build job {job_id}: {str(e)}")
            await job_queue.update_job_status(job_id, JobStatus.FAILED, error=str(e))
            raise

    async def process_tts_captioned_video_job(self, job_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a TTS-captioned video generation job.

        Args:
            job_id: The job ID
            data: Job data containing TTS-captioned video parameters

        Returns:
            Result dictionary with video URL and metadata
        """
        try:
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=0)

            # Extract parameters
            background_url = data.get("background_url")
            text = data.get("text")
            dimensions = data.get("dimensions", (1080, 1920))
            audio_url = data.get("audio_url")
            tts_provider = data.get("tts_provider", "kokoro")
            voice = data.get("voice", "af_heart")
            speed = data.get("speed", 1.0)
            volume_multiplier = data.get("volume_multiplier", 1.0)
            caption_config = data.get("caption_config", {})
            image_effect = data.get("image_effect", "ken_burns")

            # Convert Pydantic URL objects to strings
            background_url = str(background_url) if background_url else None
            audio_url = str(audio_url) if audio_url else None

            logger.info(f"Starting TTS-captioned video job {job_id}")

            # Download background image
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=10)
            background_path, _ = await download_media_file(background_url, f"background_{job_id}")

            # Generate TTS audio if text provided
            audio_path = None
            captions_data = None
            audio_duration = None
            audio_s3_url = None  # Track S3 URL for TTS audio
            if text and not audio_url:
                await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=20)
                from app.services.audio.tts_service import tts_service

                # Generate TTS audio
                audio_data, provider = await tts_service.generate_speech(
                    text=text,
                    voice=voice,
                    provider=tts_provider,
                    response_format="wav",
                    speed=speed,
                    volume_multiplier=volume_multiplier
                )

                # Upload TTS audio to S3 immediately for reliable storage
                logger.info(f"Uploading TTS audio to S3 for job {job_id}")
                
                # Save binary data to temporary file (following app's standard pattern)
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                    temp_file.write(audio_data)
                    temp_audio_path = temp_file.name
                
                # Upload to S3 with proper content type
                audio_s3_key = f"tts-audio/{job_id}.wav"
                audio_s3_url = await s3_service.upload_file(
                    file_path=temp_audio_path,
                    object_name=audio_s3_key,
                    content_type="audio/wav"
                )
                logger.info(f"TTS audio uploaded to S3: {audio_s3_url}")
                
                # Clean up temporary upload file
                try:
                    os.unlink(temp_audio_path)
                except OSError:
                    pass
                
                # Download from S3 to ensure we have the exact file
                audio_filename = f"tts_audio_{job_id}.wav"
                audio_path = os.path.join(self.temp_dir, audio_filename)
                await s3_service.download_file(
                    object_name=audio_s3_key,
                    download_path=audio_path
                )
                logger.info(f"TTS audio downloaded from S3 to: {audio_path}")
                
                # Verify file after S3 round-trip
                file_size = os.path.getsize(audio_path)
                logger.info(f"TTS audio file size after S3 round-trip: {file_size} bytes")
                
                # Immediately check duration after S3 download
                import subprocess
                import json
                try:
                    probe_cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", audio_path]
                    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
                    if probe_result.returncode == 0:
                        probe_info = json.loads(probe_result.stdout)
                        immediate_duration = float(probe_info.get("format", {}).get("duration", 0))
                        logger.info(f"Duration check after S3 round-trip: {immediate_duration}s (S3: {audio_s3_url})")
                    else:
                        logger.warning(f"Could not probe audio after S3 download: {probe_result.stderr}")
                except Exception as probe_error:
                    logger.error(f"Error probing audio after S3 download: {probe_error}")

                # Generate captions from text using audio duration
                await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=30)
                from app.utils.media import get_media_info
                from app.services.video.caption_service import AdvancedCaptionService

                # Get audio duration
                audio_info = await get_media_info(audio_path)
                original_duration = audio_info.get("duration", 30.0)
                
                logger.info(f"TTS audio duration from get_media_info: {original_duration} seconds for text length: {len(text)} characters, S3 URL: {audio_s3_url}")
                
                # Sanity check: TTS audio should be roughly proportional to text length
                # Typical speech is ~150 words per minute = 2.5 words per second
                # Let's estimate max expected duration
                word_count = len(text.split())
                estimated_duration = word_count / 2.5  # Assuming normal speech rate
                max_reasonable_duration = estimated_duration * 3  # Allow 3x slower than normal
                
                if original_duration > max_reasonable_duration:
                    logger.error(
                        f"ANOMALY DETECTED: Audio duration {original_duration}s is unreasonably long "
                        f"for {word_count} words (estimated: {estimated_duration}s, max reasonable: {max_reasonable_duration}s). "
                        f"TTS parameters: provider={tts_provider}, voice={voice}, speed={speed}. "
                        f"S3 URL: {audio_s3_url}"
                    )
                    # Force a reasonable duration
                    original_duration = min(original_duration, 60.0)
                    logger.warning(f"Forcing audio duration to {original_duration} seconds to prevent timeout")
                
                # Cap audio duration to prevent extremely long videos
                if original_duration > 60.0:
                    logger.warning(f"Audio duration {original_duration} seconds is too long, capping to 60 seconds")
                    audio_duration = 60.0
                    # Trim the audio file to the capped duration
                    trimmed_audio_path = await self._trim_audio_to_duration(audio_path, audio_duration, job_id)
                    if trimmed_audio_path:
                        # Replace the original audio path with the trimmed version
                        if os.path.exists(audio_path):
                            os.remove(audio_path)
                        audio_path = trimmed_audio_path
                else:
                    audio_duration = original_duration

                # Transcribe the TTS audio with Whisper to get actual word timestamps,
                # then align the original script text to those timestamps.
                # This ensures captions follow the real speech timing instead of
                # distributing words uniformly (which drifts out of sync).
                caption_service = AdvancedCaptionService()
                try:
                    audio_transcription = await caption_service._generate_transcription(audio_path, 'auto')
                    captions_data = caption_service._align_text_with_transcription(text, audio_transcription)
                    logger.info(f"Caption sync: Whisper transcription + text alignment succeeded for {len(text.split())} words")
                except Exception as whisper_err:
                    logger.warning(f"Whisper transcription failed, falling back to uniform distribution: {whisper_err}")
                    captions_data = await caption_service._generate_transcription_from_text(text, audio_path)

            elif audio_url:
                # Use provided audio
                audio_path, _ = await download_media_file(audio_url, f"audio_{job_id}")

            # Build the video
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=50)
            output_path = await self._build_tts_captioned_video(
                job_id,
                background_path,
                audio_path,
                captions_data,
                dimensions,
                caption_config,
                image_effect,
                audio_duration
            )

            # Upload to S3
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=90)
            s3_url = await self._upload_result(output_path, job_id, "mp4")

            # Clean up
            cleanup_files = {}
            if background_path:
                cleanup_files["background_path"] = background_path
            if audio_path:
                cleanup_files["audio_path"] = audio_path
            await self._cleanup_files(cleanup_files, output_path)

            result = {
                "video_url": s3_url,
                "dimensions": dimensions,
                "has_audio": bool(audio_path),
                "has_captions": bool(captions_data),
                "background_effect": image_effect,
            }
            
            # Add audio S3 URL if TTS was generated
            if audio_s3_url:
                result["audio_url"] = audio_s3_url
                logger.info(f"TTS audio stored at: {audio_s3_url}")

            await job_queue.update_job_status(job_id, JobStatus.COMPLETED, progress=100)
            logger.info(f"TTS-captioned video job {job_id} completed successfully")

            return result

        except Exception as e:
            logger.error(f"Error in TTS-captioned video job {job_id}: {str(e)}")
            await job_queue.update_job_status(job_id, JobStatus.FAILED, error=str(e))
            raise

    async def _build_tts_captioned_video(
        self,
        job_id: str,
        background_path: str,
        audio_path: Optional[str],
        captions_data: Optional[List[Dict[str, Any]]],
        dimensions: Tuple[int, int],
        caption_config: Dict[str, Any],
        image_effect: str,
        audio_duration: Optional[float] = None
    ) -> str:
        """
        Build a TTS-captioned video using the video builder service.

        Args:
            job_id: Job ID for temporary files
            background_path: Path to background image
            audio_path: Path to audio file (optional)
            captions_data: Caption timestamps data
            dimensions: Video dimensions (width, height)
            caption_config: Caption styling configuration
            image_effect: Background effect type

        Returns:
            Path to the generated video file
        """
        output_path = os.path.join(self.temp_dir, f"tts_video_{job_id}.mp4")

        # Generate ASS subtitle file if captions provided
        captions_path = None
        if captions_data:
            # Generate ASS content
            from app.services.video.caption_service import AdvancedCaptionService
            caption_service = AdvancedCaptionService()
            
            # Create style options from caption_config
            style_options = {
                "font_size": caption_config.get("font_size", 120),
                "font_color": caption_config.get("font_color", "#ffffff"),
                "shadow_color": caption_config.get("shadow_color", "#000000"),
                "stroke_color": caption_config.get("stroke_color", "#000000"),
                "position": caption_config.get("position", "bottom"),
                "style": "classic"  # Use classic style for TTS captions
            }
            
            # Generate ASS content
            ass_content = caption_service._process_subtitle_events(
                transcription=captions_data,
                style_type="classic",
                style_options=style_options,
                replace_dict={},  # No text replacements for TTS
                video_resolution=dimensions
            )
            
            # Save ASS file
            captions_filename = f"captions_{job_id}.ass"
            captions_path = os.path.join(self.temp_dir, captions_filename)
            with open(captions_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)

        # Prepare parameters for build_command
        background_config = {
            "type": "image",
            "effect_config": {"effect": image_effect}
        }
        
        downloaded_files = {
            "background_path": background_path,
            "audio_path": audio_path,
            "captions_path": captions_path
        }

        # Build FFmpeg command
        cmd = await self._build_ffmpeg_command(
            dimensions=dimensions,
            background_config=background_config,
            downloaded_files=downloaded_files,
            captions_config=caption_config,
            output_path=output_path,
            audio_duration=audio_duration
        )

        # Execute command
        success = await self._execute_ffmpeg_command(cmd, job_id)
        
        if not success:
            raise ValueError("Failed to build TTS-captioned video")

        return output_path

    async def _download_files(
        self,
        background_config: Dict[str, Any],
        audio_url: Optional[str],
        captions_config: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Download all required files for video building.

        Returns:
            Dict with paths to downloaded files
        """
        downloaded = {}

        # Download background file
        if background_config.get("type") == "image" and background_config.get("file"):
            background_file = str(background_config["file"])
            background_path, _ = await download_media_file(
                background_file, f"background_{uuid.uuid4().hex}"
            )
            downloaded["background_path"] = background_path
        elif background_config.get("type") == "video" and background_config.get("file"):
            background_file = str(background_config["file"])
            background_path, _ = await download_media_file(
                background_file, f"background_{uuid.uuid4().hex}"
            )
            downloaded["background_path"] = background_path

        # Download audio file
        if audio_url:
            audio_url_str = str(audio_url)
            audio_path, _ = await download_media_file(
                audio_url_str, f"audio_{uuid.uuid4().hex}"
            )
            downloaded["audio_path"] = audio_path

        # Download captions file
        if captions_config.get("file"):
            captions_file = str(captions_config["file"])
            captions_path, _ = await download_media_file(
                captions_file, f"captions_{uuid.uuid4().hex}"
            )
            downloaded["captions_path"] = captions_path

        return downloaded

    async def _build_video(
        self,
        job_id: str,
        dimensions: Tuple[int, int],
        background_config: Dict[str, Any],
        downloaded_files: Dict[str, str],
        captions_config: Dict[str, Any],
        output_format: str
    ) -> str:
        """
        Build the video using VideoBuilder.

        Returns:
            Path to the output video file
        """
        width, height = dimensions
        output_path = os.path.join(self.temp_dir, f"{job_id}.{output_format}")

        # Create VideoBuilder instance
        builder = VideoBuilder(dimensions)

        # Set background
        background_path = downloaded_files.get("background_path")
        if background_config.get("type") == "image" and background_path:
            builder.set_background_image(
                background_path,
                background_config.get("effect_config")
            )
        elif background_config.get("type") == "video" and background_path:
            builder.set_background_video(background_path)

        # Set audio
        audio_path = downloaded_files.get("audio_path")
        if audio_path:
            builder.set_audio(audio_path)

        # Set captions
        captions_path = downloaded_files.get("captions_path")
        if captions_path:
            builder.set_captions(captions_path, captions_config)

        # Set output path
        builder.set_output_path(output_path)

        # Execute the build
        success = await builder.execute()

        if not success:
            raise Exception("VideoBuilder execution failed")

        return output_path

    async def _build_ffmpeg_command(
        self,
        dimensions: Tuple[int, int],
        background_config: Dict[str, Any],
        downloaded_files: Dict[str, str],
        captions_config: Dict[str, Any],
        output_path: str,
        audio_duration: Optional[float] = None
    ) -> list:
        """
        Build the FFmpeg command for video creation.
        """
        width, height = dimensions
        cmd = ["ffmpeg", "-y"]

        filter_parts = []
        input_index = 0

        # Add background input
        background_path = downloaded_files.get("background_path")
        if background_config.get("type") == "image" and background_path:
            # Use provided audio duration for image background
            audio_path = downloaded_files.get("audio_path")
            if audio_path and audio_duration is None:
                audio_duration = await self._get_audio_duration(audio_path)

            if audio_duration:
                cmd.extend(["-loop", "1", "-t", str(audio_duration), "-i", background_path])

                # Apply Ken Burns effect if configured
                effect_config = background_config.get("effect_config", {"effect": "ken_burns"})
                effect_type = effect_config.get("effect", "ken_burns")

                if effect_type == "ken_burns":
                    zoom_factor = effect_config.get("zoom_factor", 0.001)
                    direction = effect_config.get("direction", "zoom-to-top-left")

                    zoom_expressions = {
                        "zoom-to-top": f"z='zoom+{zoom_factor}':x=iw/2-(iw/zoom/2):y=0",
                        "zoom-to-center": f"z='zoom+{zoom_factor}':x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2)",
                        "zoom-to-top-left": f"z='zoom+{zoom_factor}':x=0:y=0",
                    }
                    zoom_expr = zoom_expressions.get(direction, zoom_expressions["zoom-to-top-left"])

                    fps = 25
                    duration_frames = int(audio_duration * fps)
                    zoompan_d = duration_frames + 1

                    filter_parts.append(
                        f"[{input_index}]scale={width}:-2,setsar=1:1,"
                        f"crop={width}:{height},"
                        f"zoompan={zoom_expr}:d={zoompan_d}:s={width}x{height}:fps={fps}[bg]"
                    )
                else:
                    filter_parts.append(f"[{input_index}]scale={width}:{height},setsar=1:1[bg]")

            else:
                cmd.extend(["-i", background_path])
                filter_parts.append(f"[{input_index}]scale={width}:{height},setsar=1:1[bg]")

        elif background_config.get("type") == "video" and background_path:
            cmd.extend(["-i", background_path])
            filter_parts.append(f"[{input_index}]scale={width}:{height}[bg]")

        input_index += 1
        current_video = "[bg]"

        # Add audio input
        audio_input_index = None
        audio_path = downloaded_files.get("audio_path")
        if audio_path:
            cmd.extend(["-i", audio_path])
            audio_input_index = input_index
            input_index += 1

        # Add captions/subtitles
        captions_path = downloaded_files.get("captions_path")
        if captions_path:
            # Properly escape the path for FFmpeg filter complex
            # FFmpeg expects: backslashes as \\ and colons as \:
            escaped_path = captions_path.replace('\\', '\\\\').replace(':', '\\:')
            filter_parts.append(f"{current_video}subtitles={escaped_path}[v]")
            current_video = "[v]"
        else:
            if current_video == "[bg]":
                current_video = "[v]"
                filter_parts.append(f"[bg]copy[v]")

        # Build filter complex
        if filter_parts:
            cmd.extend(["-filter_complex", ";".join(filter_parts)])

        # Map video and audio
        cmd.extend(["-map", current_video])
        if audio_input_index is not None:
            cmd.extend(["-map", f"{audio_input_index}:a"])

        # Video codec settings
        cmd.extend(["-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p"])

        # Audio codec settings
        if audio_path:
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])

        cmd.append(output_path)
        return cmd

    async def _get_audio_duration(self, audio_path: str) -> Optional[float]:
        """Get audio duration using ffprobe."""
        try:
            import subprocess
            import json

            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                audio_path
            ]

            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                probe_data = json.loads(stdout.decode())
                return float(probe_data.get("format", {}).get("duration", 0))
        except Exception as e:
            logger.warning(f"Failed to get audio duration: {e}")

        return None

    async def _execute_ffmpeg_command(self, cmd: list, job_id: str) -> bool:
        """Execute FFmpeg command with progress tracking."""
        try:
            logger.debug(f"Executing FFmpeg command for job {job_id}: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Monitor progress
            while True:
                line = await process.stderr.readline()
                if not line:
                    break

                line_str = line.decode().strip()
                if "time=" in line_str and "speed=" in line_str:
                    # Extract progress information
                    try:
                        time_str = line_str.split("time=")[1].split(" ")[0]
                        h, m, s = time_str.split(":")
                        current_seconds = float(h) * 3600 + float(m) * 60 + float(s)

                        # Update progress (this is approximate since we don't know total duration)
                        progress = min(80, current_seconds * 2)  # Rough estimate
                        await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=int(progress))
                    except:
                        pass

            return_code = await process.wait()
            return return_code == 0

        except Exception as e:
            logger.error(f"FFmpeg execution failed for job {job_id}: {e}")
            return False

    async def _trim_audio_to_duration(self, audio_path: str, duration: float, job_id: str) -> Optional[str]:
        """
        Trim audio file to specified duration.
        
        Args:
            audio_path: Path to the audio file
            duration: Target duration in seconds
            job_id: Job ID for naming
            
        Returns:
            Path to trimmed audio file, or None if trimming failed
        """
        try:
            trimmed_path = os.path.join(self.temp_dir, f"trimmed_audio_{job_id}.wav")
            
            cmd = [
                "ffmpeg", "-y",
                "-i", audio_path,
                "-t", str(duration),
                "-c:a", "copy",
                trimmed_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, _ = await process.communicate()
            
            if process.returncode == 0 and os.path.exists(trimmed_path):
                logger.info(f"Successfully trimmed audio to {duration} seconds: {trimmed_path}")
                return trimmed_path
            else:
                logger.error(f"Failed to trim audio: {stdout.decode() if stdout else 'Unknown error'}")
                return None
                
        except Exception as e:
            logger.error(f"Error trimming audio: {e}")
            return None

    async def _upload_result(self, output_path: str, job_id: str, output_format: str) -> str:
        """Upload the result video to S3."""
        s3_path = f"video-builder-results/{job_id}.{output_format}"
        result_url = await s3_service.upload_file(output_path, s3_path)

        # Remove signature parameters from URL if present
        if '?' in result_url:
            result_url = result_url.split('?')[0]

        return result_url

    async def _cleanup_files(self, downloaded_files: Dict[str, str], output_path: str):
        """Clean up temporary files."""
        try:
            # Clean up downloaded files
            for file_path in downloaded_files.values():
                if os.path.exists(file_path):
                    os.remove(file_path)

            # Clean up output file
            if os.path.exists(output_path):
                os.remove(output_path)

        except Exception as e:
            logger.warning(f"Failed to clean up temporary files: {e}")

    def _calculate_duration(self, audio_path: Optional[str]) -> Optional[float]:
        """Calculate video duration based on audio."""
        if audio_path:
            return asyncio.run(self._get_audio_duration(audio_path))
        return None


# Create service instance
video_builder_service = VideoBuilderService()