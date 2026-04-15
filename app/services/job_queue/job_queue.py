"""
Job queue service for handling asynchronous jobs.
"""
from datetime import datetime, timezone
import uuid
import traceback
import psutil
import os
from typing import Dict, Optional, List, Any, Callable, Awaitable
import asyncio
from app.models import Job, JobStatus, JobType
from app.services.database.database_service import db_job_service
from loguru import logger

class JobInfo:
    """Job info class for simplified job information."""
    def __init__(self, job: Job):
        self.id = job.id
        # Handle enum compatibility issues for status
        try:
            if isinstance(job.status, str):
                # Convert string to JobStatus enum
                from app.models import JobStatus
                self.status = JobStatus(job.status.lower())
            else:
                self.status = job.status
        except (ValueError, AttributeError):
            # Fallback to string value if enum conversion fails
            self.status = str(job.status).lower()
            
        self.result = job.result
        self.error = job.error
        self.progress = getattr(job, 'progress', None)
        self.created_at = job.created_at
        self.updated_at = job.updated_at
        self.job_type = getattr(job, 'operation', 'unknown')  # job.operation contains the job type
        self.data = getattr(job, 'params', {})  # job.params contains the job data

class JobQueue:
    """Job queue service."""
    
    def __init__(self, max_queue_size: int = 15):
        """Initialize job queue."""
        self.jobs: Dict[str, Job] = {}
        self.max_queue_size = max_queue_size
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        self.redis_service = None
        self.last_memory_log = 0  # Initialize memory logging timestamp
        
        # Operation-specific concurrency limits
        self.operation_limits = {
            'text_to_speech': 1,  # Limit TTS to 1 concurrent job due to model thread-safety
            'tts': 1,
        }
        
        logger.info(f"Initialized job queue with max size {max_queue_size}")
    
    def _log_memory_usage(self, context: str = ""):
        """Log current memory usage."""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # Log every 30 seconds or when memory usage is high
            current_time = datetime.now().timestamp()
            if current_time - self.last_memory_log > 30 or memory_mb > 1000:
                logger.info(f"💾 Memory usage {context}: {memory_mb:.1f} MB")
                self.last_memory_log = current_time
                
                # Log warning if memory usage is very high
                if memory_mb > 1500:
                    logger.warning(f"⚠️  High memory usage detected: {memory_mb:.1f} MB")
        except Exception as e:
            logger.debug(f"Unable to monitor memory usage: {e}")
    
    def set_redis_service(self, redis_service):
        """Set Redis service for caching and job persistence fallback."""
        self.redis_service = redis_service
        logger.info("Redis service connected (used for caching and job persistence fallback)")
        self._log_memory_usage("(Redis connected)")
    
    def _sanitize_for_json(self, data):
        """Recursively sanitize data for JSON serialization by converting Pydantic models to strings."""
        import json
        from pydantic import BaseModel
        
        if data is None:
            return None
        elif isinstance(data, (str, int, float, bool)):
            return data
        elif isinstance(data, dict):
            return {key: self._sanitize_for_json(value) for key, value in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._sanitize_for_json(item) for item in data]
        elif isinstance(data, BaseModel):
            # Convert Pydantic models to dict
            return self._sanitize_for_json(data.model_dump())
        elif hasattr(data, '__str__'):
            # Convert any object with __str__ (like AnyUrl) to string
            return str(data)
        else:
            return str(data)
    
    async def _persist_job(self, job: Job):
        """Persist job to database and Redis for durability and multi-container support."""
        db_success = False
        redis_success = False
        
        # Try database first
        try:
            logger.info(f"Persisting job {job.id} with status {job.status} to database")
            await db_job_service.save_job(job)
            logger.info(f"Successfully persisted job {job.id} to database")
            db_success = True
        except Exception as e:
            logger.warning(f"Failed to persist job {job.id} to database: {e}")
        
        # Also persist to Redis as fallback for multi-container deployments
        if self.redis_service:
            try:
                # Serialize job to dict for Redis storage, sanitizing Pydantic models
                job_data = {
                    "id": job.id,
                    "operation": job.operation,
                    "params": self._sanitize_for_json(job.params),
                    "status": job.status.value if hasattr(job.status, 'value') else str(job.status),
                    "result": self._sanitize_for_json(job.result),
                    "error": job.error,
                    "created_at": job.created_at,
                    "updated_at": job.updated_at
                }
                
                # Store in Redis with 48-hour expiration (jobs older than this should be cleaned up anyway)
                await self.redis_service.set(f"job:{job.id}", job_data, expire=172800)
                logger.debug(f"Persisted job {job.id} to Redis cache")
                redis_success = True
            except Exception as e:
                logger.warning(f"Failed to persist job {job.id} to Redis: {e}")
        
        # Log critical error if both persistence methods failed
        if not db_success and not redis_success:
            logger.error(f"⚠️ CRITICAL: Failed to persist job {job.id} to both database and Redis!")
            logger.error(f"Job may not be retrievable in multi-container deployments!")
        elif not db_success:
            logger.info(f"Job {job.id} persisted to Redis only (database unavailable)")
        elif not redis_success:
            logger.info(f"Job {job.id} persisted to database only (Redis unavailable)")
    
    async def _save_video_if_applicable(self, job: Job):
        """Save media record to comprehensive library (replaces video-only saving)."""
        # Operations that should be saved to the media library
        library_operations = [
            # Video operations
            'footage_to_video', 'aiimage_to_video', 'scenes_to_video', 'short_video_creation', 'image_to_video',
            'video_generation', 'video_from_image', 'wavespeed_text_to_video', 'wavespeed_image_to_video',
            'video_concatenation', 'video_add_audio', 'video_add_captions', 'video_overlay', 'text_overlay',
            'ffmpeg_compose', 'youtube_shorts',
            # Audio operations
            'text_to_speech', 'tts', 'music_generation', 'generate_music', 'audio_transcription', 'transcribe',
            'pollinations_audio', 'media_audio_analysis',
            # Image operations
            'image_generation', 'generate_image', 'image_editing', 'edit_image', 'image_upscaling', 'upscale_image',
            'pollinations_image', 'image_overlay', 'video_thumbnails', 'video_frames', 'image_search', 'image_enhancement',
            'web_screenshot',  # Web page screenshots
            # Document operations
            'document_to_markdown', 'marker_document_conversion', 'pollinations_text',
            'pollinations_video_analysis',
            'ai_script_generation', 'research_news',
            # Media processing operations
            'media_download', 'download_media', 'media_conversion', 'convert_media',
            'metadata_extraction', 'extract_metadata', 'youtube_transcript', 'youtube_transcripts',
            'media_transcription', 'video_clips', 's3_upload', 'code_execution'
        ]
        
        if job.operation.lower() in library_operations and job.result:
            try:
                # Save to comprehensive media library
                from app.services.dashboard.media_library_service import media_library_service
                media_record = await media_library_service.save_media_from_job(job)
                if media_record:
                    logger.info(f"Saved media record for job {job.id}: {media_record.title} ({media_record.media_type.value})")
                else:
                    logger.warning(f"Failed to save media record for job {job.id}")
                
                # Also save videos to the legacy video service for backward compatibility
                video_operations = ['footage_to_video', 'aiimage_to_video', 'scenes_to_video', 'short_video_creation', 'image_to_video']
                if job.operation.lower() in video_operations:
                    try:
                        from app.services.video.video_service import VideoService
                        video_service = VideoService()
                        video_record = await video_service.save_video_from_job(job)
                        if video_record:
                            logger.info(f"Also saved to legacy video library for job {job.id}")
                    except Exception as e:
                        logger.error(f"Error saving to legacy video library for job {job.id}: {e}")
                        
            except Exception as e:
                logger.error(f"Error saving media record for job {job.id}: {e}")
    
    async def _mark_job_schedulable(self, job: Job):
        """Mark job as ready for social media scheduling if applicable."""
        schedulable_operations = [
            'footage_to_video',
            'aiimage_to_video', 
            'scenes_to_video',
            'short_video_creation',
            'image_to_video',
            'image_generation',
            'audio_generation'
        ]
        
        if job.operation.lower() in schedulable_operations and job.result:
            try:
                # Add scheduling metadata to job result
                if not isinstance(job.result, dict):
                    job.result = {"result": job.result}
                
                job.result["scheduling"] = {
                    "available": True,
                    "marked_at": datetime.now(timezone.utc).isoformat(),
                    "content_type": self._get_content_type_for_operation(job.operation),
                    "suggested_content": self._generate_suggested_content(job)
                }
                
                # Update the job in database with scheduling info
                await self._persist_job(job)
                logger.info(f"Marked job {job.id} as schedulable for social media")
                
            except Exception as e:
                logger.error(f"Error marking job {job.id} as schedulable: {e}")
    
    def _get_content_type_for_operation(self, operation: str) -> str:
        """Get content type for social media scheduling based on operation."""
        video_operations = ['footage_to_video', 'aiimage_to_video', 'scenes_to_video', 'short_video_creation', 'image_to_video']
        image_operations = ['image_generation']
        audio_operations = ['audio_generation']
        
        if operation.lower() in video_operations:
            return "video"
        elif operation.lower() in image_operations:
            return "image"
        elif operation.lower() in audio_operations:
            return "audio"
        else:
            return "unknown"
    
    def _generate_suggested_content(self, job: Job) -> str:
        """Generate suggested social media content based on job type and result."""
        try:
            operation = job.operation.lower()
            
            # Extract title or topic from job params or result
            title = ""
            if isinstance(job.params, dict):
                title = job.params.get("title", "") or job.params.get("topic", "") or job.params.get("prompt", "")
            
            if not title and isinstance(job.result, dict):
                title = job.result.get("title", "") or job.result.get("topic", "")
            
            # Generate content based on operation type
            if operation in ['footage_to_video', 'aiimage_to_video', 'scenes_to_video', 'short_video_creation']:
                if title:
                    return f"🎬 Just created an amazing video about {title}! Check it out! #video #content #creation"
                else:
                    return "🎬 Just created an amazing new video! Check it out! #video #content #creation"
            
            elif operation == 'image_to_video':
                return "🎥 Transformed a static image into an amazing video! #imagetoVideo #AIcreation #video"
            
            elif operation == 'image_generation':
                if title:
                    return f"🎨 Generated a stunning image: {title} #AIart #imageGeneration #creativity"
                else:
                    return "🎨 Just generated a stunning AI image! #AIart #imageGeneration #creativity"
            
            elif operation == 'audio_generation':
                if title:
                    return f"🎵 Created amazing audio content: {title} #audio #AIgenerated #sound"
                else:
                    return "🎵 Just created amazing AI-generated audio! #audio #AIgenerated #sound"
            
            else:
                return f"✨ Just completed an amazing {operation} project! #AI #automation #creation"
                
        except Exception as e:
            logger.error(f"Error generating suggested content for job {job.id}: {e}")
            return "✨ Just completed an amazing AI project! #AI #automation #creation"
    
    async def recover_jobs(self):
        """Recover jobs from database on startup.

        PROCESSING jobs cannot be resumed (no process function available),
        so they are marked as FAILED to prevent them being stuck forever.
        """
        try:
            # Get all jobs that are not completed or failed (active jobs)
            try:
                active_jobs = await db_job_service.get_jobs_by_status(JobStatus.PENDING)
                active_jobs += await db_job_service.get_jobs_by_status(JobStatus.PROCESSING)
            except Exception as enum_error:
                logger.warning(f"Job recovery failed due to enum compatibility: {enum_error}")
                logger.info("Skipping job recovery - this is safe for a fresh deployment")
                active_jobs = []

            recovered_count = 0
            failed_count = 0
            for job in active_jobs:
                if job.status == JobStatus.PROCESSING:
                    # PROCESSING jobs can't be resumed — mark as failed
                    job.status = JobStatus.FAILED
                    job.error = "Job was interrupted by server restart"
                    job.updated_at = datetime.now(timezone.utc).isoformat()
                    await self._persist_job(job)
                    failed_count += 1
                    logger.info(f"Marked stale PROCESSING job {job.id} as FAILED")
                # Add to in-memory storage
                self.jobs[job.id] = job
                recovered_count += 1
                logger.debug(f"Recovered job {job.id} with status {job.status}")

            logger.info(f"Recovered {recovered_count} jobs from database ({failed_count} stale PROCESSING jobs marked as FAILED)")
        except Exception as e:
            logger.error(f"Failed to recover jobs from database: {e}")
        
    def get_pending_jobs_count(self) -> int:
        """Get number of pending jobs."""
        return sum(1 for job in self.jobs.values() if job.status == JobStatus.PENDING)
    
    def get_processing_jobs_count(self) -> int:
        """Get number of processing jobs."""
        return sum(1 for job in self.jobs.values() if job.status == JobStatus.PROCESSING)
    
    def is_queue_full(self, operation: Optional[str] = None) -> bool:
        """Check if queue is full, optionally for a specific operation."""
        total_pending = self.get_pending_jobs_count()
        total_processing = self.get_processing_jobs_count()
        
        # Check global queue limit
        if (total_pending + total_processing) >= self.max_queue_size:
            return True
            
        # Check operation-specific limit if provided
        if operation and operation in self.operation_limits:
            limit = self.operation_limits[operation]
            operation_processing = sum(1 for job in self.jobs.values() 
                                    if job.status == JobStatus.PROCESSING and job.operation == operation)
            if operation_processing >= limit:
                logger.info(f"Operation {operation} has reached its concurrency limit of {limit}")
                return True
                
        return False
    
    async def create_job(self, operation: str, params: Dict[str, Any]) -> str:
        """Create a new job and add it to the queue."""
        if self.is_queue_full(operation):
            logger.warning(f"Job queue is full for operation {operation}. Rejecting new job.")
            raise ValueError("Job queue is full. Please try again later.")
            
        job_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        job = Job(
            id=job_id,
            operation=operation,
            params=params,
            created_at=timestamp,
            updated_at=timestamp
        )
        
        self.jobs[job_id] = job
        # Persist job to Redis
        await self._persist_job(job)
        logger.info(f"Created new job {job_id} for operation {operation}")
        return job_id
        
    async def add_job(self, job_id: str, job_type: JobType, process_func: Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]], data: Dict[str, Any]) -> str:
        """
        Add a new job to the queue and start processing it asynchronously.
        
        Args:
            job_id: The ID of the job.
            job_type: The type of the job.
            process_func: Function to process the job.
            data: Data for the job.
            
        Returns:
            Job ID
            
        Raises:
            ValueError: If the queue is full.
        """
        if self.is_queue_full(job_type.value):
            logger.warning(f"Job queue is full for operation {job_type.value}. Rejecting new job.")
            raise ValueError("Job queue is full. Please try again later.")
            
        timestamp = datetime.now(timezone.utc).isoformat()
        
        job = Job(
            id=job_id,
            operation=job_type.value,
            params=data,
            status=JobStatus.PENDING,
            created_at=timestamp,
            updated_at=timestamp
        )
        
        self.jobs[job_id] = job
        logger.info(f"Created new job {job_id} for operation {job_type.value}")
        
        # Persist job to database first (synchronously to avoid race conditions)
        await self._persist_job(job)
        
        # Start processing the job asynchronously (don't await)
        task = asyncio.create_task(self._process_job_wrapper(job_id, process_func, data))

        # Add error callback to prevent silent exceptions
        def task_callback(t: asyncio.Task):
            try:
                if t.exception():
                    logger.error(f"Task for job {job_id} failed with exception: {t.exception()}")
            except asyncio.CancelledError:
                logger.warning(f"Task for job {job_id} was cancelled")

        task.add_done_callback(task_callback)
        self.processing_tasks[job_id] = task

        return job_id
    
    async def _process_job_wrapper(self, job_id: str, process_func: Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]], data: Dict[str, Any]):
        """
        Process a job using the provided function.
        
        Args:
            job_id: The ID of the job.
            process_func: Function to process the job.
            data: Data for the job.
        """
        job = self.jobs.get(job_id)
        if not job:
            logger.warning(f"Attempted to process non-existent job {job_id}")
            return
        
        # Log memory before processing
        self._log_memory_usage(f"(before job {job_id})")
        
        # Update job status to processing
        logger.info(f"Before updating job {job_id} to PROCESSING: current status = {job.status}, job id in self.jobs = {job_id in self.jobs}")
        job.status = JobStatus.PROCESSING
        job.updated_at = datetime.now(timezone.utc).isoformat()
        logger.info(f"After updating job {job_id} to PROCESSING: new status = {job.status}")

        # Replace the job object in self.jobs to ensure reference is updated
        self.jobs[job_id] = job

        await self._persist_job(job)
        logger.info(f"Job {job_id} status updated to PROCESSING")
        
        try:
            # Process job
            result = await process_func(job_id, data)

            # Update job status to completed
            logger.info(f"Updating job {job_id} status to COMPLETED")
            job.status = JobStatus.COMPLETED
            job.result = result
            job.updated_at = datetime.now(timezone.utc).isoformat()
            logger.info(f"Job {job_id} in-memory status: {job.status}")

            # Replace the job object in self.jobs to ensure reference is updated
            self.jobs[job_id] = job

            await self._persist_job(job)
            logger.info(f"Job {job_id} persisted to database and Redis")

            # Save video record if this is a video generation job
            await self._save_video_if_applicable(job)

            # Mark job as ready for social media scheduling
            await self._mark_job_schedulable(job)

            logger.info(f"Job {job_id} processed successfully")
        except Exception as e:
            # Get the full traceback
            tb = traceback.format_exc()

            # Update job status to failed
            job.status = JobStatus.FAILED
            job.error = f"{str(e)}\n\nTraceback:\n{tb}"
            job.updated_at = datetime.now(timezone.utc).isoformat()

            # Replace the job object in self.jobs to ensure reference is updated
            self.jobs[job_id] = job

            await self._persist_job(job)
            logger.error(f"Error processing job {job_id}: {e}\n{tb}")
        finally:
            # Log memory after processing
            self._log_memory_usage(f"(after job {job_id})")
            
            # Remove task from processing tasks
            if job_id in self.processing_tasks:
                del self.processing_tasks[job_id]
    
    async def get_job_info(self, job_id: str) -> Optional[JobInfo]:
        """
        Get job information by ID.

        Args:
            job_id: The ID of the job.

        Returns:
            JobInfo object or None if job not found.
        """
        # Always try to get the latest from database first for accuracy
        # This ensures we get the most up-to-date status even if in-memory cache is stale
        try:
            job = await db_job_service.get_job(job_id)
            if job:
                logger.debug(f"Found job {job_id} in database with status {job.status}")
                # Update in-memory cache with fresh data from database
                self.jobs[job_id] = job
                return JobInfo(job)
        except Exception as e:
            logger.warning(f"Error retrieving job {job_id} from database: {e}")

        # Fallback to in-memory jobs if database is unavailable
        job = self.jobs.get(job_id)
        if job:
            logger.debug(f"Returning job {job_id} from in-memory cache with status {job.status}")
            return JobInfo(job)

        # If not in memory, check Redis cache (for multi-container deployments)
        if self.redis_service:
            try:
                job_data = await self.redis_service.get(f"job:{job_id}")
                if job_data:
                    logger.debug(f"Found job {job_id} in Redis cache")
                    # Reconstruct Job object from Redis data
                    job = Job(
                        id=job_data["id"],
                        operation=job_data["operation"],
                        params=job_data["params"],
                        status=JobStatus(job_data["status"]) if isinstance(job_data["status"], str) else job_data["status"],
                        result=job_data.get("result"),
                        error=job_data.get("error"),
                        created_at=job_data["created_at"],
                        updated_at=job_data["updated_at"]
                    )
                    # Add to in-memory cache for faster subsequent access
                    self.jobs[job_id] = job
                    return JobInfo(job)
            except Exception as e:
                logger.warning(f"Error retrieving job {job_id} from Redis: {e}")
        
        logger.warning(f"Job {job_id} not found in memory, Redis, or database")
        return None
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        # First check in-memory jobs
        job = self.jobs.get(job_id)
        if job:
            return job
        
        # If not in memory, check database
        try:
            job = await db_job_service.get_job(job_id)
            if job:
                logger.debug(f"Found job {job_id} in database")
                return job
        except Exception as e:
            logger.error(f"Error retrieving job {job_id} from database: {e}")
        
        logger.warning(f"Job {job_id} not found in memory or database")
        return None
    
    async def process_job(self, job_id: str, handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]):
        """Process a job with the given handler."""
        job = self.jobs.get(job_id)
        if not job:
            logger.warning(f"Attempted to process non-existent job {job_id}")
            return
        
        # Job status is already set to PROCESSING in start_job_processing
        logger.info(f"Processing job {job_id} ({job.operation})")
        
        try:
            # Process job
            result = await handler(job.params)
            
            # Update job status to completed
            job.status = JobStatus.COMPLETED
            job.result = result
            job.updated_at = datetime.now(timezone.utc).isoformat()
            await self._persist_job(job)
            
            # Save video record if applicable
            await self._save_video_if_applicable(job)
            
            # Mark job as ready for social media scheduling
            await self._mark_job_schedulable(job)
            
            logger.info(f"Job {job_id} processed successfully")
        except Exception as e:
            # Get the full traceback
            tb = traceback.format_exc()

            # Update job status to failed
            job.status = JobStatus.FAILED
            job.error = f"{str(e)}\n\nTraceback:\n{tb}"
            job.updated_at = datetime.now(timezone.utc).isoformat()

            # Replace the job object in self.jobs to ensure reference is updated
            self.jobs[job_id] = job

            await self._persist_job(job)
            logger.error(f"Error processing job {job_id}: {e}\n{tb}")
        finally:
            # Remove task from processing tasks
            if job_id in self.processing_tasks:
                del self.processing_tasks[job_id]
    
    def start_job_processing(self, job_id: str, handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]):
        """Start processing a job."""
        job = self.jobs.get(job_id)
        if not job:
            logger.warning(f"Attempted to start processing of non-existent job {job_id}")
            return
            
        if job.status != JobStatus.PENDING:
            logger.warning(f"Attempted to start processing of job {job_id} with status {job.status}")
            return
        
        # Update job status to processing immediately
        job.status = JobStatus.PROCESSING
        job.updated_at = datetime.now(timezone.utc).isoformat()
        logger.info(f"Job {job_id} status updated to PROCESSING")
        
        # Create and start the processing task
        logger.info(f"Starting job {job_id} processing task")
        task = asyncio.create_task(self.process_job(job_id, handler))
        self.processing_tasks[job_id] = task
    
    async def get_all_jobs(self, limit: int = 100) -> List[tuple[str, JobInfo]]:
        """Get all jobs with their JobInfo, including from database."""
        jobs_list = []
        job_ids_seen = set()
        
        # First add in-memory jobs (these are most current)
        for job_id, job in self.jobs.items():
            job_info = JobInfo(job)
            jobs_list.append((job_id, job_info))
            job_ids_seen.add(job_id)
        
        # Then add recent jobs from database (to show completed jobs)
        try:
            db_jobs = await db_job_service.get_all_jobs(limit=limit)
            logger.debug(f"Retrieved {len(db_jobs)} jobs from database")
            for job in db_jobs:
                if job.id not in job_ids_seen:
                    try:
                        job_info = JobInfo(job)
                        jobs_list.append((job.id, job_info))
                        job_ids_seen.add(job.id)
                        logger.debug(f"Added job {job.id} from database to jobs list")
                    except Exception as job_error:
                        logger.warning(f"Skipping job {job.id} due to enum compatibility: {job_error}")
                        continue
                else:
                    logger.debug(f"Skipped job {job.id} from database (already in memory)")
        except Exception as e:
            logger.error(f"Failed to get jobs from database: {e}")
        
        # Sort by created_at descending (newest first)
        jobs_list.sort(key=lambda x: x[1].created_at, reverse=True)
        return jobs_list[:limit]  # Limit the total results
    
    async def retry_job(self, job_id: str) -> bool:
        """Retry a failed job with the same parameters."""
        if job_id not in self.jobs:
            # Try to load from database
            try:
                job = await db_job_service.get_job(job_id)
                if not job:
                    logger.error(f"Job {job_id} not found for retry")
                    return False
                self.jobs[job_id] = job
            except Exception as e:
                logger.error(f"Failed to load job {job_id} for retry: {e}")
                return False
        
        job = self.jobs[job_id]
        
        # Only allow retry for failed jobs
        if job.status != JobStatus.FAILED:
            logger.warning(f"Cannot retry job {job_id} with status {job.status}")
            return False
        
        # Cancel any existing processing task
        if job_id in self.processing_tasks:
            task = self.processing_tasks[job_id]
            if not task.done():
                task.cancel()
            del self.processing_tasks[job_id]
        
        # Reset job status and error
        job.status = JobStatus.PENDING
        job.error = None
        job.result = None
        job.updated_at = datetime.now(timezone.utc).isoformat()
        
        # Persist the reset state
        await self._persist_job(job)
        
        # Find the original process function from the job type
        # This requires storing the process function info with the job
        # For now, we'll use a mapping based on job type
        process_func = self._get_process_func_for_job_type(job.operation)
        if not process_func:
            logger.error(f"No process function found for job type {job.operation}")
            return False
        
        # Restart the job processing
        logger.info(f"Retrying job {job_id}")
        self.processing_tasks[job_id] = asyncio.create_task(
            self._process_job_wrapper(job_id, process_func, job.params or {})
        )
        
        return True
    
    def _get_process_func_for_job_type(self, job_type: str) -> Optional[Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]]]:
        """Get the appropriate process function for a job type."""
        # For now, we'll create a simple mapping for the most common job types
        # This can be expanded as needed
        
        async def video_retry_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:  # noqa: ARG001
            """Wrapper for video creation service. _job_id is required by signature but not used."""
            from app.services.ai.short_video_creation import short_video_service
            return await short_video_service.create_short_video(data)
        
        job_type_mapping = {
            'create_short_video': video_retry_wrapper,
            # Add more mappings as needed for other job types
        }
        
        return job_type_mapping.get(job_type)

    async def remove_job(self, job_id: str) -> bool:
        """Remove a job from the queue and persistent storage."""
        if job_id in self.jobs:
            # Cancel processing task if it exists
            if job_id in self.processing_tasks:
                task = self.processing_tasks[job_id]
                if not task.done():
                    task.cancel()
                del self.processing_tasks[job_id]
            
            # Remove the job from memory
            del self.jobs[job_id]
            
            # Remove from database
            try:
                deleted = await db_job_service.delete_job(job_id)
                if not deleted:
                    logger.warning(f"Job {job_id} not found in database during delete")
            except Exception as e:
                logger.error(f"Failed to remove job {job_id} from database: {e}")
                # Re-raise the exception to indicate failure
                raise
            
            logger.info(f"Successfully removed job {job_id}")
            return True
        return False
    
    async def update_job_status(self, job_id: str, status: JobStatus, result: Any = None, error: Optional[str] = None, progress: Optional[int] = None):
        """
        Update job status and persist to database.
        
        Args:
            job_id: The ID of the job to update
            status: The new status for the job
            result: Optional result data (for completed jobs)
            error: Optional error message (for failed jobs)
            progress: Optional progress percentage (for processing jobs)
        """
        job = self.jobs.get(job_id)
        if not job:
            logger.warning(f"Attempted to update status of non-existent job {job_id}")
            return
        
        # Update job fields
        job.status = status
        job.updated_at = datetime.now(timezone.utc).isoformat()
        
        if result is not None:
            job.result = result
        if error is not None:
            job.error = error
        if progress is not None:
            job.progress = progress
        
        # Persist to database
        await self._persist_job(job)
        
        # Save video record if completed and applicable
        if status == JobStatus.COMPLETED:
            await self._save_video_if_applicable(job)
        
        logger.debug(f"Updated job {job_id} status to {status}")

    async def cleanup_old_jobs(self, max_age_hours: int = 24) -> dict:
        """Clean up old completed or failed jobs."""
        try:
            # Clean up from database
            deleted_count = await db_job_service.cleanup_old_jobs(max_age_hours)
            
            # Clean up from in-memory storage as well
            now = datetime.now(timezone.utc)
            to_remove = []
            
            for job_id, job in self.jobs.items():
                if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    created_at = datetime.fromisoformat(job.created_at)
                    age = (now - created_at).total_seconds() / 3600
                    
                    if age > max_age_hours:
                        to_remove.append(job_id)
            
            for job_id in to_remove:
                del self.jobs[job_id]
                logger.debug(f"Removed old job {job_id} from memory")
                
            total_deleted = deleted_count + len(to_remove)
            logger.info(f"Cleaned up {deleted_count} jobs from database and {len(to_remove)} from memory")
            
            return {
                "database_deleted": deleted_count,
                "memory_deleted": len(to_remove),
                "total_deleted": total_deleted
            }
        except Exception as e:
            logger.error(f"Failed to cleanup old jobs: {e}")
            raise


# Create a singleton instance
job_queue = JobQueue(max_queue_size=10)
