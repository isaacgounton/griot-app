import os
import uuid
import tempfile
import logging
import asyncio
import aiohttp
from typing import List, Dict, Optional
import ffmpeg
from app.services.s3.s3 import s3_service

logger = logging.getLogger(__name__)


class BackgroundVideoComposer:
    """Utility for composing background videos with precise timing."""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="bg_video_")
    
    async def compose_timed_videos(self, video_segments: List[Dict], target_duration: float,
                                 output_width: int = 1920, output_height: int = 1080,
                                 frame_rate: int = 30) -> str:
        """
        Compose background videos with precise timing.
        
        Args:
            video_segments: List of video segment dicts with timing info
            target_duration: Total duration for the composed video
            output_width: Output video width
            output_height: Output video height
            frame_rate: Output frame rate
        
        Returns:
            S3 URL of the composed background video
        """
        
        # Validate target duration
        if target_duration <= 0.001:
            logger.warning(f"Target duration too small ({target_duration:.6f}s), setting to 1s")
            target_duration = 1.0
        elif target_duration > 600:  # More than 10 minutes
            logger.warning(f"Target duration too large ({target_duration:.1f}s), capping to 600s")
            target_duration = 600.0
        
        try:
            # Download all video segments
            downloaded_segments = await self._download_video_segments(video_segments)
            
            # Create video segments with proper timing
            timed_segments = self._create_timed_segments(downloaded_segments, target_duration)
            
            # Compose final video using FFmpeg
            output_path = await self._compose_final_video(
                timed_segments, target_duration, output_width, output_height, frame_rate
            )
            
            # Upload to S3
            s3_url = await self._upload_to_s3(output_path)
            
            # Cleanup temp files
            segment_paths = [seg['local_path'] for seg in downloaded_segments if seg and seg.get('local_path')]
            await self._cleanup_temp_files(segment_paths + [output_path])
            
            return s3_url
            
        except Exception as e:
            logger.error(f"Failed to compose background video: {e}")
            raise ValueError(f"Video composition failed: {str(e)}")
    
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
    
    def _create_timed_segments(self, downloaded_segments: List[Dict], target_duration: float) -> List[Dict]:
        """Create timed segments with proper duration handling."""
        timed_segments = []
        current_time = 0.0
        
        for i, segment in enumerate(downloaded_segments):
            if segment is None:
                # Use previous segment or create black video
                if timed_segments:
                    prev_segment = timed_segments[-1]
                    segment_duration = min(3.0, target_duration - current_time)
                    if segment_duration > 0:
                        timed_segments.append({
                            'local_path': prev_segment['local_path'],
                            'start_time': current_time,
                            'duration': segment_duration,
                            'is_repeat': True
                        })
                        current_time += segment_duration
                continue
            
            # Calculate segment duration
            desired_duration = segment.get('duration', 3.0)
            remaining_time = target_duration - current_time
            
            if remaining_time <= 0:
                break
            
            segment_duration = min(desired_duration, remaining_time)
            
            # Ensure minimum segment duration to prevent FFmpeg errors
            if segment_duration <= 0.001:
                continue
            
            timed_segments.append({
                'local_path': segment['local_path'],
                'start_time': current_time,
                'duration': segment_duration,
                'is_repeat': False
            })
            
            current_time += segment_duration
            
            if current_time >= target_duration:
                break
        
        # Fill remaining time with last segment if needed
        if current_time < target_duration and timed_segments:
            remaining_duration = target_duration - current_time
            last_segment = timed_segments[-1]
            
            timed_segments.append({
                'local_path': last_segment['local_path'],
                'start_time': current_time,
                'duration': remaining_duration,
                'is_repeat': True
            })
        
        return timed_segments
    
    async def _compose_final_video(self, timed_segments: List[Dict], target_duration: float,
                                 width: int, height: int, frame_rate: int) -> str:
        """Compose final video using stream copy when possible, like concatenate service."""
        if not timed_segments:
            raise ValueError("No video segments to compose")
        
        output_path = os.path.join(self.temp_dir, f"composed_{uuid.uuid4()}.mp4")
        
        # Check if we can use simple concatenation (no timing adjustments needed)
        can_use_stream_copy = self._can_use_stream_copy(timed_segments, target_duration)
        
        try:
            if can_use_stream_copy:
                # Use fast stream copy like concatenate service (preserves orientation)
                await self._compose_with_stream_copy(timed_segments, output_path)
            else:
                # Use re-encoding with timing adjustments
                await self._compose_with_subprocess(timed_segments, target_duration, width, height, frame_rate, output_path)
            return output_path
            
        except Exception as e:
            logger.error(f"FFmpeg composition failed: {e}")
            raise ValueError(f"Video composition failed: {str(e)}")
    
    async def _compose_with_subprocess(self, timed_segments: List[Dict], target_duration: float,
                                     width: int, height: int, frame_rate: int, output_path: str):
        """Use subprocess to compose video with proper orientation handling."""
        
        # Create file list for concat demuxer
        concat_file = os.path.join(self.temp_dir, "concat_list.txt")
        processed_segments = []
        
        # Process each segment individually first
        for i, segment in enumerate(timed_segments):
            processed_path = await self._process_segment(
                segment, i, width, height, frame_rate
            )
            processed_segments.append(processed_path)
        
        # Create concat file
        with open(concat_file, 'w') as f:
            for seg_path in processed_segments:
                f.write(f"file '{os.path.abspath(seg_path)}'\n")
        
        # Simple concat with duration limit
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            '-t', str(target_duration),
            '-y',
            output_path
        ]
        
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
        
        if process.returncode != 0:
            logger.error(f"FFmpeg failed: {stderr.decode()}")
            raise ValueError(f"FFmpeg failed: {stderr.decode()}")
    
    async def _process_segment(self, segment: Dict, index: int, width: int, height: int, frame_rate: int) -> str:
        """Process individual segment with proper scaling and duration."""
        input_path = segment['local_path']
        duration = segment['duration']
        output_path = os.path.join(self.temp_dir, f"processed_{index}.mp4")
        
        # Validate duration to prevent FFmpeg errors
        if duration <= 0.001:  # Less than 1ms
            duration = 0.1
        elif duration > 300:  # More than 5 minutes  
            duration = 300
        
        # Determine scaling approach based on target orientation
        # Handle None values gracefully
        if width is None or height is None:
            logger.error(f"Invalid dimensions received: width={width}, height={height}")
            raise ValueError(f"Width and height must be provided, got width={width}, height={height}")
        
        is_portrait = height > width
        
        # Apply two-stage approach like viral-shorts-creator for better orientation handling
        # Stage 1: Pre-limit resolution to avoid processing massive files
        base_optimization = "scale='min(1920,iw)':'min(1920,ih)':force_original_aspect_ratio=decrease"
        
        # Stage 2: Format-specific scaling and cropping/padding
        if is_portrait:
            # Portrait: Use "increase" to fill frame completely, then crop excess
            format_filter = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
            filter_complex = f"[0:v]{base_optimization},{format_filter},fps={frame_rate},setpts=PTS-STARTPTS[v]"
        else:
            # Landscape/square: Use "increase" to fill frame completely, then crop excess (prevents black bars)
            format_filter = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
            filter_complex = f"[0:v]{base_optimization},{format_filter},fps={frame_rate},setpts=PTS-STARTPTS[v]"
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-filter_complex', filter_complex,
            '-map', '[v]',
            '-t', str(duration),
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-y',
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
        
        if process.returncode != 0:
            logger.error(f"Segment processing failed: {stderr.decode()}")
            raise ValueError(f"Segment processing failed: {stderr.decode()}")
        
        return output_path
    
    def _can_use_stream_copy(self, timed_segments: List[Dict], target_duration: float) -> bool:
        """Check if we can use stream copy (no timing adjustments needed)."""
        # If all segments have standard durations and no repeats, use stream copy
        total_segment_duration = sum(seg.get('duration', 3.0) for seg in timed_segments if seg)
        
        # Allow stream copy if:
        # 1. No segments are marked as repeats
        # 2. Total duration is close to target (within 5% or 2 seconds)
        has_repeats = any(seg.get('is_repeat', False) for seg in timed_segments if seg)
        duration_diff = abs(total_segment_duration - target_duration)
        duration_close = duration_diff <= max(target_duration * 0.05, 2.0)
        
        can_use = not has_repeats and duration_close
        return can_use
    
    async def _compose_with_stream_copy(self, timed_segments: List[Dict], output_path: str):
        """Use stream copy concatenation like the working concatenate service."""
        # Create concat file list
        concat_file = os.path.join(self.temp_dir, "stream_copy_list.txt")
        
        with open(concat_file, 'w') as f:
            for segment in timed_segments:
                if segment and segment.get('local_path'):
                    f.write(f"file '{os.path.abspath(segment['local_path'])}'\n")
        
        # Use exact same command as working concatenate service
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',  # Stream copy - preserves orientation!
            '-y',
            output_path
        ]
        
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
        
        if process.returncode != 0:
            logger.error(f"Stream copy FFmpeg failed: {stderr.decode()}")
            raise ValueError(f"Stream copy failed: {stderr.decode()}")
    
    async def _upload_to_s3(self, file_path: str) -> str:
        """Upload composed video to S3."""
        try:
            filename = f"composed_videos/{uuid.uuid4()}.mp4"
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
    
    def __del__(self):
        """Cleanup temp directory on destruction."""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception:
            pass