"""
Pixabay image search service for finding stock photos.
"""
import os
import logging
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)


class PixabayImageService:
    """Service for searching stock images on Pixabay."""
    
    def __init__(self):
        self.base_url = "https://pixabay.com/api/"
        self._api_key = None
        self._api_key_checked = False
    
    @property
    def api_key(self):
        """Lazy load the API key to ensure .env is loaded first."""
        if not self._api_key_checked:
            self._api_key = os.getenv('PIXABAY_API_KEY')
            self._api_key_checked = True
            if not self._api_key:
                logger.warning("PIXABAY_API_KEY not found. Pixabay image search will be unavailable.")
        return self._api_key
    
    def _map_orientation(self, orientation: str) -> str:
        """Map orientation from our format to Pixabay format."""
        orientation_map = {
            'landscape': 'horizontal',
            'portrait': 'vertical',
            'square': 'all'  # Pixabay doesn't have square, use all
        }
        return orientation_map.get(orientation, 'horizontal')
    
    def _get_resolution_filter(self, orientation: str, quality: str = "high") -> tuple:
        """Get minimum resolution requirements based on orientation and quality."""
        if quality == "ultra":
            multiplier = 2.0
        elif quality == "high":
            multiplier = 1.0
        else:  # standard
            multiplier = 0.75
            
        if orientation == "landscape":
            base_width, base_height = 1920, 1080
        elif orientation == "portrait":
            base_width, base_height = 1080, 1920
        elif orientation == "square":
            base_width, base_height = 1080, 1080
        else:
            base_width, base_height = 1920, 1080  # default to landscape
            
        min_width = int(base_width * multiplier)
        min_height = int(base_height * multiplier)
        target_ratio = base_width / base_height
        
        return (min_width, min_height, target_ratio)
    
    def _filter_images_by_criteria(self, images: List[Dict], orientation: str, quality: str) -> List[Dict]:
        """Filter images based on resolution and orientation criteria."""
        logger.info(f"Filtering {len(images)} Pixabay images by orientation: {orientation}, quality: {quality}")
        filtered_images = []
        
        for image in images:
            # Use standardized field names since we're filtering after processing
            width = image.get('width', 0)
            height = image.get('height', 0)
            
            # Very lenient minimum resolution check - accept almost anything decent
            if width < 300 or height < 200:  # Very basic minimum resolution
                logger.debug(f"Pixabay image {image.get('id')} filtered out due to low resolution: {width}x{height}")
                continue
            
            # Much more flexible aspect ratio filtering
            if height > 0:
                ratio = width / height
                
                if orientation == "landscape":
                    # Accept any image that's not clearly portrait
                    if ratio >= 0.8:  # Just needs to not be clearly portrait
                        filtered_images.append(image)
                    else:
                        logger.debug(f"Pixabay image {image.get('id')} filtered out: landscape ratio {ratio}")
                elif orientation == "portrait":
                    # Accept any image that's not clearly landscape
                    if ratio <= 1.2:  # Just needs to not be clearly landscape
                        filtered_images.append(image)
                    else:
                        logger.debug(f"Pixabay image {image.get('id')} filtered out: portrait ratio {ratio}")
                elif orientation == "square":
                    # Accept images close to square (very lenient)
                    if 0.4 <= ratio <= 2.5:  # Very wide range
                        filtered_images.append(image)
                    else:
                        logger.debug(f"Pixabay image {image.get('id')} filtered out: square ratio {ratio}")
                else:
                    # Default: accept all decent quality images
                    filtered_images.append(image)
            else:
                logger.debug(f"Pixabay image {image.get('id')} filtered out: height is 0")
        
        logger.info(f"Filtered down to {len(filtered_images)} Pixabay images")
        return filtered_images
    
    def _get_best_image_url(self, image: Dict, quality: str) -> Optional[str]:
        """Get the best image URL from Pixabay image based on quality preference."""
        # Pixabay provides different size URLs
        available_urls = {}
        for field in ['fullHDURL', 'largeImageURL', 'webformatURL', 'previewURL']:
            if image.get(field):
                available_urls[field] = image[field]
        
        logger.debug(f"Available URLs for image {image.get('id')}: {list(available_urls.keys())}")
        
        if quality == "ultra":
            # Try fullHD, then largeImageURL, then webformatURL
            for field in ['fullHDURL', 'largeImageURL', 'webformatURL', 'previewURL']:
                if image.get(field):
                    return image[field]
        elif quality == "high":
            # Try largeImageURL, then webformatURL, then fullHD
            for field in ['largeImageURL', 'webformatURL', 'fullHDURL', 'previewURL']:
                if image.get(field):
                    return image[field]
        else:  # standard
            # Try webformatURL, then previewURL, then largeImageURL
            for field in ['webformatURL', 'previewURL', 'largeImageURL', 'fullHDURL']:
                if image.get(field):
                    return image[field]
        
        # If no specific URL found, try any available URL
        if available_urls:
            return list(available_urls.values())[0]
        
        logger.warning(f"No suitable URL found for image {image.get('id')}")
        return None
    
    def _get_display_image_url(self, image: Dict) -> Optional[str]:
        """Get a medium-sized image URL for display purposes."""
        # Prefer medium size for display, fallback to other sizes
        for field in ['webformatURL', 'previewURL', 'largeImageURL', 'fullHDURL']:
            if image.get(field):
                return image[field]
        
        return None
    
    async def search_images(
        self,
        query: str,
        orientation: str = "landscape",
        image_type: str = "photo",
        quality: str = "high",
        per_page: int = 20,
        color: Optional[str] = None,
        size: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for images on Pixabay.
        
        Args:
            query: Search query
            orientation: Image orientation ("landscape", "portrait", "square")
            image_type: Type of image ("all", "photo", "illustration", "vector")
            quality: Quality preference ("standard", "high", "ultra")
            per_page: Number of results per page (3-200)
            color: Color filter ("grayscale", "transparent", "red", "orange", "yellow", "green", "turquoise", "blue", "lilac", "pink", "white", "gray", "black", "brown")
            size: Size filter ("large", "medium", "small")
            
        Returns:
            List of image dictionaries
        """
        if not self.api_key:
            logger.warning("Pixabay API key not available")
            return []
        
        try:
            params = {
                'key': self.api_key,
                'q': quote(query),
                'image_type': image_type,
                'orientation': self._map_orientation(orientation),
                'per_page': max(3, min(per_page, 200)),  # Pixabay requires minimum 3, max 200 per request
                'safesearch': 'true',
                'order': 'popular',
                'min_width': 640,  # Lower minimum requirements
                'min_height': 480
            }
            
            # Add optional filters
            if color:
                params['color'] = color
            
            logger.info(f"Pixabay search params: {params}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    logger.info(f"Pixabay API response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Pixabay API response: {data.get('totalHits', 0)} total hits, {len(data.get('hits', []))} returned")
                        
                        images = []
                        
                        for hit in data.get('hits', []):
                            # Get the best quality image URL
                            image_url = self._get_best_image_url(hit, quality)
                            display_url = self._get_display_image_url(hit)
                            
                            if not image_url:
                                logger.debug(f"No suitable URL found for image {hit.get('id')}")
                                continue
                            
                            image_info = {
                                'id': hit.get('id'),
                                'url': display_url or image_url,  # URL for displaying the image
                                'download_url': image_url,  # URL for downloading the full resolution image
                                'page_url': f"https://pixabay.com/en/photos/{hit.get('id')}/",  # Pixabay page URL
                                'width': hit.get('imageWidth', 0),
                                'height': hit.get('imageHeight', 0),
                                'tags': hit.get('tags', ''),
                                'user': hit.get('user', ''),
                                'photographer': hit.get('user', ''),  # For compatibility with Pexels format
                                'photographer_url': f"https://pixabay.com/users/{hit.get('user', '')}/",
                                'alt': hit.get('tags', '').replace(',', ' '),  # Use tags as alt text
                                'views': hit.get('views', 0),
                                'downloads': hit.get('downloads', 0),
                                'likes': hit.get('likes', 0),
                                'source': 'pixabay',
                                'preview_url': hit.get('previewURL', ''),
                                'web_format_url': hit.get('webformatURL', ''),
                                'large_image_url': hit.get('largeImageURL', ''),
                                'full_hd_url': hit.get('fullHDURL', ''),
                                'aspect_ratio': self._calculate_aspect_ratio(
                                    hit.get('imageWidth', 0),
                                    hit.get('imageHeight', 0)
                                ),
                                'type': hit.get('type', 'photo')
                            }
                            
                            images.append(image_info)
                        
                        # Filter by our criteria
                        filtered_images = self._filter_images_by_criteria(images, orientation, quality)
                        
                        # Sort by downloads and views (more popular first)
                        filtered_images.sort(key=lambda x: (x['downloads'] + x['views']), reverse=True)
                        
                        logger.info(f"Found {len(filtered_images)} images on Pixabay for query: {query}")
                        return filtered_images
                        
                    else:
                        error_text = await response.text()
                        logger.error(f"Pixabay API error {response.status}: {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error searching Pixabay images: {e}")
            return []
    
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
        quality: str = "high",
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for images filtered by target orientation.
        
        Args:
            query: Search query
            target_orientation: Desired orientation ("landscape", "portrait", "square")
            quality: Image quality preference
            max_results: Maximum number of results
            
        Returns:
            List of images matching the orientation
        """
        # Search with Pixabay orientation parameter
        all_images = await self.search_images(
            query=query,
            orientation=target_orientation,
            quality=quality,
            per_page=max_results * 2  # Get more to filter
        )
        
        # Additional filtering by aspect ratio for better matches
        filtered_images = []
        for image in all_images:
            image_orientation = self.get_orientation_from_aspect_ratio(image['aspect_ratio'])
            
            # Accept exact matches or close matches
            if target_orientation == "square":
                # For square, accept anything close to 1:1
                if 0.8 <= image['aspect_ratio'] <= 1.2:
                    filtered_images.append(image)
            elif target_orientation == image_orientation:
                filtered_images.append(image)
            
            if len(filtered_images) >= max_results:
                break
        
        return filtered_images[:max_results]
    
    async def get_best_image(self, query: str, orientation: str = "landscape", 
                           quality: str = "high", used_urls: Optional[List[str]] = None) -> Optional[str]:
        """
        Get the best image URL for a given query, avoiding previously used images.
        
        Args:
            query: Search query
            orientation: Image orientation
            quality: Image quality preference
            used_urls: List of previously used image URLs to avoid
        
        Returns:
            Best image download URL or None if not found
        """
        if used_urls is None:
            used_urls = []
        
        try:
            images = await self.search_images(
                query=query,
                orientation=orientation,
                quality=quality,
                per_page=20
            )
            
            # Find first image not in used_urls
            for image in images:
                download_url = image.get('download_url')
                if download_url and download_url not in used_urls:
                    return download_url
            
            logger.warning(f"No suitable image found for query: {query}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get best image for query '{query}': {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if Pixabay image service is available."""
        return bool(self.api_key)


# Singleton instance
pixabay_image_service = PixabayImageService()