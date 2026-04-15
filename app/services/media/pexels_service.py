import os
import aiohttp
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class PexelsVideoService:
    """Service for searching and retrieving videos from Pexels API."""
    
    def __init__(self):
        self.api_key = os.getenv('PEXELS_API_KEY') or os.getenv('PEXELS_KEY')
        self.base_url = "https://api.pexels.com/videos"
        
        if not self.api_key:
            logger.warning("PEXELS_API_KEY not found in environment variables")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers for Pexels API."""
        if not self.api_key:
            raise ValueError("Pexels API key not configured")
        return {
            "Authorization": self.api_key,
            "User-Agent": "Media-API/1.0"
        }
    
    def _map_orientation(self, orientation: str) -> str:
        """Map orientation from our format to Pexels format."""
        orientation_map = {
            "landscape": "landscape",
            "portrait": "portrait", 
            "square": "square"
        }
        return orientation_map.get(orientation, "landscape")
    
    def _filter_videos_by_criteria(self, videos: List[Dict], min_duration: int,
                                 max_duration: int) -> List[Dict]:
        """Filter videos based on duration criteria.

        Resolution/orientation filtering is already handled by the Pexels API
        via the 'orientation' query parameter, so we only filter by duration here.
        """
        filtered_videos = []

        for video in videos:
            duration = video.get('duration', 0)
            if duration < min_duration or duration > max_duration:
                continue
            filtered_videos.append(video)

        return filtered_videos
    
    def _get_best_video_file(self, video: Dict, size: str) -> Optional[Dict]:
        """Get the best video file from a video based on criteria."""
        size_priority = {
            "large": ["hd", "sd"],
            "medium": ["sd", "hd"],
            "small": ["sd"]
        }
        quality_order = size_priority.get(size, ["hd", "sd"])

        # Try preferred quality first
        for quality in quality_order:
            for video_file in video.get('video_files', []):
                file_quality = video_file.get('quality', '') or ''
                if quality in file_quality.lower() and video_file.get('link'):
                    return video_file

        # Fallback: return highest-resolution file available
        best = None
        best_pixels = 0
        for video_file in video.get('video_files', []):
            if not video_file.get('link'):
                continue
            pixels = video_file.get('width', 0) * video_file.get('height', 0)
            if pixels > best_pixels:
                best = video_file
                best_pixels = pixels
        return best
    
    async def search_videos(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for videos on Pexels based on query and filters.
        
        Args:
            params: Dictionary containing:
                - query: Search query string
                - per_page: Number of results per page (1-80)
                - min_duration: Minimum video duration in seconds
                - max_duration: Maximum video duration in seconds
                - orientation: Video orientation ('landscape', 'portrait', 'square')
                - size: Video size preference ('large', 'medium', 'small')
        
        Returns:
            Dictionary containing search results and metadata
        """
        if not self.api_key:
            logger.error("Pexels API key not configured. Please set PEXELS_API_KEY or PEXELS_KEY environment variable.")
            raise ValueError("Pexels API key not configured. Please check your environment variables.")
        
        query = params.get('query')
        per_page = min(params.get('per_page', 15), 80)  # Pexels max is 80
        min_duration = params.get('min_duration', 5)
        max_duration = params.get('max_duration', 60)
        orientation = params.get('orientation', 'landscape')
        size = params.get('size', 'large')
        
        if not query:
            raise ValueError("Search query is required")
        
        # Make request to Pexels API
        url = f"{self.base_url}/search"
        headers = self._get_headers()
        
        request_params = {
            "query": query,
            "orientation": self._map_orientation(orientation),
            "per_page": per_page
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=request_params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response.raise_for_status()
                    data = await response.json()
            
            # Filter videos based on criteria
            videos = data.get('videos', [])
            filtered_videos = self._filter_videos_by_criteria(
                videos, min_duration, max_duration
            )
            
            # Process videos and extract best file for each
            processed_videos = []
            for video in filtered_videos:
                video_file = self._get_best_video_file(video, size)
                if video_file:
                    # Extract thumbnail image from Pexels API
                    # Pexels returns 'image' as a direct preview photo URL
                    image_url = video.get('image')
                    
                    processed_video = {
                        "id": video.get('id'),
                        "url": video.get('url'),
                        "download_url": video_file.get('link'),
                        "image": image_url,  # Add thumbnail image for preview
                        "duration": video.get('duration'),
                        "width": video_file.get('width'),
                        "height": video_file.get('height'),
                        "file_size": video_file.get('file_size'),
                        "quality": video_file.get('quality', 'unknown'),
                        "file_type": video_file.get('file_type', 'mp4'),
                        "tags": video.get('tags', []),
                        "user": {
                            "name": video.get('user', {}).get('name', 'Pexels User')
                        }
                    }
                    processed_videos.append(processed_video)
            
            # Sort by duration preference (closer to 15 seconds is better for shorts)
            target_duration = 15
            processed_videos.sort(key=lambda x: abs(x['duration'] - target_duration))
            
            return {
                "videos": processed_videos,
                "total_results": data.get('total_results', len(processed_videos)),
                "page": data.get('page', 1),
                "per_page": data.get('per_page', per_page),
                "query_used": query
            }
            
        except aiohttp.ClientError as e:
            logger.error(f"Pexels API request failed: {e}")
            raise ValueError(f"Failed to search videos: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in video search: {e}")
            raise ValueError(f"Video search failed: {str(e)}")
    
    async def get_best_video(self, query: str, orientation: str = "landscape",
                           used_urls: Optional[List[str]] = None) -> Optional[str]:
        """
        Get the best video URL for a given query, avoiding previously used videos.
        
        Args:
            query: Search query
            orientation: Video orientation
            used_urls: List of previously used video URLs to avoid
        
        Returns:
            Best video download URL or None if not found
        """
        if used_urls is None:
            used_urls = []
        
        params = {
            "query": query,
            "per_page": 20,
            "min_duration": 5,
            "max_duration": 60,
            "orientation": orientation,
            "size": "large"
        }
        
        try:
            result = await self.search_videos(params)
            videos = result.get('videos', [])
            
            # Find first video not in used_urls
            for video in videos:
                download_url = video.get('download_url')
                if download_url and download_url not in used_urls:
                    return download_url
            
            logger.warning(f"No suitable video found for query: {query}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get best video for query '{query}': {e}")
            return None


# Create a singleton instance
pexels_service = PexelsVideoService()