"""
Pixabay video search service for finding stock footage.
"""
import os
import logging
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)


class PixabayVideoService:
    """Service for searching stock videos on Pixabay."""
    
    def __init__(self):
        self.api_key = os.getenv('PIXABAY_API_KEY')
        self.base_url = "https://pixabay.com/api/videos/"
        
        if not self.api_key:
            logger.warning("PIXABAY_API_KEY not found. Pixabay video search will be unavailable.")
    
    async def search_videos(
        self,
        query: str,
        orientation: str = "all",
        video_type: str = "film",
        duration: str = "all",
        per_page: int = 20,
        min_duration: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search for videos on Pixabay.
        
        Args:
            query: Search query
            orientation: Video orientation ("all", "horizontal", "vertical")
            video_type: Type of video ("all", "film", "animation")
            duration: Duration filter ("all", "short", "medium", "long")
            per_page: Number of results per page (3-200)
            min_duration: Minimum video duration in seconds
            
        Returns:
            List of video dictionaries
        """
        if not self.api_key:
            logger.warning("Pixabay API key not available")
            return []
        
        try:
            params = {
                'key': self.api_key,
                'q': quote(query),
                'video_type': video_type,
                'orientation': orientation,
                'duration': duration,
                'per_page': min(per_page, 200),  # Max 200 per request
                'safesearch': 'true',
                'order': 'popular'
            }
            
            # Map our orientation parameter to Pixabay's format
            orientation_map = {
                'landscape': 'horizontal',
                'portrait': 'vertical',
                'square': 'all'  # Pixabay doesn't have square, use all
            }
            params['orientation'] = orientation_map.get(orientation, orientation)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        videos = []
                        
                        for hit in data.get('hits', []):
                            # Get the best quality video URL
                            video_url = self._get_best_video_url(hit)
                            if not video_url:
                                continue
                            
                            # Filter by minimum duration
                            if hit.get('duration', 0) < min_duration:
                                continue
                            
                            # Build a real thumbnail URL from picture_id
                            # Pixabay video thumbnails: https://i.vimeocdn.com/video/{picture_id}_295x166.jpg
                            pic_id = hit.get('picture_id', '')
                            thumbnail_url = f"https://i.vimeocdn.com/video/{pic_id}_295x166.jpg" if pic_id else ''

                            video_info = {
                                'id': hit.get('id'),
                                'url': video_url,
                                'duration': hit.get('duration', 0),
                                'width': hit.get('videos', {}).get('large', {}).get('width', 0),
                                'height': hit.get('videos', {}).get('large', {}).get('height', 0),
                                'tags': hit.get('tags', ''),
                                'user': hit.get('user', ''),
                                'views': hit.get('views', 0),
                                'downloads': hit.get('downloads', 0),
                                'likes': hit.get('likes', 0),
                                'source': 'pixabay',
                                'thumbnail': thumbnail_url,
                                'aspect_ratio': self._calculate_aspect_ratio(
                                    hit.get('videos', {}).get('large', {}).get('width', 0),
                                    hit.get('videos', {}).get('large', {}).get('height', 0)
                                )
                            }
                            
                            videos.append(video_info)
                        
                        logger.info(f"Found {len(videos)} videos on Pixabay for query: {query}")
                        return videos
                        
                    else:
                        error_text = await response.text()
                        logger.error(f"Pixabay API error {response.status}: {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error searching Pixabay videos: {e}")
            return []
    
    def _get_best_video_url(self, hit: Dict[str, Any]) -> Optional[str]:
        """Get the best quality video URL from Pixabay hit."""
        videos = hit.get('videos', {})
        
        # Prefer large, then medium, then small, then tiny
        for quality in ['large', 'medium', 'small', 'tiny']:
            if quality in videos and videos[quality].get('url'):
                return videos[quality]['url']
        
        return None
    
    def _calculate_aspect_ratio(self, width: int, height: int) -> float:
        """Calculate aspect ratio from width and height."""
        if height == 0:
            return 16/9  # Default to 16:9
        return width / height
    
    def get_orientation_from_aspect_ratio(self, aspect_ratio: float) -> str:
        """Determine orientation from aspect ratio."""
        if aspect_ratio > 1.2:
            return "landscape"
        elif aspect_ratio < 0.8:
            return "portrait"
        else:
            return "square"
    
    async def search_by_orientation(
        self,
        query: str,
        target_orientation: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for videos filtered by target orientation.
        
        Args:
            query: Search query
            target_orientation: Desired orientation ("landscape", "portrait", "square")
            max_results: Maximum number of results
            
        Returns:
            List of videos matching the orientation
        """
        # Search with Pixabay orientation parameter
        all_videos = await self.search_videos(
            query=query,
            orientation=target_orientation,
            per_page=max_results * 2  # Get more to filter
        )
        
        # Additional filtering by aspect ratio for better matches
        filtered_videos = []
        for video in all_videos:
            video_orientation = self.get_orientation_from_aspect_ratio(video['aspect_ratio'])
            
            # Accept exact matches or close matches
            if target_orientation == "square":
                # For square, accept anything close to 1:1
                if 0.8 <= video['aspect_ratio'] <= 1.2:
                    filtered_videos.append(video)
            elif target_orientation == video_orientation:
                filtered_videos.append(video)
            
            if len(filtered_videos) >= max_results:
                break
        
        return filtered_videos[:max_results]
    
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
        
        try:
            # Search for videos with the specified orientation
            videos = await self.search_by_orientation(
                query=query,
                target_orientation=orientation,
                max_results=20
            )
            
            # Filter out previously used URLs and find the best video
            for video in videos:
                video_url = video.get('url')
                if video_url and video_url not in used_urls:
                    logger.info(f"Found Pixabay video for query '{query}': {video_url}")
                    return video_url
            
            logger.warning(f"No Pixabay video found for query: {query}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting best video from Pixabay for query '{query}': {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if Pixabay service is available."""
        return bool(self.api_key)


# Singleton instance
pixabay_service = PixabayVideoService()