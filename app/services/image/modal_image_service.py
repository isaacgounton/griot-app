import os
import aiohttp
import time
from typing import Dict, Any, Optional
import logging
import asyncio
from collections import deque

logger = logging.getLogger(__name__)


class ModalImageService:
    """Service for Modal Image API integration with rate limiting support."""
    
    def __init__(self):
        self.api_key = os.getenv("MODAL_IMAGE_API_KEY")
        self.base_url = os.getenv("MODAL_IMAGE_API_URL", "")
        
        # Rate limiting configuration
        self.max_requests_per_second = int(os.getenv("MODAL_IMAGE_MAX_RPS", "2"))
        self.max_concurrent = int(os.getenv("MODAL_IMAGE_MAX_CONCURRENT", "3"))
        self.retry_attempts = int(os.getenv("MODAL_IMAGE_RETRY_ATTEMPTS", "3"))
        self.base_delay = float(os.getenv("MODAL_IMAGE_BASE_DELAY", "1.0"))
        
        # Rate limiting state
        self._request_times = deque()
        self._rate_limit_lock = asyncio.Lock()
        
        if not self.api_key:
            logger.warning("MODAL_IMAGE_API_KEY not found in environment variables")
        if not self.base_url:
            logger.warning("MODAL_IMAGE_API_URL not found in environment variables")
        
        logger.info(f"Modal Image service initialized with base URL: {self.base_url}")
        logger.info(f"Rate limiting: {self.max_requests_per_second} req/s, {self.max_concurrent} concurrent")
    
    async def _wait_for_rate_limit(self):
        """Enforce rate limiting by waiting if necessary."""
        async with self._rate_limit_lock:
            current_time = time.time()
            
            # Remove requests older than 1 second
            while self._request_times and self._request_times[0] < current_time - 1.0:
                self._request_times.popleft()
            
            # If we've hit the rate limit, wait
            if len(self._request_times) >= self.max_requests_per_second:
                wait_time = 1.0 - (current_time - self._request_times[0])
                if wait_time > 0:
                    logger.debug(f"Rate limit hit, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    # Clean up again after waiting
                    current_time = time.time()
                    while self._request_times and self._request_times[0] < current_time - 1.0:
                        self._request_times.popleft()
            
            # Record this request
            self._request_times.append(current_time)
    
    async def _make_request_with_retry(self, url: str, headers: dict, data: dict | None = None, files: dict | None = None) -> bytes:
        """Make HTTP request with exponential backoff retry logic."""
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                # Wait for rate limit before making request
                await self._wait_for_rate_limit()
                
                async with aiohttp.ClientSession() as session:
                    if files:
                        # For multipart form data (image editing)
                        async with session.post(url, headers=headers, data=data) as response:
                            if response.status == 200:
                                return await response.read()
                            else:
                                response_text = await response.text()
                                logger.error(f"Modal Image API error {response.status}: {response_text}")
                                if response.status == 429:  # Rate limit exceeded
                                    retry_after = response.headers.get('Retry-After', '1')
                                    wait_time = float(retry_after) if retry_after.isdigit() else 2 ** attempt
                                    logger.warning(f"Rate limited (429), waiting {wait_time}s before retry {attempt + 1}/{self.retry_attempts}")
                                    await asyncio.sleep(wait_time)
                                    continue
                                elif response.status >= 500:  # Server errors
                                    wait_time = self.base_delay * (2 ** attempt)
                                    logger.warning(f"Server error {response.status}, waiting {wait_time}s before retry {attempt + 1}/{self.retry_attempts}")
                                    await asyncio.sleep(wait_time)
                                    continue
                                else:
                                    raise Exception(f"Modal Image API error {response.status}: {response_text}")
                    else:
                        # For form data (image generation)
                        async with session.post(url, headers=headers, data=data) as response:
                            if response.status == 200:
                                return await response.read()
                            else:
                                response_text = await response.text()
                                logger.error(f"Modal Image API error {response.status}: {response_text}")
                                if response.status == 429:  # Rate limit exceeded
                                    retry_after = response.headers.get('Retry-After', '1')
                                    wait_time = float(retry_after) if retry_after.isdigit() else 2 ** attempt
                                    logger.warning(f"Rate limited (429), waiting {wait_time}s before retry {attempt + 1}/{self.retry_attempts}")
                                    await asyncio.sleep(wait_time)
                                    continue
                                elif response.status >= 500:  # Server errors
                                    wait_time = self.base_delay * (2 ** attempt)
                                    logger.warning(f"Server error {response.status}, waiting {wait_time}s before retry {attempt + 1}/{self.retry_attempts}")
                                    await asyncio.sleep(wait_time)
                                    continue
                                else:
                                    raise Exception(f"Modal Image API error {response.status}: {response_text}")
                            
            except aiohttp.ClientError as e:
                last_exception = e
                wait_time = self.base_delay * (2 ** attempt)
                logger.warning(f"Network error on attempt {attempt + 1}/{self.retry_attempts}: {str(e)}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(wait_time)
                continue
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.retry_attempts - 1:
                    wait_time = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(wait_time)
                continue
        
        # All retries failed
        raise Exception(f"Failed after {self.retry_attempts} attempts. Last error: {str(last_exception)}")
    
    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        guidance_scale: float = 3.5,
        num_inference_steps: int = 20,
        seed: Optional[int] = None
    ) -> bytes:
        """
        Generate an image using Modal Image Dev model.
        
        Args:
            prompt: Text prompt for image generation
            width: Image width in pixels (default: 1024)
            height: Image height in pixels (default: 1024)
            guidance_scale: Guidance scale (default: 3.5)
            num_inference_steps: Number of inference steps (default: 20)
            seed: Optional seed for reproducible results
        
        Returns:
            Image binary data as bytes
        """
        if not self.api_key or not self.base_url:
            raise ValueError("Modal Image API key or URL not configured")
        
        # Validate aspect ratio (3:7 to 7:3 as per Flux requirements)
        aspect_ratio = width / height
        min_ratio = 3 / 7
        max_ratio = 7 / 3
        
        if aspect_ratio < min_ratio or aspect_ratio > max_ratio:
            raise ValueError(f"Invalid aspect ratio. Image aspect ratio ({width}:{height}) must be between 3:7 and 7:3. Current ratio: {aspect_ratio:.2f}")
        
        url = f"{self.base_url}/generate_image"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "guidance_scale": guidance_scale,
            "num_inference_steps": num_inference_steps
        }
        
        if seed is not None:
            data["seed"] = seed
        
        logger.info(f"Generating image with Flux: prompt: {prompt[:50]}..., size: {width}x{height}")
        
        try:
            result_bytes = await self._make_request_with_retry(url, headers, data)
            logger.info("Image generated successfully with Flux")
            return result_bytes
        except Exception as e:
            logger.error(f"Error generating image with Flux: {str(e)}")
            raise
    
    async def edit_image(
        self,
        image_bytes: bytes,
        prompt: str,
        guidance_scale: float = 3.5,
        num_inference_steps: int = 20,
        seed: Optional[int] = None
    ) -> bytes:
        """
        Edit an image using Modal Image Dev model.
        
        Args:
            image_bytes: Input image as bytes
            prompt: Text prompt describing the desired edit
            guidance_scale: Guidance scale (default: 3.5)
            num_inference_steps: Number of inference steps (default: 20)
            seed: Optional seed for reproducible results
        
        Returns:
            Edited image binary data as bytes
        """
        if not self.api_key or not self.base_url:
            raise ValueError("Modal Image API key or URL not configured")
        
        url = f"{self.base_url}/edit_image"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Prepare multipart form data
        data = aiohttp.FormData()
        # Use proper MIME type detection based on actual image content
        if image_bytes.startswith(b'\x89PNG'):
            content_type = 'image/png'
            filename = 'image.png'
        elif image_bytes.startswith(b'\xff\xd8\xff'):
            content_type = 'image/jpeg'
            filename = 'image.jpg'
        else:
            # Default to PNG if we can't detect the type
            content_type = 'image/png'
            filename = 'image.png'
            
        data.add_field('image', image_bytes, filename=filename, content_type=content_type)
        data.add_field('prompt', prompt)
        data.add_field('guidance_scale', str(guidance_scale))
        data.add_field('num_inference_steps', str(num_inference_steps))
        
        if seed is not None:
            data.add_field('seed', str(seed))
        
        logger.info(f"Editing image with Flux: prompt: {prompt[:50]}...")
        
        try:
            # For multipart data, we need to handle the request differently
            async with aiohttp.ClientSession() as session:
                for attempt in range(self.retry_attempts):
                    try:
                        await self._wait_for_rate_limit()
                        
                        async with session.post(url, headers=headers, data=data) as response:
                            if response.status == 200:
                                result_bytes = await response.read()
                                logger.info("Image edited successfully with Flux")
                                return result_bytes
                            else:
                                response_text = await response.text()
                                logger.error(f"Modal Image API error {response.status}: {response_text}")
                                if response.status == 429:  # Rate limit exceeded
                                    retry_after = response.headers.get('Retry-After', '1')
                                    wait_time = float(retry_after) if retry_after.isdigit() else 2 ** attempt
                                    logger.warning(f"Rate limited (429), waiting {wait_time}s before retry {attempt + 1}/{self.retry_attempts}")
                                    await asyncio.sleep(wait_time)
                                    continue
                                elif response.status >= 500:  # Server errors
                                    wait_time = self.base_delay * (2 ** attempt)
                                    logger.warning(f"Server error {response.status}, waiting {wait_time}s before retry {attempt + 1}/{self.retry_attempts}")
                                    await asyncio.sleep(wait_time)
                                    continue
                                else:
                                    raise Exception(f"Modal Image API error {response.status}: {response_text}")
                    except aiohttp.ClientError as e:
                        if attempt < self.retry_attempts - 1:
                            wait_time = self.base_delay * (2 ** attempt)
                            logger.warning(f"Network error on attempt {attempt + 1}/{self.retry_attempts}: {str(e)}")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise Exception(f"Network error after {self.retry_attempts} attempts: {str(e)}")
                
                raise Exception(f"Failed after {self.retry_attempts} attempts")
        except Exception as e:
            logger.error(f"Error editing image with Flux: {str(e)}")
            raise
    
    async def generate_multiple_images(
        self,
        prompts: list[str],
        width: int = 1024,
        height: int = 1024,
        guidance_scale: float = 3.5,
        num_inference_steps: int = 20
    ) -> list[Dict[str, Any]]:
        """
        Generate multiple images concurrently with intelligent rate limiting.
        
        Args:
            prompts: List of text prompts for image generation
            width: Image width in pixels (default: 1024)
            height: Image height in pixels (default: 1024)
            guidance_scale: Guidance scale (default: 3.5)
            num_inference_steps: Number of inference steps (default: 20)
        
        Returns:
            List of dictionaries containing generated image data
        """
        if not prompts:
            return []
        
        logger.info(f"Generating {len(prompts)} images with Flux")
        logger.info(f"Dimensions: {width}x{height}, guidance: {guidance_scale}, steps: {num_inference_steps}")
        logger.info(f"Rate limiting: {self.max_requests_per_second} req/s, max {self.max_concurrent} concurrent")
        
        # Use configured max_concurrent from environment
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def generate_single(prompt: str, index: int) -> Dict[str, Any]:
            async with semaphore:
                try:
                    result_bytes = await self.generate_image(
                        prompt=prompt,
                        width=width,
                        height=height,
                        guidance_scale=guidance_scale,
                        num_inference_steps=num_inference_steps
                    )
                    # Convert binary data to base64 to match Together.ai format
                    import base64
                    b64_data = base64.b64encode(result_bytes).decode('utf-8')
                    
                    return {
                        "index": index,
                        "prompt": prompt,
                        "success": True,
                        "data": {
                            "data": [{
                                "b64_json": b64_data
                            }]
                        }
                    }
                except Exception as e:
                    logger.error(f"Failed to generate image {index}: {str(e)}")
                    return {
                        "index": index,
                        "prompt": prompt,
                        "success": False,
                        "error": str(e)
                    }
        
        # Create tasks for all prompts with proper index mapping
        tasks = [generate_single(prompt, i) for i, prompt in enumerate(prompts)]
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_results = []
        for result in results:
            if isinstance(result, dict) and result.get("success"):
                successful_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Task failed with exception: {str(result)}")
        
        logger.info(f"Successfully generated {len(successful_results)}/{len(prompts)} images")
        
        return successful_results
    
    def is_available(self) -> bool:
        """Check if the Modal Image service is available (API key and URL configured)."""
        return bool(self.api_key and self.base_url)

    def get_available_models(self) -> list[str]:
        """Get list of available Modal Image models."""
        # Modal Image supports a single model
        return ['modal-image']


# Global instance
modal_image_service = ModalImageService()

# Backward compatibility alias
flux_service = modal_image_service