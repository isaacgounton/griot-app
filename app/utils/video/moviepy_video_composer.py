"""
MoviePy-based video composer for precise timing without pauses.
Based on the original Text-To-Video-AI project approach.
Supports both MoviePy 1.x and 2.x APIs.
"""
import os
import uuid
import tempfile
import logging
import asyncio
import aiohttp
from typing import List, Dict, Optional

# MoviePy imports with compatibility for different versions
_MOVIEPY_V2 = False
try:
    # Try MoviePy 2.x direct imports
    from moviepy import VideoFileClip, CompositeVideoClip
    _MOVIEPY_V2 = True
except ImportError:
    # Fall back to MoviePy 1.x editor imports
    from moviepy.editor import VideoFileClip, CompositeVideoClip

from app.services.s3.s3 import s3_service

logger = logging.getLogger(__name__)
logger.info(f"MoviePy version detected: {'2.x' if _MOVIEPY_V2 else '1.x'}")


# ─── MoviePy version-agnostic helpers ─────────────────────────────────
def _subclip(clip, start, end):
    """clip.subclip(s,e) in v1 → clip.subclipped(s,e) in v2."""
    if hasattr(clip, 'subclipped'):
        return clip.subclipped(start, end)
    return clip.subclip(start, end)


def _set_start(clip, t):
    if hasattr(clip, 'with_start'):
        return clip.with_start(t)
    return clip.set_start(t)


def _set_end(clip, t):
    if hasattr(clip, 'with_end'):
        return clip.with_end(t)
    return clip.set_end(t)


def _set_duration(clip, t):
    if hasattr(clip, 'with_duration'):
        return clip.with_duration(t)
    return clip.set_duration(t)


def _set_position(clip, pos):
    if hasattr(clip, 'with_position'):
        return clip.with_position(pos)
    return clip.set_position(pos)


def _resize(clip, **kwargs):
    if hasattr(clip, 'resized'):
        return clip.resized(**kwargs)
    return clip.resize(**kwargs)


def _crossfadein(clip, duration):
    """Apply crossfade-in: v2 uses effects API, v1 uses method."""
    if _MOVIEPY_V2:
        try:
            from moviepy.video.fx import CrossFadeIn
            return clip.with_effects([CrossFadeIn(duration)])
        except (ImportError, AttributeError):
            pass
    if hasattr(clip, 'crossfadein'):
        return clip.crossfadein(duration)
    return clip


def _crossfadeout(clip, duration):
    """Apply crossfade-out: v2 uses effects API, v1 uses method."""
    if _MOVIEPY_V2:
        try:
            from moviepy.video.fx import CrossFadeOut
            return clip.with_effects([CrossFadeOut(duration)])
        except (ImportError, AttributeError):
            pass
    if hasattr(clip, 'crossfadeout'):
        return clip.crossfadeout(duration)
    return clip


def _fadein(clip, duration):
    if _MOVIEPY_V2:
        try:
            from moviepy.video.fx import FadeIn
            return clip.with_effects([FadeIn(duration)])
        except (ImportError, AttributeError):
            pass
    if hasattr(clip, 'fadein'):
        return clip.fadein(duration)
    return clip


def _fadeout(clip, duration):
    if _MOVIEPY_V2:
        try:
            from moviepy.video.fx import FadeOut
            return clip.with_effects([FadeOut(duration)])
        except (ImportError, AttributeError):
            pass
    if hasattr(clip, 'fadeout'):
        return clip.fadeout(duration)
    return clip
# ──────────────────────────────────────────────────────────────────────


