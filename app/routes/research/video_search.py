import uuid
from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from app.models import (
    JobResponse, JobType,
    VideoSearchQueryRequest,
    StockVideoSearchRequest,
)
from app.services.job_queue import job_queue
from app.services.media.pexels_service import pexels_service
from app.services.media.pixabay_service import PixabayVideoService
from app.services.media.video_search_query_generator import video_search_query_generator
from app.utils.auth import get_current_user

# Initialize services
pixabay_video_service = PixabayVideoService()

router = APIRouter(prefix="/ai", tags=["Research"])


async def process_stock_video_search_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Wrapper function for stock video search job processing."""
    return await pexels_service.search_videos(data)


async def process_video_search_queries_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Wrapper function for video search query generation job processing."""
    return await video_search_query_generator.generate_video_search_queries(data)


@router.post("/video-search/stock-videos", response_model=JobResponse)
async def search_stock_videos(
    request: StockVideoSearchRequest,
    _: dict[str, Any] = Depends(get_current_user)
):
    """Search for stock videos from Pexels with filtering by duration, resolution, and orientation."""
    job_id = str(uuid.uuid4())
    
    try:
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.STOCK_VIDEO_SEARCH,
            process_func=process_stock_video_search_wrapper,
            data=request.model_dump()
        )

        return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create stock video search job: {str(e)}")


@router.post("/video-search-queries", response_model=JobResponse)
async def generate_video_search_queries(
    request: VideoSearchQueryRequest,
    _: dict[str, Any] = Depends(get_current_user)
):
    """Generate optimized stock footage search queries from a video script using AI."""
    job_id = str(uuid.uuid4())
    
    try:
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.VIDEO_SEARCH_QUERY_GENERATION,
            process_func=process_video_search_queries_wrapper,
            data=request.model_dump()
        )
        
        return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create video search queries job: {str(e)}")
