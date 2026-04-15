"""
General job management endpoints for the API.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any
from app.models import JobStatus
from app.services.job_queue import job_queue
from app.utils.auth import get_current_user

router = APIRouter(prefix="/jobs", tags=["Storage & Jobs"])


@router.get("", response_model=dict)
async def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Number of jobs per page"),
    all: bool = Query(True, description="Return all jobs without pagination (API usage)"),
    _: Dict[str, Any] = Depends(get_current_user)
):
    """List all jobs with optional pagination. Returns job status, type, and results."""
    try:
        # Get all jobs from the job queue
        all_jobs = await job_queue.get_all_jobs()
        
        # Handle pagination or return all jobs
        if all:
            # Return all jobs without pagination for API usage
            jobs_page = all_jobs
            total_jobs = len(all_jobs)
            page = 1
            limit = total_jobs
        else:
            # Calculate pagination
            total_jobs = len(all_jobs)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            
            # Get jobs for current page
            jobs_page = all_jobs[start_idx:end_idx]
        
        # Convert to Job format expected by frontend
        jobs_list = []
        for job_id, job_info in jobs_page:
            # Clean params to remove binary data for JSON serialization
            clean_params = {}
            if job_info.data:
                for key, value in job_info.data.items():
                    if key == "original_image_data":
                        # Skip binary data
                        continue
                    elif key == "original_image_data_b64":
                        # Show truncated base64 for debugging
                        clean_params[key] = f"{str(value)[:50]}..." if isinstance(value, str) and len(value) > 50 else value
                    else:
                        clean_params[key] = value
            
            # Get status value safely
            status_value = job_info.status.value if isinstance(job_info.status, JobStatus) else job_info.status
            
            job_dict = {
                "id": job_id,
                "status": status_value,
                "operation": str(job_info.job_type),
                "params": clean_params,
                "result": job_info.result,
                "error": job_info.error,
                "created_at": str(job_info.created_at) if job_info.created_at else "",
                "updated_at": str(job_info.updated_at) if job_info.updated_at else ""
            }
            jobs_list.append(job_dict)
        
        return {
            "success": True,
            "data": {
                "jobs": jobs_list,
                "total": total_jobs
            },
            "page": page,
            "limit": limit
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.get("/{job_id}/status", response_model=dict)
async def get_job_status(
    job_id: str,
    _: Dict[str, Any] = Depends(get_current_user)
):
    """Get the status and result of a specific job by ID."""
    try:
        job_info = await job_queue.get_job_info(job_id)
        
        if not job_info:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Clean params to remove binary data for JSON serialization
        clean_params = {}
        if job_info.data:
            for key, value in job_info.data.items():
                if key == "original_image_data":
                    # Skip binary data
                    continue
                elif key == "original_image_data_b64":
                    # Show truncated base64 for debugging
                    clean_params[key] = f"{str(value)[:50]}..." if isinstance(value, str) and len(value) > 50 else value
                else:
                    clean_params[key] = value
        
        # Get status value safely
        status_value = job_info.status.value if isinstance(job_info.status, JobStatus) else job_info.status
        
        # Convert to format expected by frontend
        job_data = {
            "id": job_id,
            "status": status_value,
            "operation": str(job_info.job_type),
            "params": clean_params,
            "result": job_info.result,
            "error": job_info.error,
            "created_at": str(job_info.created_at) if job_info.created_at else "",
            "updated_at": str(job_info.updated_at) if job_info.updated_at else ""
        }
        
        return {
            "success": True,
            "job_id": job_id,
            "data": job_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.post("/{job_id}/retry", response_model=dict)
async def retry_job(
    job_id: str,
    _: Dict[str, Any] = Depends(get_current_user)
):
    """Retry a failed job with its original parameters. Only failed jobs can be retried."""
    try:
        job_info = await job_queue.get_job_info(job_id)
        
        if not job_info:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if job can be retried
        status_value = job_info.status.value if isinstance(job_info.status, JobStatus) else job_info.status
        if status_value != "failed":
            raise HTTPException(
                status_code=400, 
                detail=f"Only failed jobs can be retried. Current status: {status_value}"
            )
        
        # Retry the job
        retry_success = await job_queue.retry_job(job_id)
        
        if not retry_success:
            raise HTTPException(status_code=500, detail="Failed to retry job")
        
        return {
            "success": True,
            "message": f"Job {job_id} has been queued for retry",
            "job_id": job_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry job: {str(e)}")


@router.delete("/{job_id}", response_model=dict)
async def delete_job(
    job_id: str,
    _: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a specific job from the tracking system."""
    try:
        job_info = await job_queue.get_job_info(job_id)
        
        if not job_info:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Remove job from queue
        await job_queue.remove_job(job_id)
        
        return {
            "success": True,
            "message": f"Job {job_id} deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")