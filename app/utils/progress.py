"""
Progress tracking utilities for long-running operations.

This module provides sophisticated progress tracking and reporting
for jobs, file operations, and other time-consuming tasks.
"""
import time
import asyncio
from typing import Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from app.utils.logging import get_logger
from app.services.redis import redis_service

logger = get_logger(module="progress", component="tracking")

class ProgressStage(Enum):
    """Enumeration of progress stages for different operations."""
    INITIALIZING = "initializing"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    UPLOADING = "uploading"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ProgressInfo:
    """Progress information for tracking operation status."""
    job_id: str
    stage: ProgressStage = ProgressStage.INITIALIZING
    percentage: float = 0.0
    current_step: str = ""
    total_steps: Optional[int] = None
    current_step_number: int = 0
    start_time: float = field(default_factory=time.time)
    estimated_completion: Optional[float] = None
    bytes_processed: int = 0
    total_bytes: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time since start."""
        return time.time() - self.start_time
    
    @property
    def estimated_remaining(self) -> Optional[float]:
        """Estimate remaining time based on current progress."""
        if self.percentage <= 0:
            return None
        
        elapsed = self.elapsed_time
        if self.percentage >= 100:
            return 0
        
        # Estimate remaining time based on current progress rate
        rate = self.percentage / elapsed if elapsed > 0 else 0
        if rate > 0:
            remaining_percentage = 100 - self.percentage
            return remaining_percentage / rate
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert progress info to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "stage": self.stage.value,
            "percentage": round(self.percentage, 2),
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "current_step_number": self.current_step_number,
            "elapsed_time": round(self.elapsed_time, 2),
            "estimated_remaining": round(self.estimated_remaining, 2) if self.estimated_remaining else None,
            "bytes_processed": self.bytes_processed,
            "total_bytes": self.total_bytes,
            "error_message": self.error_message,
            "metadata": self.metadata
        }

class ProgressTracker:
    """Enhanced progress tracking with Redis persistence and real-time updates."""
    
    def __init__(self, job_id: str, total_steps: Optional[int] = None):
        """
        Initialize progress tracker.
        
        Args:
            job_id: Unique identifier for the job
            total_steps: Total number of steps in the operation
        """
        self.progress = ProgressInfo(job_id=job_id, total_steps=total_steps)
        self.redis_key = f"progress:{job_id}"
        self.update_callbacks: list[Callable[[ProgressInfo], None]] = []
        
    async def update_stage(self, stage: ProgressStage, step_description: str = ""):
        """
        Update the current stage of operation.
        
        Args:
            stage: New progress stage
            step_description: Description of current step
        """
        self.progress.stage = stage
        self.progress.current_step = step_description
        
        # Auto-calculate percentage based on stage
        stage_percentages = {
            ProgressStage.INITIALIZING: 5,
            ProgressStage.DOWNLOADING: 20,
            ProgressStage.PROCESSING: 70,
            ProgressStage.UPLOADING: 90,
            ProgressStage.FINALIZING: 95,
            ProgressStage.COMPLETED: 100,
            ProgressStage.FAILED: 0
        }
        
        if stage in stage_percentages:
            await self.update_percentage(stage_percentages[stage])
        
        await self._persist_progress()
        await self._notify_callbacks()
        
        logger.bind(
            job_id=self.progress.job_id,
            stage=stage.value,
            step=step_description,
            percentage=self.progress.percentage
        ).info(f"Progress update: {stage.value}")
        
    async def update_percentage(self, percentage: float, step_description: str = ""):
        """
        Update progress percentage.
        
        Args:
            percentage: Progress percentage (0-100)
            step_description: Optional step description
        """
        self.progress.percentage = max(0, min(100, percentage))
        if step_description:
            self.progress.current_step = step_description
            
        await self._persist_progress()
        await self._notify_callbacks()
        
    async def update_step(self, step_number: int, step_description: str):
        """
        Update current step number and description.
        
        Args:
            step_number: Current step number
            step_description: Description of the step
        """
        self.progress.current_step_number = step_number
        self.progress.current_step = step_description
        
        # Calculate percentage if total steps is known
        if self.progress.total_steps:
            percentage = (step_number / self.progress.total_steps) * 100
            await self.update_percentage(percentage)
        else:
            await self._persist_progress()
            await self._notify_callbacks()
            
    async def update_bytes(self, bytes_processed: int, total_bytes: Optional[int] = None):
        """
        Update bytes processed for file operations.
        
        Args:
            bytes_processed: Number of bytes processed
            total_bytes: Total bytes to process (optional)
        """
        self.progress.bytes_processed = bytes_processed
        if total_bytes:
            self.progress.total_bytes = total_bytes
            
        # Calculate percentage based on bytes if available
        if self.progress.total_bytes and self.progress.total_bytes > 0:
            percentage = (bytes_processed / self.progress.total_bytes) * 100
            await self.update_percentage(percentage)
        else:
            await self._persist_progress()
            await self._notify_callbacks()
            
    async def add_metadata(self, key: str, value: Any):
        """
        Add metadata to progress tracking.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.progress.metadata[key] = value
        await self._persist_progress()
        
    async def set_error(self, error_message: str):
        """
        Set error state and message.
        
        Args:
            error_message: Error description
        """
        self.progress.stage = ProgressStage.FAILED
        self.progress.error_message = error_message
        
        await self._persist_progress()
        await self._notify_callbacks()
        
        logger.bind(
            job_id=self.progress.job_id,
            error=error_message
        ).error(f"Progress tracking failed: {error_message}")
        
    async def complete(self, completion_message: str = "Operation completed successfully"):
        """
        Mark operation as completed.
        
        Args:
            completion_message: Completion message
        """
        self.progress.stage = ProgressStage.COMPLETED
        self.progress.percentage = 100.0
        self.progress.current_step = completion_message
        
        await self._persist_progress()
        await self._notify_callbacks()
        
        logger.bind(
            job_id=self.progress.job_id,
            duration=self.progress.elapsed_time
        ).info(f"Progress tracking completed in {self.progress.elapsed_time:.2f}s")
        
    def add_callback(self, callback: Callable[[ProgressInfo], None]):
        """
        Add a callback function to be called on progress updates.
        
        Args:
            callback: Function to call with ProgressInfo
        """
        self.update_callbacks.append(callback)
        
    async def _persist_progress(self):
        """Persist progress to Redis for retrieval."""
        try:
            progress_data = self.progress.to_dict()
            await redis_service.set(
                self.redis_key, 
                progress_data, 
                expire=3600  # Expire after 1 hour
            )
        except Exception as e:
            logger.warning(f"Failed to persist progress to Redis: {e}")
            
    async def _notify_callbacks(self):
        """Notify all registered callbacks of progress update."""
        for callback in self.update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.progress)
                else:
                    callback(self.progress)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

