"""
Enhanced FFmpeg execution utilities with progress tracking and optimized output filtering.

This module provides robust FFmpeg command execution with real-time progress tracking,
intelligent output filtering, and enhanced error handling.
"""
import subprocess
import asyncio
import re
import time
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
from app.utils.logging import get_logger, log_operation_start, log_operation_complete, log_operation_error
from app.utils.progress import FFmpegProgressTracker

logger = get_logger(module="ffmpeg", component="media_processing")

class FFmpegExecutor:
    """Enhanced FFmpeg executor with progress tracking and output filtering."""
    
    # Patterns to filter from FFmpeg output to reduce noise
    FILTER_PATTERNS = [
        # Skip initialization information
        r"ffmpeg version",
        r"built with",
        r"configuration:",
        r"libav\w+",
        r"Input #\d+",
        r"Metadata:",
        r"Duration:",
        r"Stream #\d+",
        r"Press \[q\]",
        r"Output #\d+",
        r"Stream mapping:",
        
        # Skip processing details that are too verbose
        r"frame=\s*\d+",
        r"fps=\s*[\d.]+",
        r"\[libx264",
        r"kb/s:",
        r"Qavg:",
        r"video:",
        r"audio:",
        r"subtitle:",
        r"frame [IP]:",
        r"mb [IP]",
        r"coded y,",
        r"i16 v,h,dc,p:",
        r"i8c dc,h,v,p:",
        r"compatible_brands:",
        r"encoder\s*:",
        r"Side data:",
        r"libswscale",
        r"libswresample",
        r"libpostproc",
        
        # Additional metadata patterns
        r"major_brand",
        r"minor_version",
        r"creation_time",
        r"handler_name",
        r"vendor_id",
        r"bitrate",
        r"SAR \d+:\d+",
        r"DAR \d+:\d+",
        r"fps, \d+",
    ]
    
    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        """
        Initialize FFmpeg executor.
        
        Args:
            ffmpeg_path: Path to ffmpeg executable
            ffprobe_path: Path to ffprobe executable
        """
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.FILTER_PATTERNS]
        
    async def execute_with_progress(
        self,
        cmd: List[str],
        job_id: str,
        operation_name: str,
        expected_duration: Optional[float] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """
        Execute FFmpeg command with real-time progress tracking.
        
        Args:
            cmd: FFmpeg command as list
            job_id: Job identifier for progress tracking
            operation_name: Name of the operation for logging
            expected_duration: Expected output duration for progress calculation
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if successful, False otherwise
        """
        operation_logger = log_operation_start(operation_name, job_id=job_id, command=" ".join(cmd))
        start_time = time.time()
        
        # Create progress tracker
        progress_tracker = None
        if expected_duration:
            from app.utils.progress import create_ffmpeg_progress_tracker
            progress_tracker = await create_ffmpeg_progress_tracker(job_id, expected_duration)
            await progress_tracker.update_stage(
                progress_tracker.progress.stage.__class__.PROCESSING, 
                f"Starting {operation_name}"
            )
        
        try:
            # Start the FFmpeg process
            process = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                universal_newlines=True,
                text=True,
            )
            
            # Process output line by line
            async for line in self._read_process_output(process):
                # Update progress if tracker is available
                if progress_tracker:
                    await progress_tracker.parse_ffmpeg_progress(line)
                
                # Call custom progress callback if provided
                if progress_callback and expected_duration:
                    percentage = self._extract_progress_percentage(line, expected_duration)
                    if percentage is not None:
                        progress_callback(percentage, line)
                
                # Filter and log relevant output
                if self._should_log_line(line):
                    operation_logger.debug(f"ffmpeg: {line.strip()}")
            
            # Wait for process completion
            return_code = process.wait()
            
            if return_code != 0:
                # Get any remaining error output
                remaining_stderr = process.stderr.read() if process.stderr else ""
                error_msg = f"FFmpeg exited with code {return_code}"
                if remaining_stderr:
                    error_msg += f": {remaining_stderr}"
                
                if progress_tracker:
                    await progress_tracker.set_error(error_msg)
                
                log_operation_error(operation_name, Exception(error_msg), job_id=job_id)
                return False
            
            # Mark as completed
            if progress_tracker:
                await progress_tracker.complete(f"{operation_name} completed successfully")
            
            duration = time.time() - start_time
            log_operation_complete(operation_name, duration, job_id=job_id)
            return True
            
        except Exception as e:
            if progress_tracker:
                await progress_tracker.set_error(str(e))
            
            log_operation_error(operation_name, e, job_id=job_id)
            return False
    
    async def _read_process_output(self, process: subprocess.Popen):
        """
        Asynchronously read process output line by line.
        
        Args:
            process: The subprocess to read from
            
        Yields:
            Lines from stderr
        """
        while True:
            line = process.stderr.readline()
            if not line:
                break
            yield line.strip()
    
    def _should_log_line(self, line: str) -> bool:
        """
        Determine if a line should be logged based on filter patterns.
        
        Args:
            line: Line to check
            
        Returns:
            True if line should be logged
        """
        line_stripped = line.strip()
        
        # Skip empty lines
        if not line_stripped:
            return False
        
        # Skip lines that match filter patterns
        for pattern in self.compiled_patterns:
            if pattern.search(line_stripped):
                return False
        
        # Skip lines that are just metadata key-value pairs
        if ":" in line_stripped and any(
            header in line_stripped.lower() for header in [
                "duration", "start", "bitrate", "stream", "metadata"
            ]
        ):
            return False
        
        # Log warnings and errors
        if any(keyword in line_stripped.lower() for keyword in ["warning", "error", "failed"]):
            return True
        
        # Log important status updates
        if any(keyword in line_stripped for keyword in ["time=", "speed=", "fps="]):
            return False  # These are progress lines, handle separately
        
        return True
    
    def _extract_progress_percentage(self, line: str, expected_duration: float) -> Optional[float]:
        """
        Extract progress percentage from FFmpeg output line.
        
        Args:
            line: FFmpeg output line
            expected_duration: Expected total duration
            
        Returns:
            Progress percentage or None
        """
        if not expected_duration or "time=" not in line:
            return None
        
        try:
            # Extract time information (format: time=HH:MM:SS.MS)
            time_part = line.split("time=")[1].split(" ")[0]
            
            # Convert to seconds
            time_parts = time_part.split(":")
            if len(time_parts) == 3:
                hours, minutes, seconds = time_parts
                current_seconds = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
                
                # Calculate percentage
                percentage = min(100, (current_seconds / expected_duration) * 100)
                return percentage
                
        except (ValueError, IndexError):
            pass
        
        return None
    
    async def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get media file information using ffprobe.
        
        Args:
            file_path: Path to media file
            
        Returns:
            Dictionary with media information
        """
        operation_logger = log_operation_start("get_media_info", file_path=file_path)
        
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                "-select_streams", "v:0",  # Select first video stream
                file_path,
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"ffprobe failed: {stderr}")
            
            import json
            probe_data = json.loads(stdout)
            
            # Extract useful information
            format_info = probe_data.get("format", {})
            streams = probe_data.get("streams", [])
            
            media_info = {
                "duration": float(format_info.get("duration", 0)),
                "size": int(format_info.get("size", 0)),
                "bit_rate": int(format_info.get("bit_rate", 0)),
                "format_name": format_info.get("format_name", ""),
                "streams": len(streams)
            }
            
            # Add video-specific info if available
            if streams:
                video_stream = streams[0]
                media_info.update({
                    "width": video_stream.get("width"),
                    "height": video_stream.get("height"),
                    "codec": video_stream.get("codec_name", ""),
                    "fps": eval(video_stream.get("r_frame_rate", "0/1")) if video_stream.get("r_frame_rate") else 0
                })
            
            log_operation_complete("get_media_info", file_path=file_path)
            return media_info
            
        except Exception as e:
            log_operation_error("get_media_info", e, file_path=file_path)
            return {}
    
    def format_duration(self, seconds: float) -> str:
        """
        Format duration in HH:MM:SS format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

# Global FFmpeg executor instance
ffmpeg_executor = FFmpegExecutor()

# Convenience functions
async def execute_ffmpeg_with_progress(
    cmd: List[str],
    job_id: str,
    operation_name: str,
    expected_duration: Optional[float] = None
) -> bool:
    """Execute FFmpeg command with progress tracking."""
    return await ffmpeg_executor.execute_with_progress(
        cmd, job_id, operation_name, expected_duration
    )

async def get_media_info(file_path: str) -> Dict[str, Any]:
    """Get media file information."""
    return await ffmpeg_executor.get_media_info(file_path)