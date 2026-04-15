"""
Admin endpoints for job management and cleanup.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime, timezone
import logging

from app.utils.auth import get_current_user
from app.services.job_queue import job_queue
from app.services.settings.scheduler_service import scheduler_service
from app.services.database.database_service import db_job_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/jobs", tags=["Admin"])


@router.post("/cleanup")
async def manual_cleanup(
    max_age_hours: int = 24,
    _: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Manually trigger job cleanup.
    
    Args:
        max_age_hours: Maximum age of jobs to keep (default: 24 hours)
        
    Returns:
        Cleanup result with statistics
    """
    try:
        start_time = datetime.now(timezone.utc)
        
        # Perform cleanup
        cleanup_result = await job_queue.cleanup_old_jobs(max_age_hours=max_age_hours)
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        return {
            "success": True,
            "message": f"Job cleanup completed successfully. Deleted {cleanup_result['total_deleted']} jobs.",
            "max_age_hours": max_age_hours,
            "duration_seconds": round(duration, 2),
            "timestamp": end_time.isoformat(),
            "cleanup_stats": cleanup_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.get("/cleanup/status")
async def get_cleanup_status(_: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current cleanup and scheduler status."""
    try:
        # Initialize default response
        response = {
            "scheduler": {
                "running": False,
                "error": None
            },
            "job_counts": {
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Try to get scheduler status
        try:
            response["scheduler"] = scheduler_service.get_status()
        except Exception as sched_error:
            logger.warning(f"Failed to get scheduler status: {sched_error}")
            response["scheduler"]["error"] = str(sched_error)
        
        # Try to get job counts
        try:
            counts = await db_job_service.get_job_count_by_status()
            # Convert count keys to match expected response format
            response["job_counts"] = {
                "pending": counts.get("pending", 0),
                "processing": counts.get("processing", 0),
                "completed": counts.get("completed", 0),
                "failed": counts.get("failed", 0)
            }
        except Exception as job_error:
            logger.warning(f"Failed to get job counts: {job_error}")
            # Keep default counts if query fails
        
        return response
        
    except Exception as e:
        logger.error(f"Error in cleanup status endpoint: {e}")
        # Return a valid response even if something goes wrong
        return {
            "scheduler": {"running": False, "error": str(e)},
            "job_counts": {"pending": 0, "processing": 0, "completed": 0, "failed": 0},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "error"
        }


@router.post("/cleanup/trigger")
async def trigger_cleanup_now(_: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Trigger immediate cleanup using scheduler service.
    """
    try:
        result = await scheduler_service.trigger_cleanup_now()
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Unknown error")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger cleanup: {str(e)}"
        )


@router.get("/stats")
async def get_job_statistics(_: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get comprehensive job statistics.
    """
    try:
        # Get job counts by status
        job_counts = await db_job_service.get_job_count_by_status()
        
        # Get recent jobs
        recent_jobs = await db_job_service.get_all_jobs(limit=10)
        
        # Calculate total jobs
        total_jobs = sum(job_counts.values())
        
        return {
            "job_counts": job_counts,
            "total_jobs": total_jobs,
            "recent_jobs": len(recent_jobs),
            "scheduler_status": scheduler_service.get_status(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.delete("/jobs/{job_id}")
async def delete_specific_job(
    job_id: str,
    _: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete a specific job by ID.
    
    Args:
        job_id: The job ID to delete
        
    Returns:
        Deletion result
    """
    try:
        # Check if job exists
        job_info = await job_queue.get_job_info(job_id)
        if not job_info:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        
        # Delete the job
        success = await db_job_service.delete_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete job {job_id}"
            )
        
        return {
            "success": True,
            "message": f"Job {job_id} deleted successfully",
            "job_id": job_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting job: {str(e)}"
        )


@router.post("/scheduler/start")
async def start_scheduler(_: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Start the background scheduler."""
    try:
        if scheduler_service.running:
            return {
                "success": True,
                "message": "Scheduler is already running",
                "status": scheduler_service.get_status()
            }
        
        await scheduler_service.start()
        
        return {
            "success": True,
            "message": "Scheduler started successfully",
            "status": scheduler_service.get_status()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start scheduler: {str(e)}"
        )


@router.post("/scheduler/stop")
async def stop_scheduler(_: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Stop the background scheduler."""
    try:
        if not scheduler_service.running:
            return {
                "success": True,
                "message": "Scheduler is already stopped",
                "status": scheduler_service.get_status()
            }
        
        await scheduler_service.stop()
        
        return {
            "success": True,
            "message": "Scheduler stopped successfully",
            "status": scheduler_service.get_status()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop scheduler: {str(e)}"
        )