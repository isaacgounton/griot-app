"""
Multi-provider video search service that combines Pexels and Pixabay.
"""
import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from .pexels_service import PexelsVideoService
from .pixabay_service import pixabay_service

logger = logging.getLogger(__name__)


class MultiVideoSearchService:
    """Unified video search service using multiple providers."""
    
    def __init__(self):
        self.pexels_service = PexelsVideoService()
        self.pixabay_service = pixabay_service
        
        # Check which services are available
        self.pexels_available = bool(self.pexels_service.api_key)
        self.pixabay_available = self.pixabay_service.is_available()
        
        if not self.pexels_available and not self.pixabay_available:
            logger.warning("No video search APIs available. Please set PEXELS_API_KEY or PIXABAY_API_KEY.")
        else:
            available_services = []
            if self.pexels_available:
                available_services.append("Pexels")
            if self.pixabay_available:
                available_services.append("Pixabay")
            logger.info(f"Video search services available: {', '.join(available_services)}")
    
    async def search_videos(
        self,
        query: str,
        orientation: str = "landscape",
        max_results: int = 10,
        min_duration: int = 3,
        max_duration: int = 300,
        prefer_provider: str = "auto"
    ) -> List[Dict[str, Any]]:
        """
        Search for videos across multiple providers.
        
        Args:
            query: Search query
            orientation: Video orientation ("landscape", "portrait", "square")
            max_results: Maximum number of results
            min_duration: Minimum duration in seconds
            max_duration: Maximum duration in seconds
            prefer_provider: Preferred provider ("auto", "pexels", "pixabay")
            
        Returns:
            Combined list of videos from all available providers
        """
        all_videos = []
        
        # Determine search strategy
        if prefer_provider == "pexels" and self.pexels_available:
            videos = await self._search_pexels(query, orientation, max_results, min_duration, max_duration)
            all_videos.extend(videos)
        elif prefer_provider == "pixabay" and self.pixabay_available:
            videos = await self._search_pixabay(query, orientation, max_results, min_duration)
            all_videos.extend(videos)
        else:
            # Auto mode: search both providers in parallel
            tasks = []
            
            if self.pexels_available:
                tasks.append(self._search_pexels(query, orientation, max_results // 2 + 1, min_duration, max_duration))
            
            if self.pixabay_available:
                tasks.append(self._search_pixabay(query, orientation, max_results // 2 + 1, min_duration))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, list):
                        all_videos.extend(result)
                    elif isinstance(result, Exception):
                        logger.warning(f"Video search provider failed: {result}")
        
        # Sort by relevance score and remove duplicates
        unique_videos = self._deduplicate_videos(all_videos)
        sorted_videos = self._sort_videos_by_relevance(unique_videos, query, orientation)
        
        logger.info(f"Found {len(sorted_videos)} unique videos from {len(all_videos)} total results")
        return sorted_videos[:max_results]
    
    async def _search_pexels(
        self,
        query: str,
        orientation: str,
        max_results: int,
        min_duration: int,
        max_duration: int
    ) -> List[Dict[str, Any]]:
        """Search Pexels for videos."""
        try:
            # Prepare params for Pexels service (it expects a dict)
            pexels_params = {
                'query': query,
                'orientation': orientation,
                'per_page': max_results,
                'min_duration': min_duration,
                'max_duration': max_duration
            }
            
            # Call Pexels service (it's actually async)
            pexels_result = await self.pexels_service.search_videos(pexels_params)
            videos = pexels_result.get('videos', [])
            
            # Standardize format
            standardized_videos = []
            for video in videos:
                standardized_video = self._standardize_pexels_video(video)
                standardized_videos.append(standardized_video)
            
            return standardized_videos
            
        except Exception as e:
            logger.error(f"Pexels search failed: {e}")
            return []
    
    async def _search_pixabay(
        self,
        query: str,
        orientation: str,
        max_results: int,
        min_duration: int
    ) -> List[Dict[str, Any]]:
        """Search Pixabay for videos."""
        try:
            videos = await self.pixabay_service.search_by_orientation(
                query=query,
                target_orientation=orientation,
                max_results=max_results
            )
            
            # Filter by duration and standardize format
            filtered_videos = []
            for video in videos:
                if video.get('duration', 0) >= min_duration:
                    standardized_video = self._standardize_pixabay_video(video)
                    filtered_videos.append(standardized_video)
            
            return filtered_videos
            
        except Exception as e:
            logger.error(f"Pixabay search failed: {e}")
            return []
    
    def _standardize_pexels_video(self, video: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize Pexels video format."""
        return {
            'id': f"pexels_{video.get('id', '')}",
            'url': video.get('video_files', [{}])[0].get('link', ''),
            'thumbnail': video.get('image', ''),
            'duration': video.get('duration', 0),
            'width': video.get('width', 0),
            'height': video.get('height', 0),
            'aspect_ratio': video.get('aspect_ratio', 16/9),
            'orientation': video.get('orientation', 'landscape'),
            'tags': ', '.join(video.get('tags', [])) if video.get('tags') else '',
            'user': video.get('user', {}).get('name', ''),
            'source': 'pexels',
            'quality_score': self._calculate_pexels_quality_score(video),
            'relevance_score': 0  # Will be calculated later
        }
    
    def _standardize_pixabay_video(self, video: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize Pixabay video format."""
        return {
            'id': f"pixabay_{video.get('id', '')}",
            'url': video.get('url', ''),
            'thumbnail': video.get('thumbnail', ''),
            'duration': video.get('duration', 0),
            'width': video.get('width', 0),
            'height': video.get('height', 0),
            'aspect_ratio': video.get('aspect_ratio', 16/9),
            'orientation': self._get_orientation_from_aspect_ratio(video.get('aspect_ratio', 16/9)),
            'tags': video.get('tags', ''),
            'user': video.get('user', ''),
            'source': 'pixabay',
            'quality_score': self._calculate_pixabay_quality_score(video),
            'relevance_score': 0  # Will be calculated later
        }
    
    def _calculate_pexels_quality_score(self, video: Dict[str, Any]) -> float:
        """Calculate quality score for Pexels video."""
        score = 0.5  # Base score
        
        # Resolution bonus
        width = video.get('width', 0)
        height = video.get('height', 0)
        if width >= 1920 and height >= 1080:
            score += 0.3
        elif width >= 1280 and height >= 720:
            score += 0.2
        
        # Duration bonus (prefer 3-30 second clips)
        duration = video.get('duration', 0)
        if 3 <= duration <= 30:
            score += 0.2
        elif duration > 30:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_pixabay_quality_score(self, video: Dict[str, Any]) -> float:
        """Calculate quality score for Pixabay video."""
        score = 0.5  # Base score
        
        # Resolution bonus
        width = video.get('width', 0)
        height = video.get('height', 0)
        if width >= 1920 and height >= 1080:
            score += 0.2
        elif width >= 1280 and height >= 720:
            score += 0.1
        
        # Popularity metrics
        views = video.get('views', 0)
        downloads = video.get('downloads', 0)
        likes = video.get('likes', 0)
        
        if views > 1000:
            score += 0.1
        if downloads > 100:
            score += 0.1
        if likes > 50:
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_orientation_from_aspect_ratio(self, aspect_ratio: float) -> str:
        """Get orientation from aspect ratio."""
        if aspect_ratio > 1.2:
            return "landscape"
        elif aspect_ratio < 0.8:
            return "portrait"
        else:
            return "square"
    
    def _deduplicate_videos(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate videos based on URL or similar characteristics."""
        seen_urls = set()
        unique_videos = []
        
        for video in videos:
            url = video.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_videos.append(video)
        
        return unique_videos
    
    def _sort_videos_by_relevance(
        self,
        videos: List[Dict[str, Any]],
        query: str,
        target_orientation: str
    ) -> List[Dict[str, Any]]:
        """Sort videos by relevance score."""
        query_words = query.lower().split()
        
        for video in videos:
            relevance_score = 0
            
            # Tag relevance
            tags = video.get('tags', '').lower()
            for word in query_words:
                if word in tags:
                    relevance_score += 0.3
            
            # Orientation match
            if video.get('orientation') == target_orientation:
                relevance_score += 0.3
            
            # Quality score
            relevance_score += video.get('quality_score', 0) * 0.4
            
            video['relevance_score'] = relevance_score
        
        # Sort by relevance score (descending)
        return sorted(videos, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    def is_available(self) -> bool:
        """Check if any video search service is available."""
        return self.pexels_available or self.pixabay_available
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        providers = []
        if self.pexels_available:
            providers.append("pexels")
        if self.pixabay_available:
            providers.append("pixabay")
        return providers


# Singleton instance
multi_video_search_service = MultiVideoSearchService()