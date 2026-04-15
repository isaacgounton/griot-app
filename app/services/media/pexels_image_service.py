import os
import aiohttp
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class PexelsImageService:
    """Service for searching and retrieving images from Pexels API."""
    
    def __init__(self):
        self.base_url = "https://api.pexels.com/v1"
        self._api_key = None
        self._api_key_checked = False
        
    @property
    def api_key(self):
        """Lazy load the API key to ensure .env is loaded first."""
        if not self._api_key_checked:
            self._api_key = os.getenv('PEXELS_API_KEY')
            self._api_key_checked = True
            if not self._api_key:
                logger.warning("PEXELS_API_KEY not found in environment variables")
        return self._api_key
    
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
        logger.info(f"Filtering {len(images)} Pexels images for orientation: {orientation}, quality: {quality}")
        filtered_images = []
        
        for image in images:
            width = image.get('width', 0)
            height = image.get('height', 0)
            
            # Very lenient minimum resolution check - accept almost anything decent
            if width < 400 or height < 300:  # Very basic minimum resolution
                logger.debug(f"Pexels image {image.get('id')} filtered out due to low resolution: {width}x{height}")
                continue
            
            # Much more flexible aspect ratio filtering
            if height > 0:
                ratio = width / height
                
                if orientation == "landscape":
                    # Accept any image that's not clearly portrait
                    if ratio >= 0.9:  # Just needs to not be clearly portrait
                        filtered_images.append(image)
                    else:
                        logger.debug(f"Pexels image {image.get('id')} filtered out: landscape ratio {ratio}")
                elif orientation == "portrait":
                    # Accept any image that's not clearly landscape
                    if ratio <= 1.1:  # Just needs to not be clearly landscape
                        filtered_images.append(image)
                    else:
                        logger.debug(f"Pexels image {image.get('id')} filtered out: portrait ratio {ratio}")
                elif orientation == "square":
                    # Accept images close to square (very lenient)
                    if 0.5 <= ratio <= 2.0:  # Very wide range
                        filtered_images.append(image)
                    else:
                        logger.debug(f"Pexels image {image.get('id')} filtered out: square ratio {ratio}")
                else:
                    # Default: accept all decent quality images
                    filtered_images.append(image)
            else:
                logger.debug(f"Pexels image {image.get('id')} filtered out: height is 0")
        
        logger.info(f"Filtered down to {len(filtered_images)} Pexels images")
        return filtered_images
    
    def _get_best_image_url(self, image: Dict, quality: str) -> Optional[str]:
        """Get the best image URL from a Pexels image based on quality preference."""
        src = image.get('src', {})
        
        # Quality preference mapping
        if quality == "ultra":
            # Try original first, then large, then medium
            for size in ['original', 'large2x', 'large', 'medium']:
                if src.get(size):
                    return src[size]
        elif quality == "high":
            # Try large first, then medium, then original
            for size in ['large', 'large2x', 'medium', 'original']:
                if src.get(size):
                    return src[size]
        else:  # standard
            # Try medium first, then small, then large
            for size in ['medium', 'small', 'large']:
                if src.get(size):
                    return src[size]
        
        # Fallback to any available URL
        for size in ['original', 'large2x', 'large', 'medium', 'small', 'tiny']:
            if src.get(size):
                return src[size]
        
        return None
    
    def _get_display_image_url(self, image: Dict) -> Optional[str]:
        """Get a medium-sized image URL for display purposes."""
        src = image.get('src', {})
        
        # Prefer medium size for display, fallback to other sizes
        for size in ['medium', 'small', 'large', 'original']:
            if src.get(size):
                return src[size]
        
        return None
    
    async def search_images(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for images on Pexels based on query and filters.
        
        Args:
            params: Dictionary containing:
                - query: Search query string
                - per_page: Number of results per page (1-80)
                - orientation: Image orientation ('landscape', 'portrait', 'square')
                - quality: Image quality preference ('standard', 'high', 'ultra')
                - color: Color filter ('red', 'orange', 'yellow', 'green', 'turquoise', 'blue', 'violet', 'pink', 'brown', 'black', 'gray', 'white')
                - size: Size filter ('large', 'medium', 'small')
        
        Returns:
            Dictionary containing search results and metadata
        """
        if not self.api_key:
            logger.error("Pexels API key not configured. Please set PEXELS_API_KEY or PEXELS_KEY environment variable.")
            raise ValueError("Pexels API key not configured. Please check your environment variables.")
        
        query = params.get('query')
        per_page = min(params.get('per_page', 15), 80)  # Pexels max is 80
        orientation = params.get('orientation', 'landscape')
        quality = params.get('quality', 'high')
        color = params.get('color')
        size = params.get('size')
        
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
        
        # Add optional filters
        if color:
            request_params["color"] = color
        if size:
            request_params["size"] = size
        
        try:
            logger.info(f"Making Pexels API request with params: {request_params}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=request_params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response.raise_for_status()
                    data = await response.json()
            
            # Log API response details
            raw_images = data.get('photos', [])
            total_results = data.get('total_results', 0)
            logger.info(f"Pexels API returned {len(raw_images)} images out of {total_results} total results for query: '{query}'")
            
            # Filter images based on criteria
            images = raw_images
            filtered_images = self._filter_images_by_criteria(images, orientation, quality)
            
            # Process images and extract best URL for each
            processed_images = []
            for image in filtered_images:
                image_url = self._get_best_image_url(image, quality)
                if image_url:
                    # Get a smaller size for display (to improve loading performance)
                    display_url = self._get_display_image_url(image)
                    
                    processed_image = {
                        "id": image.get('id'),
                        "url": display_url,  # URL for displaying the image
                        "download_url": image_url,  # URL for downloading the full resolution image
                        "page_url": image.get('url'),  # Original Pexels page URL
                        "width": image.get('width'),
                        "height": image.get('height'),
                        "photographer": image.get('photographer'),
                        "photographer_url": image.get('photographer_url'),
                        "alt": image.get('alt', ''),
                        "src": image.get('src', {}),
                        "avg_color": image.get('avg_color', '#000000')
                    }
                    processed_images.append(processed_image)
            
            # Sort by resolution (higher resolution first for better quality)
            processed_images.sort(key=lambda x: x['width'] * x['height'], reverse=True)
            
            return {
                "images": processed_images,
                "total_results": data.get('total_results', len(processed_images)),
                "page": data.get('page', 1),
                "per_page": data.get('per_page', per_page),
                "next_page": data.get('next_page'),
                "query_used": query
            }
            
        except aiohttp.ClientError as e:
            logger.error(f"Pexels API request failed: {e}")
            raise ValueError(f"Failed to search images: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in image search: {e}")
            raise ValueError(f"Image search failed: {str(e)}")
    
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
        
        params = {
            "query": query,
            "per_page": 20,
            "orientation": orientation,
            "quality": quality
        }
        
        try:
            result = await self.search_images(params)
            images = result.get('images', [])
            
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
        """Check if Pexels image service is available."""
        return bool(self.api_key)


# Create a singleton instance
pexels_image_service = PexelsImageService()