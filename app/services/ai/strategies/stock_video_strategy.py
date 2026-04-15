import logging
from typing import Dict, Any, List, Optional
from app.services.ai.media_generation_strategy import MediaGenerationStrategy
from app.services.media.pexels_service import pexels_service
from app.services.media.pixabay_service import pixabay_service
from app.services.research.news_research_service import news_research_service

logger = logging.getLogger(__name__)


class StockVideoStrategy(MediaGenerationStrategy):
    """Strategy for generating video segments using stock videos from Pexels/Pixabay."""
    
    def get_strategy_name(self) -> str:
        return "Stock Video Strategy (Pexels/Pixabay)"
    
    async def generate_media_segments(
        self, 
        video_queries: List[Dict], 
        orientation: str,
        params: Dict[str, Any]
    ) -> List[Optional[Dict[str, Any]]]:
        """Generate video segments using stock videos."""
        
        footage_provider = params.get('footage_provider', 'pexels')
        footage_quality = params.get('footage_quality', 'high')
        script_type = params.get('script_type', 'facts')
        
        logger.info(f"Generating stock videos using provider: {footage_provider}")
        
        background_videos: List[Optional[Dict[str, Any]]] = []
        used_urls: List[str] = []
        
        for i, query_data in enumerate(video_queries):
            query = query_data['query']
            
            # Enhance query for news content
            enhanced_query = self._enhance_video_query_for_news(query, script_type)
            
            try:
                video_url = None
                
                if footage_provider == "pixabay":
                    video_url = await self._get_pixabay_video(
                        enhanced_query,
                        orientation,
                        used_urls
                    )
                else:  # Default to pexels
                    video_url = await pexels_service.get_best_video(
                        query=enhanced_query,
                        orientation=orientation,
                        used_urls=used_urls
                    )
                
                if video_url:
                    background_videos.append({
                        'download_url': video_url,
                        'start_time': query_data['start_time'],
                        'end_time': query_data['end_time'],
                        'duration': query_data['duration'],
                        'query': enhanced_query,
                        'provider': footage_provider
                    })
                    used_urls.append(video_url)
                else:
                    # Try fallback search with different provider
                    logger.warning(f"No video found for query: {query}, trying fallback")
                    fallback_video = await self._get_fallback_video(
                        enhanced_query,
                        orientation,
                        used_urls,
                        footage_provider,
                        query_data
                    )
                    if fallback_video:
                        background_videos.append(fallback_video)
                        used_urls.append(fallback_video['download_url'])
                    else:
                        logger.warning(f"No fallback video found for query: {query}")
                        background_videos.append(None)
                    
            except Exception as e:
                logger.error(f"Error finding video for query '{query}': {e}")
                # Try fallback search even on exceptions
                try:
                    fallback_video = await self._get_fallback_video(
                        enhanced_query,
                        orientation,
                        used_urls,
                        footage_provider,
                        query_data
                    )
                    if fallback_video:
                        background_videos.append(fallback_video)
                        used_urls.append(fallback_video['download_url'])
                    else:
                        background_videos.append(None)
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed for query '{query}': {fallback_error}")
                    background_videos.append(None)
        
        return background_videos
    
    def _enhance_video_query_for_news(self, query: str, script_type: str) -> str:
        """Enhance video search query with news-specific keywords if applicable."""
        if script_type == "daily_news":
            # Add news-specific keywords to improve video search
            news_keywords = news_research_service.get_news_keywords(query)
            # Use the first few keywords to enhance the query
            enhanced_query = f"{query} {' '.join(news_keywords[:3])}"
            return enhanced_query
        return query
    
    async def _get_pixabay_video(
        self,
        query: str,
        orientation: str,
        used_urls: List[str]
    ) -> Optional[str]:
        """Get video from Pixabay service."""
        try:
            return await pixabay_service.get_best_video(
                query=query,
                orientation=orientation,
                used_urls=used_urls
            )
        except Exception as e:
            logger.error(f"Error searching Pixabay for query '{query}': {e}")
            return None
    
    async def _get_fallback_video(
        self,
        query: str,
        orientation: str,
        used_urls: List[str],
        original_provider: str,
        query_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get fallback video when primary provider fails."""
        # Try different fallback strategies based on original provider
        fallback_providers = []
        
        if original_provider == "pixabay":
            fallback_providers = ["pexels"]
        else:  # pexels
            fallback_providers = ["pixabay"]
        
        for provider in fallback_providers:
            try:
                fallback_url = None
                fallback_query = "nature landscape abstract"  # Generic fallback query
                
                if provider == "pexels":
                    fallback_url = await pexels_service.get_best_video(
                        query=fallback_query,
                        orientation=orientation,
                        used_urls=used_urls
                    )
                elif provider == "pixabay":
                    fallback_url = await self._get_pixabay_video(
                        fallback_query,
                        orientation,
                        used_urls
                    )
                
                if fallback_url:
                    logger.info(f"Found fallback video using {provider} for query: '{query}'")
                    return {
                        'download_url': fallback_url,
                        'start_time': query_data['start_time'],
                        'end_time': query_data['end_time'],
                        'duration': query_data['duration'],
                        'query': f"{query} (fallback: {provider})",
                        'provider': f"{original_provider}_fallback_{provider}"
                    }
                    
            except Exception as e:
                logger.error(f"Fallback provider {provider} failed: {e}")
                continue
        
        return None