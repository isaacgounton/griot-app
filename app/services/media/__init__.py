"""
Media search and retrieval services.
"""

from .pexels_service import PexelsVideoService
from .pixabay_service import PixabayVideoService
from .pexels_image_service import PexelsImageService
from .pixabay_image_service import PixabayImageService
from .video_search_query_generator import VideoSearchQueryGenerator

# Create service instances
pexels_video_service = PexelsVideoService()
pixabay_video_service = PixabayVideoService()
pexels_image_service = PexelsImageService()
pixabay_image_service = PixabayImageService()
video_search_query_generator = VideoSearchQueryGenerator()

__all__ = [
    "pexels_video_service",
    "pixabay_video_service",
    "pexels_image_service",
    "pixabay_image_service",
    "video_search_query_generator",
    "PexelsVideoService",
    "PixabayVideoService",
    "PexelsImageService",
    "PixabayImageService",
    "VideoSearchQueryGenerator"
] 