class FFmpegProgressTracker(ProgressTracker):
    """Specialized progress tracker for FFmpeg operations."""
    
    def __init__(self, job_id: str, expected_duration: Optional[float] = None):
        """
        Initialize FFmpeg progress tracker.
        
        Args:
            job_id: Job identifier
            expected_duration: Expected duration of output media in seconds
        """
        super().__init__(job_id)
        self.expected_duration = expected_duration
        
    async def parse_ffmpeg_progress(self, line: str):
        """
        Parse FFmpeg output line and update progress.
        
        Args:
            line: Line from FFmpeg stderr output
        """
        if not self.expected_duration:
            return
            
        # Look for time information in FFmpeg output
        if "time=" in line and "speed=" in line:
            try:
                # Extract time information (format: time=HH:MM:SS.MS)
                time_part = line.split("time=")[1].split(" ")[0]
                
                # Convert to seconds
                time_parts = time_part.split(":")
                if len(time_parts) == 3:
                    hours, minutes, seconds = time_parts
                    current_seconds = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
                    
                    # Calculate percentage
                    percentage = min(100, (current_seconds / self.expected_duration) * 100)
                    
                    await self.update_percentage(
                        percentage, 
                        f"Processing: {time_part} / {self._format_duration(self.expected_duration)}"
                    )
                    
            except (ValueError, IndexError) as e:
                # If parsing fails, continue silently
                pass
                
    def _format_duration(self, seconds: float) -> str:
        """Format duration in HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

# Convenience functions for easy progress tracking
async def create_progress_tracker(job_id: str, total_steps: Optional[int] = None) -> ProgressTracker:
    """Create a new progress tracker instance."""
    tracker = ProgressTracker(job_id, total_steps)
    await tracker.update_stage(ProgressStage.INITIALIZING, "Initializing operation")
    return tracker

async def create_ffmpeg_progress_tracker(job_id: str, expected_duration: Optional[float] = None) -> FFmpegProgressTracker:
    """Create a new FFmpeg progress tracker instance."""
    tracker = FFmpegProgressTracker(job_id, expected_duration)
    await tracker.update_stage(ProgressStage.INITIALIZING, "Initializing FFmpeg operation")
    return tracker

async def get_progress_info(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get current progress information for a job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Progress information dictionary or None if not found
    """
    try:
        redis_key = f"progress:{job_id}"
        progress_data = await redis_service.get(redis_key)
        return progress_data
    except Exception as e:
        logger.warning(f"Failed to get progress info for job {job_id}: {e}")
        return None