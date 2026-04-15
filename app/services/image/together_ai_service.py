import os
import aiohttp
import base64
import time
from typing import Dict, Any, Optional
import logging
import asyncio
from collections import deque

logger = logging.getLogger(__name__)


class TogetherAIService:
    """Service for Together.ai API integration with rate limiting support."""
    
    def __init__(self):
        self.base_url = "https://api.together.xyz/v1"
        self.api_key = os.getenv("TOGETHER_API_KEY")
        self.default_model = os.getenv("TOGETHER_DEFAULT_MODEL", "black-forest-labs/FLUX.1-schnell")
        self.default_width = int(os.getenv("TOGETHER_DEFAULT_WIDTH", "576"))
        self.default_height = int(os.getenv("TOGETHER_DEFAULT_HEIGHT", "1024"))
        self.default_steps = int(os.getenv("TOGETHER_DEFAULT_STEPS", "4"))
        
        # Parse available models from environment
        models_env = os.getenv("TOGETHER_MODELS", "black-forest-labs/FLUX.1-schnell,black-forest-labs/FLUX.1-dev,Qwen/Qwen2-VL-72B-Instruct,stabilityai/stable-diffusion-3-medium")
        self.available_models = [m.strip() for m in models_env.split(",") if m.strip()]
        
        # Rate limiting configuration
        self.max_requests_per_second = int(os.getenv("TOGETHER_MAX_RPS", "2"))  # Conservative default
        self.max_concurrent = int(os.getenv("TOGETHER_MAX_CONCURRENT", "3"))
        self.retry_attempts = int(os.getenv("TOGETHER_RETRY_ATTEMPTS", "3"))
        self.base_delay = float(os.getenv("TOGETHER_BASE_DELAY", "1.0"))  # Base delay between requests
        
        # Rate limiting state
        self._request_times = deque()
        self._rate_limit_lock = asyncio.Lock()
        
        if not self.api_key:
            logger.warning("TOGETHER_API_KEY not found in environment variables")
        
        logger.info(f"Together.ai service initialized with model: {self.default_model}")
        logger.info(f"Available models: {self.available_models}")
        logger.info(f"Default dimensions: {self.default_width}x{self.default_height}, steps: {self.default_steps}")
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
    
    async def _make_request_with_retry(self, url: str, headers: dict, payload: dict) -> dict:
        """Make HTTP request with exponential backoff retry logic."""
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                # Wait for rate limit before making request
                await self._wait_for_rate_limit()
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=payload) as response:
                        response_text = await response.text()
                        
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:  # Rate limit exceeded
                            retry_after = response.headers.get('Retry-After', '1')
                            wait_time = float(retry_after) if retry_after.isdigit() else 2 ** attempt
                            logger.warning(f"Rate limited (429), waiting {wait_time}s before retry {attempt + 1}/{self.retry_attempts}")
                            await asyncio.sleep(wait_time)
                            continue
                        elif response.status >= 500:  # Server errors
                            wait_time = self.base_delay * (2 ** attempt)
                            logger.warning(f"Together AI server error {response.status} (attempt {attempt + 1}/{self.retry_attempts}), waiting {wait_time}s before retry")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            # Client error, don't retry
                            logger.error(f"Together.ai API error {response.status}: {response_text}")
                            raise Exception(f"Together.ai API error {response.status}: {response_text}")
                            
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
        model: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        steps: Optional[int] = None,
        n: int = 1,
        response_format: str = "b64_json"
    ) -> Dict[str, Any]:
        """
        Generate an image using Together.ai's Modal Image model.
        
        Args:
            prompt: Text prompt for image generation
            model: Model to use (default: from environment or Modal Image.1-schnell)
            width: Image width in pixels (default: from environment or 576)
            height: Image height in pixels (default: from environment or 1024)
            steps: Number of inference steps (default: from environment or 4)
            n: Number of images to generate
            response_format: Response format ('b64_json' or 'url')
        
        Returns:
            Dictionary containing the generated image data
        """
        if not self.api_key:
            raise ValueError("Together.ai API key not configured")
        
        # Use environment defaults if not specified
        model = model or self.default_model
        width = width or self.default_width
        height = height or self.default_height
        steps = steps or self.default_steps
        
        # Validate steps parameter (Together.ai requires 1-12)
        if steps < 1 or steps > 12:
            logger.warning(f"Steps value {steps} is outside valid range (1-12). Clamping to valid range.")
            steps = max(1, min(12, steps))
        
        url = f"{self.base_url}/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "n": n,
            "response_format": response_format
        }
        
        logger.info(f"Generating image with Together.ai: {model}, prompt: {prompt[:50]}...")
        
        try:
            result = await self._make_request_with_retry(url, headers, payload)
            logger.info("Image generated successfully with Together.ai")
            return result
        except Exception as e:
            logger.error(f"Error generating image with Together.ai: {str(e)}")
            raise
    
    async def generate_image_from_b64(
        self,
        prompt: str,
        model: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        steps: Optional[int] = None
    ) -> bytes:
        """
        Generate an image and return the binary data directly.
        
        Args:
            prompt: Text prompt for image generation
            model: Model to use (default: from environment)
            width: Image width in pixels (default: from environment)
            height: Image height in pixels (default: from environment)
            steps: Number of inference steps (default: from environment)
        
        Returns:
            Image binary data as bytes
        """
        result = await self.generate_image(
            prompt=prompt,
            model=model or self.default_model,
            width=width or self.default_width,
            height=height or self.default_height,
            steps=steps or self.default_steps,
            response_format="b64_json"
        )
        
        if "data" not in result or not result["data"]:
            raise Exception("No image data received from Together.ai")
        
        b64_json = result["data"][0]["b64_json"]
        image_data = base64.b64decode(b64_json)
        
        return image_data
    
    async def generate_multiple_images(
        self,
        prompts: list[str],
        model: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        steps: Optional[int] = None
    ) -> list[Dict[str, Any]]:
        """
        Generate multiple images concurrently with intelligent rate limiting.
        
        Automatically handles Together.ai rate limits with:
        - Per-second request rate limiting
        - Concurrent request limiting
        - Exponential backoff retry logic
        - 429 rate limit response handling
        
        Args:
            prompts: List of text prompts for image generation
            model: Model to use (default: from environment)
            width: Image width in pixels (default: from environment)
            height: Image height in pixels (default: from environment)
            steps: Number of inference steps (default: from environment)
        
        Returns:
            List of dictionaries containing generated image data
        
        Rate limiting is configured via environment variables:
        - TOGETHER_MAX_RPS: Max requests per second (default: 2)
        - TOGETHER_MAX_CONCURRENT: Max concurrent requests (default: 3)
        - TOGETHER_RETRY_ATTEMPTS: Retry attempts (default: 3)
        """
        if not prompts:
            return []
        
        # Use environment defaults
        model = model or self.default_model
        width = width or self.default_width
        height = height or self.default_height
        steps = steps or self.default_steps
        
        # Validate steps parameter (Together.ai requires 1-12)
        if steps < 1 or steps > 12:
            logger.warning(f"Steps value {steps} is outside valid range (1-12). Clamping to valid range.")
            steps = max(1, min(12, steps))
        
        logger.info(f"Generating {len(prompts)} images with Together.ai")
        logger.info(f"Using model: {model}, dimensions: {width}x{height}, steps: {steps}")
        logger.info(f"Rate limiting: {self.max_requests_per_second} req/s, max {self.max_concurrent} concurrent")
        
        # Use configured max_concurrent from environment
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def generate_single(prompt: str, index: int) -> Dict[str, Any]:
            async with semaphore:
                try:
                    result = await self.generate_image(
                        prompt=prompt,
                        model=model,
                        width=width,
                        height=height,
                        steps=steps
                    )
                    return {
                        "index": index,
                        "prompt": prompt,
                        "success": True,
                        "data": result
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
        """Check if the Together.ai service is available (API key configured)."""
        return bool(self.api_key)
    
    def get_available_models(self) -> list:
        """Get list of available Together.ai image generation models."""
        return self.available_models


# Global instance
together_ai_service = TogetherAIService()