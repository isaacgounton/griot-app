import uuid
from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.models import JobResponse, JobType
from app.services.job_queue import job_queue
from app.services.media.pexels_image_service import PexelsImageService
from app.services.media.pixabay_image_service import PixabayImageService
from app.utils.auth import get_current_user

# Initialize service instances
pexels_image_service = PexelsImageService()
pixabay_image_service = PixabayImageService()

# Request models
class StockImageSearchRequest(BaseModel):
    """Request model for stock image search."""
    query: str
    orientation: str = "landscape"
    quality: str = "high"
    per_page: int = 20
    page: int = 1
    color: str | None = None
    size: str | None = None
    provider: str = "pexels"

# Response models
class ImageResult(BaseModel):
    """Individual image result."""
    id: str
    url: str
    download_url: str
    width: int
    height: int
    photographer: str | None = None
    photographer_url: str | None = None
    alt: str | None = None
    tags: str | None = None
    source: str
    aspect_ratio: float

class StockImageSearchResult(BaseModel):
    """Result model for stock image search."""
    images: list[ImageResult]
    total_results: int
    page: int
    per_page: int
    query_used: str
    provider_used: str

router = APIRouter(prefix="/ai", tags=["Research"])


async def process_stock_image_search_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Wrapper function for stock image search job processing."""
    provider = data.get('provider', 'pexels')
    
    if provider == 'pexels':
        # Convert to Pexels API format
        params = {
            'query': data['query'],
            'per_page': data.get('per_page', 20),
            'orientation': data.get('orientation', 'landscape'),
            'quality': data.get('quality', 'high'),
            'color': data.get('color'),
            'size': data.get('size')
        }
        result = await pexels_image_service.search_images(params)
        
        # Convert to standardized format
        images = []
        for img in result.get('images', []):
            images.append({
                'id': str(img.get('id', '')),
                'url': img.get('url', ''),
                'download_url': img.get('download_url', ''),
                'width': img.get('width', 0),
                'height': img.get('height', 0),
                'photographer': img.get('photographer'),
                'photographer_url': img.get('photographer_url'),
                'alt': img.get('alt', ''),
                'tags': '',
                'source': 'pexels',
                'aspect_ratio': img.get('width', 1) / max(img.get('height', 1), 1)
            })
        
        return {
            'images': images,
            'total_results': result.get('total_results', len(images)),
            'page': result.get('page', 1),
            'per_page': result.get('per_page', 20),
            'query_used': data['query'],
            'provider_used': 'pexels'
        }
    
    elif provider == 'pixabay':
        # Use Pixabay service
        images_data = await pixabay_image_service.search_images(
            query=data['query'],
            orientation=data.get('orientation', 'landscape'),
            quality=data.get('quality', 'high'),
            per_page=data.get('per_page', 20),
            color=data.get('color'),
            size=data.get('size')
        )
        
        # Convert to standardized format
        images = []
        for img in images_data:
            images.append({
                'id': str(img.get('id', '')),
                'url': img.get('url', ''),
                'download_url': img.get('download_url', ''),
                'width': img.get('width', 0),
                'height': img.get('height', 0),
                'photographer': img.get('user'),
                'photographer_url': None,
                'alt': '',
                'tags': img.get('tags', ''),
                'source': 'pixabay',
                'aspect_ratio': img.get('aspect_ratio', 1.0)
            })
        
        return {
            'images': images,
            'total_results': len(images),
            'page': 1,
            'per_page': data.get('per_page', 20),
            'query_used': data['query'],
            'provider_used': 'pixabay'
        }
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")


@router.post("/image-search/stock-images", response_model=JobResponse)
async def search_stock_images(
    request: StockImageSearchRequest,
    _: dict[str, Any] = Depends(get_current_user)
):
    """Search for stock images from Pexels or Pixabay with orientation, quality, and color filters."""
    try:
        # Validate provider
        if request.provider not in ['pexels', 'pixabay']:
            raise HTTPException(
                status_code=400,
                detail="Provider must be 'pexels' or 'pixabay'"
            )
        
        # Validate orientation
        if request.orientation not in ['landscape', 'portrait', 'square']:
            raise HTTPException(
                status_code=400,
                detail="Orientation must be 'landscape', 'portrait', or 'square'"
            )
        
        # Validate quality
        if request.quality not in ['standard', 'high', 'ultra']:
            raise HTTPException(
                status_code=400,
                detail="Quality must be 'standard', 'high', or 'ultra'"
            )
        
        # Create job
        job_id = str(uuid.uuid4())
        job_data = {
            "query": request.query,
            "orientation": request.orientation,
            "quality": request.quality,
            "per_page": min(request.per_page, 80),  # Limit to reasonable amount
            "page": request.page,
            "color": request.color,
            "size": request.size,
            "provider": request.provider
        }
        
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.IMAGE_SEARCH,
            process_func=process_stock_image_search_wrapper,
            data=job_data
        )
        
        return JobResponse(job_id=job_id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create image search job: {str(e)}"
        )


@router.get("/image-providers/status")
async def get_image_providers_status(_: dict[str, Any] = Depends(get_current_user)):
    """Get the status of available image providers."""
    return {
        "providers": {
            "pexels": {
                "available": pexels_image_service.is_available(),
                "name": "Pexels",
                "description": "High-quality stock photos from professional creators",
                "features": ["Professional Quality", "Free License", "Large Library"]
            },
            "pixabay": {
                "available": pixabay_image_service.is_available(),
                "name": "Pixabay", 
                "description": "Free stock photos with diverse library",
                "features": ["Diverse Content", "Vector Graphics", "Free License"]
            }
        },
        "supported_orientations": ["landscape", "portrait", "square"],
        "supported_qualities": ["standard", "high", "ultra"],
        "supported_colors": ["red", "orange", "yellow", "green", "turquoise", "blue", "violet", "pink", "brown", "black", "gray", "white"],
        "supported_sizes": ["large", "medium", "small"]
    }