class MoviePyVideoComposer:
    """Video composer using MoviePy for precise timing like the original Text-To-Video-AI project."""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="moviepy_video_")
    
    async def compose_timed_videos(self, video_segments: List[Dict], target_duration: float,
                                 output_width: int = 1920, output_height: int = 1080,
                                 frame_rate: int = 30) -> str:
        """
        Compose background videos with precise timing using MoviePy.
        
        Args:
            video_segments: List of video segment dicts with timing info and URLs
            target_duration: Total duration for the composed video
            output_width: Output video width  
            output_height: Output video height
            frame_rate: Output frame rate
        
        Returns:
            S3 URL of the composed background video
        """
        try:
            # Download all video segments
            downloaded_segments = await self._download_video_segments(video_segments)
            
            # Preprocess videos with FFmpeg for quality (hybrid approach)
            logger.info("Preprocessing videos with FFmpeg for optimal quality...")
            processed_segments = await self._preprocess_videos_with_ffmpeg(downloaded_segments, output_width, output_height)
            
            # Create MoviePy video clips with precise timing from FFmpeg-processed videos
            video_clips = await self._create_video_clips(processed_segments, target_duration, output_width, output_height)
            
            # Compose final video using MoviePy
            output_path = await self._compose_final_video(video_clips, target_duration, output_width, output_height, frame_rate)
            
            # Upload to S3
            s3_url = await self._upload_to_s3(output_path)
            
            # Cleanup temp files
            segment_paths = [seg['local_path'] for seg in downloaded_segments if seg and seg.get('local_path')]
            await self._cleanup_temp_files(segment_paths + [output_path])
            
            return s3_url
            
        except Exception as e:
            logger.error(f"Failed to compose background video using MoviePy: {e}")
            raise ValueError(f"MoviePy video composition failed: {str(e)}")
    
    async def _download_video_segments(self, video_segments: List[Dict]) -> List[Dict]:
        """Download video segments from URLs."""
        downloaded_segments = []
        
        async with aiohttp.ClientSession() as session:
            for i, segment in enumerate(video_segments):
                if segment is None:
                    downloaded_segments.append(None)
                    continue
                
                try:
                    download_url = segment['download_url']
                    local_path = os.path.join(self.temp_dir, f"segment_{i}.mp4")
                    
                    async with session.get(download_url) as response:
                        if response.status == 200:
                            with open(local_path, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    f.write(chunk)
                            
                            segment_copy = segment.copy()
                            segment_copy['local_path'] = local_path
                            downloaded_segments.append(segment_copy)
                            
                        else:
                            logger.warning(f"Failed to download segment {i}: HTTP {response.status}")
                            downloaded_segments.append(None)
                            
                except Exception as e:
                    logger.error(f"Error downloading segment {i}: {e}")
                    downloaded_segments.append(None)
        
        return downloaded_segments
    
    async def _preprocess_videos_with_ffmpeg(self, downloaded_segments: List[Dict], output_width: int, output_height: int) -> List[Dict]:
        """Preprocess videos with FFmpeg for better quality, then return paths for MoviePy timing."""
        processed_segments = []
        
        for i, segment in enumerate(downloaded_segments):
            if segment is None:
                processed_segments.append(None)
                continue
            
            try:
                input_path = segment['local_path']
                output_path = os.path.join(self.temp_dir, f"processed_segment_{i}.mp4")
                
                # Apply viral-shorts-creator orientation method - EXACT copy from edit.js
                # Stage 1: Pre-limit resolution to avoid processing massive files
                base_optimization = "scale='min(1920,iw)':'min(1920,ih)':force_original_aspect_ratio=decrease"
                
                # Stage 2: Format-specific scaling - use INCREASE + CROP for ALL formats like viral-shorts-creator
                format_filter = f"scale={output_width}:{output_height}:force_original_aspect_ratio=increase,crop={output_width}:{output_height}"
                filter_complex = f"{base_optimization},{format_filter}"
                
                cmd = [
                    'ffmpeg', '-y',
                    '-i', input_path,
                    '-vf', filter_complex,
                    '-c:v', 'libx264',
                    '-preset', 'medium',        # Less aggressive preset
                    '-crf', '18',              # Higher quality (lower CRF)
                    '-g', '30',                # Set GOP size to match frame rate
                    '-keyint_min', '30',       # Minimum GOP size
                    '-sc_threshold', '0',      # Disable scene change detection
                    '-pix_fmt', 'yuv420p',     # Ensure compatible pixel format
                    output_path
                ]
                
                # Run FFmpeg preprocessing
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    # Update segment with processed path
                    processed_segment = segment.copy()
                    processed_segment['processed_path'] = output_path
                    processed_segments.append(processed_segment)
                else:
                    logger.error(f"FFmpeg preprocessing failed for segment {i}: {stderr.decode()}")
                    processed_segments.append(None)
                    
            except Exception as e:
                logger.error(f"Error preprocessing segment {i} with FFmpeg: {e}")
                processed_segments.append(None)
        
        return processed_segments

    async def _create_video_clips(self, downloaded_segments: List[Dict], target_duration: float,
                                output_width: int, output_height: int) -> List[VideoFileClip]:
        """Create MoviePy video clips with continuous timing and crossfade transitions."""
        video_clips = []
        valid_segments = [seg for seg in downloaded_segments if seg is not None]

        if not valid_segments:
            raise ValueError("No valid video segments available for composition")

        # Always respect transcription timing for natural speech flow
        crossfade_duration = 0.2  # Reduced crossfade for short segments

        # Check if segments have actual duration information from transcription
        has_actual_durations = all(seg.get('duration') for seg in valid_segments if seg.get('duration', 0) > 0)

        if has_actual_durations:
            logger.info("Using actual segment durations from transcription (preserving natural speech timing)")
            total_segment_duration = sum(seg.get('duration', 3.0) for seg in valid_segments)
            logger.info(f"Total segment duration: {total_segment_duration:.2f}s, target: {target_duration:.2f}s")

            # Adjust crossfade for very short segments to prevent black screens
            min_segment_duration = min(seg.get('duration', 3.0) for seg in valid_segments)
            if min_segment_duration < 1.0:
                crossfade_duration = min(0.1, min_segment_duration / 4)  # Max 25% of shortest segment
                logger.info(f"Reduced crossfade to {crossfade_duration:.2f}s for short segments (min: {min_segment_duration:.2f}s)")
        else:
            logger.info("Using uniform segment distribution")
            segment_duration = target_duration / len(valid_segments) if valid_segments else 3.0

        # Create clips with continuous timing and crossfades
        current_time = 0.0

        for i, segment in enumerate(valid_segments):
            try:
                # Use the FFmpeg-processed video instead of original
                video_path = segment.get('processed_path', segment['local_path'])
                video_clip = VideoFileClip(video_path)

                # Use actual segment duration if available, otherwise uniform duration
                if has_actual_durations:
                    segment_duration = segment.get('duration', 3.0)
                    # For very short segments, extend slightly to prevent black screens while preserving timing
                    if segment_duration < crossfade_duration * 1.5:
                        logger.info(f"Short segment detected ({segment_duration:.2f}s), using minimal overlap")
                        effective_crossfade = min(crossfade_duration, segment_duration / 3)
                    else:
                        effective_crossfade = crossfade_duration
                else:
                    segment_duration = target_duration / len(valid_segments) if valid_segments else 3.0
                    effective_crossfade = crossfade_duration

                start_time = current_time
                actual_duration = min(segment_duration, video_clip.duration)

                # Version-agnostic clip manipulation
                video_clip = _subclip(video_clip, 0, actual_duration)
                video_clip = _set_start(video_clip, start_time)
                video_clip = _set_end(video_clip, start_time + actual_duration)

                # Update current time for next segment
                if i < len(valid_segments) - 1:
                    current_time = start_time + actual_duration - effective_crossfade
                else:
                    current_time = start_time + actual_duration

                # Add crossfade transitions
                if i > 0 and effective_crossfade > 0:
                    video_clip = _crossfadein(video_clip, effective_crossfade)
                if i < len(valid_segments) - 1 and effective_crossfade > 0:
                    video_clip = _crossfadeout(video_clip, effective_crossfade)

                video_clips.append(video_clip)
                logger.debug(f"Clip {i}: {actual_duration:.2f}s at t={start_time:.2f}s")

            except Exception as e:
                logger.error(f"Failed to create video clip for segment {i}: {e}", exc_info=True)
                continue

        # Fill remaining time with continuous coverage if needed
        if video_clips and current_time < target_duration:
            remaining_time = target_duration - current_time
            logger.info(f"Filling remaining {remaining_time:.2f}s with continuous coverage")

            segment_index = 0
            fill_current_time = current_time - crossfade_duration

            while fill_current_time < target_duration and segment_index < len(valid_segments) * 3:
                segment = valid_segments[segment_index % len(valid_segments)]

                try:
                    video_path = segment.get('processed_path', segment['local_path'])
                    video_clip = VideoFileClip(video_path)

                    if has_actual_durations:
                        fill_segment_duration = segment.get('duration', 3.0)
                    else:
                        fill_segment_duration = segment_duration

                    fill_duration = min(fill_segment_duration, target_duration - fill_current_time + crossfade_duration)
                    fill_crossfade = min(crossfade_duration, fill_duration / 4)

                    video_clip = _subclip(video_clip, 0, min(fill_duration, video_clip.duration))
                    video_clip = _set_start(video_clip, fill_current_time)
                    video_clip = _set_end(video_clip, fill_current_time + fill_duration)

                    if fill_crossfade > 0:
                        video_clip = _crossfadein(video_clip, fill_crossfade)
                        if fill_current_time + fill_duration < target_duration:
                            video_clip = _crossfadeout(video_clip, fill_crossfade)

                    video_clips.append(video_clip)
                    fill_current_time += fill_duration - fill_crossfade
                    segment_index += 1

                except Exception as e:
                    logger.error(f"Failed to create fill clip: {e}")
                    break

        logger.info(f"Created {len(video_clips)} video clips for composition")
        return video_clips
    
    async def _compose_final_video(self, video_clips: List[VideoFileClip], target_duration: float,
                                 output_width: int, output_height: int, frame_rate: int) -> str:
        """Compose final video using MoviePy CompositeVideoClip."""
        if not video_clips:
            raise ValueError("No video clips to compose")

        output_path = os.path.join(self.temp_dir, f"composed_{uuid.uuid4()}.mp4")

        try:

            # Create composite video with explicit size to prevent black canvas
            composite_video = CompositeVideoClip(video_clips, size=(output_width, output_height))

            # Clamp to the actual extent of the clips to prevent MoviePy from
            # trying to read audio past a clip's end, which raises an OSError.
            clips_max_end = max(
                (getattr(c, 'start', 0) or 0) + c.duration
                for c in video_clips
                if c.duration
            )
            safe_duration = min(target_duration, clips_max_end)
            composite_video = _set_duration(composite_video, safe_duration)
            
            # Write video file with settings similar to original project
            # Run in executor to prevent blocking the event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: composite_video.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    fps=frame_rate,
                    preset='ultrafast',
                    logger=None,
                )
            )
            
            # Close clips to free memory
            for clip in video_clips:
                clip.close()
            composite_video.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"MoviePy composition failed: {e}")
            raise ValueError(f"Video composition failed: {str(e)}")
    
    async def _upload_to_s3(self, file_path: str) -> str:
        """Upload composed video to S3."""
        try:
            filename = f"moviepy_composed/{uuid.uuid4()}.mp4"
            s3_url = await s3_service.upload_file(file_path, filename)
            return s3_url
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise ValueError(f"S3 upload failed: {str(e)}")
    
    async def _cleanup_temp_files(self, file_paths: List[str]):
        """Clean up temporary files."""
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup {file_path}: {e}")
    
    async def create_video_from_image(self, job_id: str, params: Dict) -> Dict:
        """
        Create a video from an image with effects like zoom, pan, etc.
        
        Args:
            job_id: Unique identifier for the job
            params: Parameters including image_url, video_length, effect_type, etc.
        
        Returns:
            Dictionary with video_url and metadata
        """
        try:
            import tempfile
            import aiohttp
            
            # MoviePy imports with compatibility
            try:
                from moviepy import ImageClip, CompositeVideoClip
            except ImportError:
                from moviepy.editor import ImageClip, CompositeVideoClip
            
            # Extract parameters
            image_url = params['image_url']
            video_length = params.get('video_length', 3.0)
            frame_rate = params.get('frame_rate', 30)
            effect_type = params.get('effect_type', 'zoom')
            zoom_speed = params.get('zoom_speed', 25)
            output_width = params.get('output_width', 1080)
            output_height = params.get('output_height', 1920)
            
            logger.info(f"Creating video from image: {effect_type} effect, {video_length}s duration")
            
            # Download image
            temp_image_path = os.path.join(self.temp_dir, f"image_{job_id}.png")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download image: {response.status}")
                    
                    image_data = await response.read()
                    with open(temp_image_path, 'wb') as f:
                        f.write(image_data)
            
            # Create video with effects
            output_path = await self._create_video_with_effect(
                image_path=temp_image_path,
                effect_type=effect_type,
                duration=video_length,
                frame_rate=frame_rate,
                zoom_speed=zoom_speed,
                output_width=output_width,
                output_height=output_height,
                job_id=job_id
            )
            
            # Upload to S3
            video_url = await self._upload_to_s3(output_path)
            
            # Cleanup temp files
            await self._cleanup_temp_files([temp_image_path, output_path])
            
            # Force garbage collection to free memory
            import gc
            gc.collect()
            
            logger.info(f"Successfully created video segment: {video_url}")
            
            return {
                'video_url': video_url,
                'duration': video_length,
                'width': output_width,
                'height': output_height,
                'frame_rate': frame_rate,
                'effect_type': effect_type
            }
            
        except Exception as e:
            logger.error(f"Failed to create video from image: {str(e)}")
            
            # Cleanup on failure
            try:
                if 'temp_image_path' in locals() and os.path.exists(temp_image_path):
                    os.unlink(temp_image_path)
                if 'output_path' in locals() and os.path.exists(output_path):
                    os.unlink(output_path)
            except:
                pass
            
            # Force cleanup memory on error
            import gc
            gc.collect()
            
            raise Exception(f"Video creation failed: {str(e)}")
    
    async def _create_video_with_effect(self, image_path: str, effect_type: str, duration: float,
                                      frame_rate: int, zoom_speed: int, output_width: int,
                                      output_height: int, job_id: str) -> str:
        """Create video with visual effects from image."""
        # MoviePy imports with compatibility
        try:
            from moviepy import ImageClip, CompositeVideoClip
        except ImportError:
            from moviepy.editor import ImageClip, CompositeVideoClip
        import numpy as np
        
        output_path = os.path.join(self.temp_dir, f"video_{job_id}.mp4")
        
        try:
            # Create image clip
            image_clip = ImageClip(image_path, duration=duration)
            
            # Resize image to fit output dimensions while maintaining aspect ratio
            image_clip = _resize(image_clip, height=output_height)
            if image_clip.w < output_width:
                image_clip = _resize(image_clip, width=output_width)
            
            # Apply effects
            if effect_type == 'zoom':
                image_clip = self._apply_zoom_effect(image_clip, zoom_speed, duration)
            elif effect_type == 'pan':
                image_clip = self._apply_pan_effect(image_clip, duration)
            elif effect_type == 'ken_burns':
                image_clip = self._apply_ken_burns_effect(image_clip, duration, zoom_speed)
            elif effect_type == 'fade':
                image_clip = self._apply_fade_effect(image_clip, duration)
            # 'slide' and other effects can be added here
            
            # Center the clip
            image_clip = _set_position(image_clip, 'center')

            # Create composite video with explicit background
            final_video = CompositeVideoClip([image_clip], size=(output_width, output_height), bg_color=(0,0,0))
            final_video = _set_duration(final_video, duration)
            
            # Write video file
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: final_video.write_videofile(
                    output_path,
                    codec='libx264',
                    fps=frame_rate,
                    preset='fast',
                    logger=None,
                    audio=False,
                )
            )
            
            # Close clips
            image_clip.close()
            final_video.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to create video with {effect_type} effect: {str(e)}")
            raise
    
    def _apply_zoom_effect(self, clip, zoom_speed: int, duration: float):
        """Apply zoom effect using frame-level transforms (compatible with MoviePy 1.x and 2.x)."""
        import numpy as np
        from PIL import Image as PILImage

        max_zoom = 1.0 + (zoom_speed / 100.0 * 0.5)  # speed=20 → 1.1 (10% zoom)
        clip_w, clip_h = clip.size

        def process_frame(frame, t):
            progress = min(t / max(duration, 0.001), 1.0)
            zoom = 1.0 + (max_zoom - 1.0) * progress
            crop_w = max(1, int(clip_w / zoom))
            crop_h = max(1, int(clip_h / zoom))
            x = (clip_w - crop_w) // 2
            y = (clip_h - crop_h) // 2
            cropped = frame[y:y + crop_h, x:x + crop_w]
            img = PILImage.fromarray(cropped.astype(np.uint8))
            return np.array(img.resize((clip_w, clip_h), PILImage.LANCZOS))

        return clip.fl(lambda gf, t: process_frame(gf(t), t), apply_to='video')

    def _apply_pan_effect(self, clip, duration: float):
        """Apply panning effect to clip."""
        def pan_func(t):
            return ('center', 'center')  # Simplified for now

        return _set_position(clip, pan_func)

    def _apply_ken_burns_effect(self, clip, duration: float, zoom_speed: int = 20):
        """Apply Ken Burns effect: gradual zoom-in + horizontal pan.

        Uses frame-level numpy/PIL transforms so it works with both MoviePy 1.x
        and 2.x without relying on the version-sensitive resize helpers.
        """
        import numpy as np
        from PIL import Image as PILImage

        max_zoom = 1.0 + (zoom_speed / 100.0 * 0.5)  # speed=20 → 1.1 (10% zoom)
        clip_w, clip_h = clip.size

        def process_frame(frame, t):
            progress = min(t / max(duration, 0.001), 1.0)
            zoom = 1.0 + (max_zoom - 1.0) * progress
            crop_w = max(1, int(clip_w / zoom))
            crop_h = max(1, int(clip_h / zoom))
            # Pan left→right horizontally; center vertically
            max_x = clip_w - crop_w
            max_y = clip_h - crop_h
            x = int(max_x * progress)
            y = max_y // 2
            cropped = frame[y:y + crop_h, x:x + crop_w]
            img = PILImage.fromarray(cropped.astype(np.uint8))
            return np.array(img.resize((clip_w, clip_h), PILImage.LANCZOS))

        return clip.fl(lambda gf, t: process_frame(gf(t), t), apply_to='video')

    def _apply_fade_effect(self, clip, duration: float):
        """Apply fade in/out effect."""
        fade_duration = min(0.5, duration / 4)
        return _fadeout(_fadein(clip, fade_duration), fade_duration)

    def __del__(self):
        """Cleanup temp directory on destruction."""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception:
            pass