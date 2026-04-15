import os
import aiohttp
import asyncio
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class WaveSpeedAIService:
    """Service for WaveSpeedAI video generation integration."""
    
    def __init__(self):
        self.api_key = os.getenv("WAVESPEEDAI_API_KEY")
        self.base_url = "https://api.wavespeed.ai/api/v3"
        
        if not self.api_key:
            logger.warning("WAVESPEEDAI_API_KEY not found in environment variables")
        
        logger.info(f"WaveSpeedAI service initialized with base URL: {self.base_url}")
    
    async def text_to_video(
        self,
        prompt: str,
        model: str = "wan-2.2",
        size: str = "832*480",
        duration: int = 5,
        seed: int = -1,
        max_wait_time: int = 300  # 5 minutes max wait
    ) -> bytes:
        """
        Generate a video from a text prompt using WaveSpeedAI.
        
        Args:
            prompt: Text prompt describing the video content
            model: Model version to use (wan-2.2, minimax-video-02, etc.)
            size: Video dimensions (832*480, 480*832)
            duration: Video duration in seconds (5, 8)
            seed: Random seed for reproducible results (-1 for random)
            max_wait_time: Maximum time to wait for completion in seconds
            
        Returns:
            Video binary data as bytes
        """
        if not self.api_key:
            raise ValueError("WaveSpeedAI API key not configured")
        
        # Submit the generation request
        request_id = await self._submit_text_to_video_request(prompt, model, size, duration, seed)
        
        # Poll for results
        video_url = await self._poll_for_result(request_id, max_wait_time)
        
        # Download the video
        video_bytes = await self._download_video(video_url)
        
        return video_bytes

    async def image_to_video(
        self,
        image_url: str,
        prompt: str,
        seed: int = -1,
        model: str = "wan-2.2",
        resolution: str = "720p",
        max_wait_time: int = 300  # 5 minutes max wait
    ) -> bytes:
        """
        Generate a video from an image using WaveSpeedAI.
        
        Args:
            image_url: URL of the image to animate
            prompt: Text prompt describing the video motion/content
            seed: Random seed for reproducible results (-1 for random)
            model: Model version to use (default: wan-2.2)
            resolution: Video resolution (720p, 1080p, etc.)
            max_wait_time: Maximum time to wait for completion in seconds
            
        Returns:
            Video binary data as bytes
        """
        if not self.api_key:
            raise ValueError("WaveSpeedAI API key not configured")
        
        # Submit the generation request
        request_id = await self._submit_request(image_url, prompt, seed, model, resolution)
        
        # Poll for results
        video_url = await self._poll_for_result(request_id, max_wait_time)
        
        # Download the video
        video_bytes = await self._download_video(video_url)
        
        return video_bytes
    
    async def _submit_text_to_video_request(
        self,
        prompt: str,
        model: str,
        size: str,
        duration: int,
        seed: int
    ) -> str:
        """Submit a text-to-video generation request and return the request ID."""
        # Use the ultra-fast WAN 2.2 endpoint
        if model == "wan-2.2":
            endpoint = f"{self.base_url}/wavespeed-ai/wan-2.2/t2v-480p-ultra-fast"
            payload = {
                "prompt": prompt,
                "size": size,
                "duration": duration,
                "seed": seed
            }
        elif model == "minimax-video-02":
            endpoint = f"{self.base_url}/minimax/video-02"
            payload = {
                "prompt": prompt,
                "resolution": "768p" if "832" in size else "480p",
                "duration": duration,
                "enable_prompt_expansion": True
            }
        elif model == "minimax-video-01":
            endpoint = f"{self.base_url}/minimax/video-01"
            payload = {
                "prompt": prompt,
                "aspect_ratio": "16:9" if "832" in size else "9:16",
                "fps": 25
            }
        else:
            raise ValueError(f"Unsupported model: {model}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        logger.info(f"Submitting WaveSpeedAI text-to-video request with {model}: {prompt[:50]}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    request_id = result["data"]["id"]
                    logger.info(f"WaveSpeedAI text-to-video request submitted successfully. Request ID: {request_id}")
                    return request_id
                else:
                    error_text = await response.text()
                    logger.error(f"WaveSpeedAI API error {response.status}: {error_text}")
                    raise Exception(f"WaveSpeedAI API error {response.status}: {error_text}")
    
    async def _submit_request(
        self,
        image_url: str,
        prompt: str,
        seed: int,
        model: str,
        resolution: str
    ) -> str:
        """Submit a video generation request and return the request ID."""
        url = f"{self.base_url}/wavespeed-ai/{model}/i2v-5b-{resolution}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "image": image_url,
            "prompt": prompt,
            "seed": seed
        }
        
        logger.info(f"Submitting WaveSpeedAI request: {prompt[:50]}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    request_id = result["data"]["id"]
                    logger.info(f"WaveSpeedAI request submitted successfully. Request ID: {request_id}")
                    return request_id
                else:
                    error_text = await response.text()
                    logger.error(f"WaveSpeedAI API error {response.status}: {error_text}")
                    raise Exception(f"WaveSpeedAI API error {response.status}: {error_text}")
    
    async def _poll_for_result(self, request_id: str, max_wait_time: int) -> str:
        """Poll for the result of a video generation request."""
        url = f"{self.base_url}/predictions/{request_id}/result"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        data = result["data"]
                        status = data["status"]
                        
                        if status == "completed":
                            video_url = data["outputs"][0]
                            elapsed = time.time() - start_time
                            logger.info(f"WaveSpeedAI generation completed in {elapsed:.1f}s. URL: {video_url}")
                            return video_url
                        elif status == "failed":
                            error = data.get("error", "Unknown error")
                            logger.error(f"WaveSpeedAI generation failed: {error}")
                            raise Exception(f"WaveSpeedAI generation failed: {error}")
                        else:
                            logger.info(f"WaveSpeedAI generation in progress. Status: {status}")
                    else:
                        error_text = await response.text()
                        logger.error(f"WaveSpeedAI polling error {response.status}: {error_text}")
                        raise Exception(f"WaveSpeedAI polling error {response.status}: {error_text}")
            
            await asyncio.sleep(2)  # Wait 2 seconds between polls
        
        raise Exception(f"WaveSpeedAI generation timed out after {max_wait_time} seconds")
    
    async def _download_video(self, video_url: str) -> bytes:
        """Download the generated video from the provided URL."""
        logger.info(f"Downloading video from WaveSpeedAI: {video_url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as response:
                if response.status == 200:
                    video_bytes = await response.read()
                    logger.info(f"Video downloaded successfully ({len(video_bytes)} bytes)")
                    return video_bytes
                else:
                    error_text = await response.text()
                    logger.error(f"Video download error {response.status}: {error_text}")
                    raise Exception(f"Video download error {response.status}: {error_text}")
    
    def is_available(self) -> bool:
        """Check if the WaveSpeedAI service is available (API key configured)."""
        return bool(self.api_key)


# Global instance
wavespeed_service = WaveSpeedAIService()