"""
Background task scheduler service for periodic maintenance tasks.
"""
import asyncio
import os
from datetime import datetime, timezone
from typing import Optional
from loguru import logger


class SchedulerService:
    """Background task scheduler for periodic maintenance."""
    
    def __init__(self):
        """Initialize scheduler service."""
        self.running = False
        self.tasks = {}
        self.cleanup_interval = int(os.getenv('CLEANUP_INTERVAL_HOURS', '6'))  # Default: every 6 hours
        self.job_retention_hours = int(os.getenv('JOB_RETENTION_HOURS', '24'))  # Default: keep 24 hours
        logger.info(f"Scheduler initialized - cleanup every {self.cleanup_interval}h, retention {self.job_retention_hours}h")
    
    async def start(self):
        """Start all background tasks."""
        if self.running:
            logger.warning("Scheduler already running")
            return
            
        self.running = True
        logger.info("🕒 Starting background scheduler service")
        
        # Start job cleanup task
        self.tasks['job_cleanup'] = asyncio.create_task(self._job_cleanup_loop())
        
        # Start S3 cleanup task (optional)
        self.tasks['s3_cleanup'] = asyncio.create_task(self._s3_cleanup_loop())
        
        logger.info("✅ Background scheduler started successfully")
    
    async def stop(self):
        """Stop all background tasks."""
        if not self.running:
            return
            
        logger.info("🛑 Stopping background scheduler service")
        self.running = False
        
        # Cancel all tasks
        for task_name, task in self.tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.debug(f"Cancelled task: {task_name}")
        
        self.tasks.clear()
        logger.info("✅ Background scheduler stopped")
    
    async def _job_cleanup_loop(self):
        """Periodic job cleanup loop."""
        logger.info(f"🧹 Job cleanup task started (every {self.cleanup_interval} hours)")
        
        while self.running:
            try:
                # Wait for cleanup interval
                await asyncio.sleep(self.cleanup_interval * 3600)  # Convert hours to seconds
                
                if not self.running:
                    break
                
                # Perform cleanup
                cleanup_result = await self._perform_job_cleanup()
                
            except asyncio.CancelledError:
                logger.info("Job cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in job cleanup loop: {e}")
                # Continue running despite errors
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    async def _s3_cleanup_loop(self):
        """Periodic S3 cleanup loop for orphaned files."""
        logger.info("🗂️ S3 cleanup task started (daily)")
        
        while self.running:
            try:
                # Wait 24 hours between S3 cleanups
                await asyncio.sleep(24 * 3600)
                
                if not self.running:
                    break
                
                # Perform S3 cleanup (optional - only if enabled)
                if os.getenv('ENABLE_S3_CLEANUP', 'false').lower() == 'true':
                    await self._perform_s3_cleanup()
                
            except asyncio.CancelledError:
                logger.info("S3 cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in S3 cleanup loop: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying
    
    async def _perform_job_cleanup(self) -> dict:
        """Perform job cleanup operation."""
        try:
            from app.services.job_queue import job_queue
            
            logger.info(f"🧹 Starting job cleanup (retention: {self.job_retention_hours}h)")
            start_time = datetime.now()
            
            # Clean up old jobs
            cleanup_result = await job_queue.cleanup_old_jobs(max_age_hours=self.job_retention_hours)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Job cleanup completed in {duration:.2f}s - deleted {cleanup_result['total_deleted']} jobs")
            
            return cleanup_result
            
        except Exception as e:
            logger.error(f"Failed to perform job cleanup: {e}")
            raise
    
    async def _perform_s3_cleanup(self):
        """Perform S3 cleanup operation for orphaned files."""
        try:
            logger.info("🗂️ Starting S3 cleanup for orphaned files")
            start_time = datetime.now()
            
            # This is a placeholder for S3 cleanup logic
            # You could implement logic to:
            # 1. List all S3 objects older than retention period
            # 2. Check if corresponding job records exist
            # 3. Delete orphaned files
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ S3 cleanup completed in {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to perform S3 cleanup: {e}")
    
    async def trigger_cleanup_now(self) -> dict:
        """Manually trigger cleanup immediately."""
        try:
            logger.info("🚀 Manual cleanup triggered")
            cleanup_result = await self._perform_job_cleanup()
            
            return {
                "success": True,
                "message": f"Cleanup completed successfully. Deleted {cleanup_result['total_deleted']} jobs.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cleanup_stats": cleanup_result
            }
        except Exception as e:
            logger.error(f"Manual cleanup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_status(self) -> dict:
        """Get scheduler status."""
        return {
            "running": self.running,
            "cleanup_interval_hours": self.cleanup_interval,
            "job_retention_hours": self.job_retention_hours,
            "active_tasks": list(self.tasks.keys()),
            "task_count": len(self.tasks)
        }


# Singleton instance
scheduler_service = SchedulerService()