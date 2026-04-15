import logging
from typing import Dict, Any, List, Optional
from app.services.ai.media_generation_strategy import MediaGenerationStrategy
from app.services.media.pexels_image_service import pexels_image_service
from app.services.media.pixabay_image_service import pixabay_image_service
from app.services.image.image_to_video import image_to_video_service
from app.services.research.news_research_service import news_research_service

logger = logging.getLogger(__name__)


class StockImageStrategy(MediaGenerationStrategy):
    """Strategy for generating video segments using stock images with motion effects."""
    
    def get_strategy_name(self) -> str:
        return "Stock Image Strategy (Pexels/Pixabay Images + Motion)"
    
    async def generate_media_segments(
        self, 
        video_queries: List[Dict], 
        orientation: str,
        params: Dict[str, Any]
    ) -> List[Optional[Dict[str, Any]]]:
        """Generate video segments using stock images with motion effects."""
        
        footage_provider = params.get('footage_provider', 'pexels')
        footage_quality = params.get('footage_quality', 'high')
        script_type = params.get('script_type', 'facts')
        motion_params = params.get('motion_params', {})
        use_ai_fallback = params.get('use_ai_image_fallback', True)
        
        logger.info(f"Generating stock images with motion using provider: {footage_provider}, effect: {motion_params.get('effect_type', 'ken_burns')}")
        
        # Check if stock image services are available
        pexels_available = pexels_image_service.is_available()
        pixabay_available = pixabay_image_service.is_available()
        
        if not pexels_available and not pixabay_available:
            logger.warning("No stock image API keys configured, falling back to AI image generation immediately")
            # Import here to avoid circular imports
            from app.services.ai.strategies.ai_image_strategy import AIImageStrategy
            
            ai_strategy = AIImageStrategy()
            return await ai_strategy.generate_media_segments(
                video_queries=video_queries,
                orientation=orientation,
                params={
                    'image_provider': params.get('image_provider', 'together'),
                    'motion_params': motion_params
                }
            )
        
        background_videos: List[Optional[Dict[str, Any]]] = []
        used_urls: List[str] = []
        
        for i, query_data in enumerate(video_queries):
            query = query_data['query']
            
            # Enhance query for news content
            enhanced_query = self._enhance_video_query_for_news(query, script_type)
            
            try:
                video_url = None
                
                if footage_provider == "pixabay":
                    video_url = await self._get_pixabay_image_to_video(
                        enhanced_query,
                        orientation,
                        query_data['duration'],
                        footage_quality,
                        used_urls,
                        motion_params.get('effect_type', 'ken_burns'),
                        motion_params.get('zoom_speed', 10.0),
                        motion_params.get('pan_direction', 'right'),
                        motion_params.get('ken_burns_keypoints')
                    )
                else:  # Default to pexels
                    video_url = await self._get_pexels_image_to_video(
                        enhanced_query,
                        orientation,
                        query_data['duration'],
                        footage_quality,
                        used_urls,
                        motion_params.get('effect_type', 'ken_burns'),
                        motion_params.get('zoom_speed', 10.0),
                        motion_params.get('pan_direction', 'right'),
                        motion_params.get('ken_burns_keypoints')
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
                    logger.warning(f"No image found for query: {query}, trying fallback")
                    fallback_video = await self._get_fallback_video(
                        enhanced_query,
                        orientation,
                        used_urls,
                        footage_provider,
                        query_data,
                        "image",
                        use_ai_fallback,
                        motion_params
                    )
                    if fallback_video:
                        background_videos.append(fallback_video)
                        used_urls.append(fallback_video['download_url'])
                    else:
                        logger.warning(f"No fallback image found for query: {query}")
                        background_videos.append(None)
                    
            except Exception as e:
                logger.error(f"Error finding image for query '{query}': {e}")
                # Try fallback search even on exceptions
                try:
                    fallback_video = await self._get_fallback_video(
                        enhanced_query,
                        orientation,
                        used_urls,
                        footage_provider,
                        query_data,
                        "image",
                        use_ai_fallback,
                        motion_params
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
    
    async def _get_pexels_image_to_video(
        self,
        query: str,
        orientation: str,
        duration: float,
        quality: str,
        used_urls: List[str],
        effect_type: str = 'ken_burns',
        zoom_speed: float = 10.0,
        pan_direction: str = 'right',
        ken_burns_keypoints: Optional[List] = None
    ) -> Optional[str]:
        """Get image from Pexels and convert to video with motion effects."""
        try:
            # Use the same approach as the dashboard
            params = {
                'query': query,
                'per_page': 20,
                'orientation': orientation,
                'quality': quality,
                'color': None,
                'size': None
            }

            result = await pexels_image_service.search_images(params)
            images = result.get('images', [])

            # Find first image not in used_urls
            image_url = None
            for img in images:
                img_url = img.get('download_url') or img.get('url', '')
                if img_url and img_url not in used_urls:
                    image_url = img_url
                    break

            if not image_url:
                logger.warning(f"No Pexels image found for query: {query}")
                return None

            # Convert image to video with motion effects
            video_params = {
                'image_url': image_url,
                'video_length': duration,
                'zoom_speed': zoom_speed,
                'frame_rate': 30,
                'should_add_captions': False,  # Captions will be added later in the pipeline
                'match_length': 'video',
                'effect_type': effect_type,
                'pan_direction': pan_direction,
                'ken_burns_keypoints': ken_burns_keypoints,
            }

            video_result = await image_to_video_service.image_to_video(video_params)
            
            if video_result and (video_result.get('video_url') or video_result.get('final_video_url')):
                video_url = video_result.get('video_url') or video_result.get('final_video_url')
                logger.info(f"Successfully converted Pexels image to video for query: {query}")
                return video_url
            else:
                logger.error(f"Image-to-video conversion failed: no video URL returned")
                return None
                
        except Exception as e:
            logger.error(f"Error processing Pexels image for query '{query}': {e}")
            return None
    
    async def _get_pixabay_image_to_video(
        self,
        query: str,
        orientation: str,
        duration: float,
        quality: str,
        used_urls: List[str],
        effect_type: str = 'ken_burns',
        zoom_speed: float = 10.0,
        pan_direction: str = 'right',
        ken_burns_keypoints: Optional[List] = None
    ) -> Optional[str]:
        """Get image from Pixabay and convert to video with motion effects."""
        try:
            # Use the same approach as the dashboard
            images_data = await pixabay_image_service.search_images(
                query=query,
                orientation=orientation,
                quality=quality,
                per_page=20,
                color=None,
                size=None
            )

            # Find first image not in used_urls
            image_url = None
            for img in images_data:
                img_url = img.get('download_url') or img.get('url', '')
                if img_url and img_url not in used_urls:
                    image_url = img_url
                    break

            if not image_url:
                logger.warning(f"No Pixabay image found for query: {query}")
                return None

            # Convert image to video with motion effects
            video_params = {
                'image_url': image_url,
                'video_length': duration,
                'zoom_speed': zoom_speed,
                'frame_rate': 30,
                'should_add_captions': False,  # Captions will be added later in the pipeline
                'match_length': 'video',
                'effect_type': effect_type,
                'pan_direction': pan_direction,
                'ken_burns_keypoints': ken_burns_keypoints,
            }

            video_result = await image_to_video_service.image_to_video(video_params)
            
            if video_result and (video_result.get('video_url') or video_result.get('final_video_url')):
                video_url = video_result.get('video_url') or video_result.get('final_video_url')
                logger.info(f"Successfully converted Pixabay image to video for query: {query}")
                return video_url
            else:
                logger.error(f"Image-to-video conversion failed: no video URL returned")
                return None
                
        except Exception as e:
            logger.error(f"Error processing Pixabay image for query '{query}': {e}")
            return None
    
    async def _get_fallback_video(
        self,
        query: str,
        orientation: str,
        used_urls: List[str],
        original_provider: str,
        query_data: Dict[str, Any],
        media_type: str = "image",
        use_ai_fallback: bool = True,
        motion_params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get fallback video when primary provider fails."""
        # Try different fallback strategies based on original provider
        fallback_providers = []
        
        if original_provider == "pixabay":
            fallback_providers = ["pexels"]
        else:  # pexels
            fallback_providers = ["pixabay"]
        
        # First try other stock providers
        for provider in fallback_providers:
            try:
                fallback_url = None
                fallback_query = "nature landscape abstract"  # Generic fallback query
                
                if provider == "pexels":
                    fallback_url = await self._get_pexels_image_to_video(
                        fallback_query,
                        orientation,
                        query_data['duration'],
                        "high",
                        used_urls,
                        motion_params.get('effect_type', 'ken_burns') if motion_params else 'ken_burns',
                        motion_params.get('zoom_speed', 10.0) if motion_params else 10.0,
                        motion_params.get('pan_direction', 'right') if motion_params else 'right',
                        motion_params.get('ken_burns_keypoints') if motion_params else None
                    )
                elif provider == "pixabay":
                    fallback_url = await self._get_pixabay_image_to_video(
                        fallback_query,
                        orientation,
                        query_data['duration'],
                        "high",
                        used_urls,
                        motion_params.get('effect_type', 'ken_burns') if motion_params else 'ken_burns',
                        motion_params.get('zoom_speed', 10.0) if motion_params else 10.0,
                        motion_params.get('pan_direction', 'right') if motion_params else 'right',
                        motion_params.get('ken_burns_keypoints') if motion_params else None
                    )
                
                if fallback_url:
                    logger.info(f"Found fallback {media_type} using {provider} for query: '{query}'")
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
        
        # If all stock providers failed and we're looking for images, try AI generation as final fallback
        if media_type == "image" and use_ai_fallback and original_provider != "ai_generated":
            logger.info(f"Stock image providers failed for '{query}', trying AI image generation as final fallback")
            try:
                # Import here to avoid circular imports
                from app.services.ai.strategies.ai_image_strategy import AIImageStrategy
                
                ai_strategy = AIImageStrategy()
                ai_fallback_results = await ai_strategy.generate_media_segments(
                    video_queries=[query_data],
                    orientation=orientation,
                    params={
                        'image_provider': 'together',
                        'motion_params': motion_params or {}
                    }
                )
                
                if ai_fallback_results and ai_fallback_results[0]:
                    fallback_result = ai_fallback_results[0]
                    fallback_result['query'] = f"{query} (AI fallback)"
                    fallback_result['provider'] = f"{original_provider}_ai_fallback"
                    logger.info(f"Successfully generated AI fallback image for query: '{query}'")
                    return fallback_result
                    
            except Exception as e:
                logger.error(f"AI image fallback also failed for query '{query}': {e}")
        
        return None