"""
Admin API routes for stats, jobs, system info, and security management.
"""
import os
import time
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.services.redis import redis_service
from app.utils.security_admin import security_admin
from app.middleware.security import SecurityMiddleware

router = APIRouter(tags=["Admin"])


@router.get("/admin/stats", tags=["Admin"])
async def get_admin_stats(api_key: Dict[str, Any] = Depends(get_current_user)):
    """Get dashboard statistics"""
    try:
        # Get stats from Redis/job queue
        stats = {
            "active_jobs": 0,
            "completed_jobs": 0, 
            "failed_jobs": 0,
            "redis_connected": False
        }
        
        # Try to get Redis stats
        try:
            await redis_service.ping()
            stats["redis_connected"] = True
            
            # Get job counts from Redis if available
            job_keys = await redis_service.get_keys("job:*")
            stats["active_jobs"] = len([k for k in job_keys if k.endswith(":status")])
            
        except Exception as e:
            logging.warning(f"Could not get Redis stats: {e}")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting admin stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving stats")

@router.get("/admin/jobs", tags=["Admin"])
async def get_admin_jobs(api_key: Dict[str, Any] = Depends(get_current_user)):
    """Get recent jobs"""
    try:
        jobs = []
        
        # Try to get jobs from Redis
        try:
            await redis_service.ping()
            job_keys = await redis_service.get_keys("job:*:status")
            
            for key in job_keys[:20]:  # Limit to 20 most recent
                job_id = key.split(":")[1]
                try:
                    status = await redis_service.get(key)
                    job_data = await redis_service.get(f"job:{job_id}")
                    
                    if job_data:
                        import json
                        job_info = json.loads(job_data)
                        jobs.append({
                            "id": job_id,
                            "type": job_info.get("type", "unknown"),
                            "status": status,
                            "created_at": job_info.get("created_at", time.time()),
                            "progress": job_info.get("progress", 0)
                        })
                except Exception as e:
                    logging.warning(f"Error parsing job {job_id}: {e}")
                    
        except Exception as e:
            logging.warning(f"Could not get jobs from Redis: {e}")
        
        # Sort by creation time
        jobs.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        
        return {"jobs": jobs}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting admin jobs: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving jobs")

@router.get("/admin/system", tags=["Admin"])
async def get_system_info(api_key: Dict[str, Any] = Depends(get_current_user)):
    """Get system information"""
    try:
        return {
            "debug": os.getenv('DEBUG', 'false').lower() == 'true',
            "redis_url": os.getenv('REDIS_URL', '').replace('redis://', 'redis://***@') if 'redis://' in os.getenv('REDIS_URL', '') else os.getenv('REDIS_URL', ''),
            "s3_bucket": os.getenv('S3_BUCKET_NAME', ''),
            "s3_region": os.getenv('S3_REGION', ''),
            "s3_endpoint": os.getenv('S3_ENDPOINT_URL', '') or 'AWS S3',
            "kokoro_api": os.getenv('KOKORO_API_URL', '')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving system info")


# Security Admin Endpoints

class BlockIPRequest(BaseModel):
    """Request model for blocking an IP"""
    ip: str
    permanent: bool = False
    reason: str = "Manual block via admin API"


@router.post("/admin/security/block-ip", tags=["Admin"])
async def block_ip(
    request: BlockIPRequest,
    api_key: Dict[str, Any] = Depends(get_current_user)
):
    """Permanently or temporarily block an IP address"""
    try:
        # Validate IP format
        import ipaddress
        try:
            ipaddress.ip_address(request.ip)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid IP address format")

        if request.permanent:
            # Add to permanent block list
            security_admin.block_ip_permanently(request.ip, request.reason)
            # Also add to middleware's in-memory block list
            middleware = SecurityMiddleware.get_instance()
            if middleware:
                middleware._block_ip_permanently(request.ip)

            return {
                "status": "success",
                "message": f"IP {request.ip} has been permanently blocked",
                "ip": request.ip,
                "reason": request.reason
            }
        else:
            # Add to temporary block list via middleware
            middleware = SecurityMiddleware.get_instance()
            if middleware:
                middleware._block_ip_temporarily(request.ip)
                return {
                    "status": "success",
                    "message": f"IP {request.ip} has been temporarily blocked for 1 hour",
                    "ip": request.ip,
                    "duration": "1 hour"
                }
            else:
                # Fallback to permanent if middleware not available
                security_admin.block_ip_permanently(request.ip, request.reason)
                return {
                    "status": "success",
                    "message": f"IP {request.ip} has been blocked (middleware not available, using permanent block)",
                    "ip": request.ip
                }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error blocking IP: {e}")
        raise HTTPException(status_code=500, detail=f"Error blocking IP: {str(e)}")


class UnblockIPRequest(BaseModel):
    """Request model for unblocking an IP"""
    ip: str


@router.delete("/admin/security/unblock-ip", tags=["Admin"])
async def unblock_ip(
    request: UnblockIPRequest,
    api_key: Dict[str, Any] = Depends(get_current_user)
):
    """Remove an IP from the permanent block list"""
    try:
        # Remove from permanent block list
        success = security_admin.unblock_ip(request.ip)

        # Also remove from middleware's in-memory block list if exists
        middleware = SecurityMiddleware.get_instance()
        if middleware and request.ip in middleware.blocked_ips:
            middleware.blocked_ips.discard(request.ip)

        if success:
            return {
                "status": "success",
                "message": f"IP {request.ip} has been unblocked",
                "ip": request.ip
            }
        else:
            raise HTTPException(status_code=404, detail=f"IP {request.ip} was not in the block list")

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error unblocking IP: {e}")
        raise HTTPException(status_code=500, detail=f"Error unblocking IP: {str(e)}")


@router.get("/admin/security/blocked-ips", tags=["Admin"])
async def list_blocked_ips(api_key: Dict[str, Any] = Depends(get_current_user)):
    """Get list of all permanently blocked IPs"""
    try:
        blocked_ips = security_admin.list_blocked_ips()

        # Also get temporary blocks from middleware if available
        temp_blocks = {}
        middleware = SecurityMiddleware.get_instance()
        if middleware:
            stats = middleware.get_security_stats()
            temp_blocks = stats.get("temp_blocks_remaining", {})

        return {
            "status": "success",
            "permanently_blocked": blocked_ips,
            "temporarily_blocked": temp_blocks,
            "total_permanent": len(blocked_ips),
            "total_temporary": len(temp_blocks)
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error listing blocked IPs: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing blocked IPs: {str(e)}")


@router.get("/admin/security/stats", tags=["Admin"])
async def get_security_stats(api_key: Dict[str, Any] = Depends(get_current_user)):
    """Get security statistics and attack patterns"""
    try:
        # Get middleware stats
        middleware_stats = {}
        middleware = SecurityMiddleware.get_instance()
        if middleware:
            middleware_stats = middleware.get_security_stats()

        # Get attack pattern analysis
        attack_patterns = security_admin.analyze_attack_patterns()

        return {
            "status": "success",
            "middleware": middleware_stats,
            "attack_patterns": attack_patterns
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting security stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting security stats: {str(e)}")


@router.post("/admin/security/reload-blocks", tags=["Admin"])
async def reload_permanent_blocks(api_key: Dict[str, Any] = Depends(get_current_user)):
    """Reload permanent blocks from file into middleware"""
    try:
        middleware = SecurityMiddleware.get_instance()
        if not middleware:
            raise HTTPException(status_code=503, detail="Security middleware not available")

        # Reload permanent blocks
        blocked_ips = security_admin.load_persistent_blocks()
        middleware.blocked_ips = blocked_ips

        return {
            "status": "success",
            "message": f"Reloaded {len(blocked_ips)} permanent blocks",
            "count": len(blocked_ips)
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error reloading blocks: {e}")
        raise HTTPException(status_code=500, detail=f"Error reloading blocks: {str(e)}")