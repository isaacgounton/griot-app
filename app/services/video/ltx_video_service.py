import os
import aiohttp
import base64
import time
import logging
import asyncio
from typing import Dict, Any, Optional
from collections import deque

logger = logging.getLogger(__name__)


class ModalVideoService:
    """Service for Modal Video deployment integration."""
    
    def __init__(self):
        self.api_url = os.getenv("MODAL_VIDEO_API_URL")
        self.api_key = os.getenv("MODAL_VIDEO_API_KEY")
        
        if not self.api_url:
            logger.warning("MODAL_VIDEO_API_URL not found in environment variables")
        
        if not self.api_key:
            logger.warning("MODAL_VIDEO_API_KEY not found in environment variables")
        
        logger.info(f"Modal Video service initialized with API URL: {self.api_url}")
    
    async def generate_video(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 704,
        height: int = 480,
        num_frames: int = 150,  # produces ~10s of video
        num_inference_steps: int = 200,
        guidance_scale: float = 4.5,
        seed: Optional[int] = None
    ) -> bytes:
        """
        Generate a video using Modal Video Modal deployment.
        
        Args:
            prompt: Text prompt for video generation
            negative_prompt: Text prompt for what to avoid in the video
            width: Video width in pixels (must be divisible by 32)
            height: Video height in pixels (must be divisible by 32)
            num_frames: Number of frames to generate (1-257)
            num_inference_steps: Number of inference steps
            guidance_scale: Guidance scale for prompt adherence
            seed: Random seed for reproducible results
            
        Returns:
            Video binary data as bytes
        """
        if not self.api_url or not self.api_key:
            raise ValueError("Modal Video API URL or API key not configured")
        
        # Validate dimensions (must be divisible by 32)
        if width % 32 != 0 or height % 32 != 0:
            raise ValueError("Width and height must be divisible by 32")
        
        # Validate frame count
        if num_frames < 1 or num_frames > 257:
            raise ValueError("num_frames must be between 1 and 257")
        
        url = f"{self.api_url}/generate_video"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Prepare form data
        form_data = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": str(width),
            "height": str(height),
            "num_frames": str(num_frames),
            "num_inference_steps": str(num_inference_steps),
            "guidance_scale": str(guidance_scale)
        }
        
        if seed is not None:
            form_data["seed"] = str(seed)
        
        logger.info(f"Generating video with Modal Video: prompt: {prompt[:50]}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=form_data) as response:
                    response_content = await response.read()
                    
                    if response.status == 200:
                        logger.info("Video generated successfully with Modal Video")
                        return response_content
                    else:
                        error_text = response_content.decode('utf-8') if response_content else "Unknown error"
                        logger.error(f"Modal Video API error {response.status}: {error_text}")
                        raise Exception(f"Modal Video API error {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"Error generating video with Modal Video: {str(e)}")
            raise
    
    async def image_to_video(
        self,
        image_bytes: bytes,
        prompt: str,
        negative_prompt: str = "",
        width: int = 704,
        height: int = 480,
        num_frames: int = 150,
        num_inference_steps: int = 200,
        guidance_scale: float = 4.5,
        seed: Optional[int] = None
    ) -> bytes:
        """
        Generate a video from an image using Modal Video Modal deployment.
        
        Args:
            image_bytes: Image binary data
            prompt: Text prompt describing the video motion/content
            negative_prompt: Text prompt for what to avoid in the video
            width: Video width in pixels (must be divisible by 32)
            height: Video height in pixels (must be divisible by 32)
            num_frames: Number of frames to generate (1-257)
            num_inference_steps: Number of inference steps
            guidance_scale: Guidance scale for prompt adherence
            seed: Random seed for reproducible results
            
        Returns:
            Video binary data as bytes
        """
        if not self.api_url or not self.api_key:
            raise ValueError("Modal Video API URL or API key not configured")
        
        # Validate dimensions (must be divisible by 32)
        if width % 32 != 0 or height % 32 != 0:
            raise ValueError("Width and height must be divisible by 32")
        
        # Validate frame count
        if num_frames < 1 or num_frames > 257:
            raise ValueError("num_frames must be between 1 and 257")
        
        url = f"{self.api_url}/image_to_video"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Prepare form data
        form_data = aiohttp.FormData()
        form_data.add_field('image', image_bytes, filename='image.png', content_type='image/png')
        form_data.add_field('prompt', prompt)
        form_data.add_field('negative_prompt', negative_prompt)
        form_data.add_field('width', str(width))
        form_data.add_field('height', str(height))
        form_data.add_field('num_frames', str(num_frames))
        form_data.add_field('num_inference_steps', str(num_inference_steps))
        form_data.add_field('guidance_scale', str(guidance_scale))
        
        if seed is not None:
            form_data.add_field('seed', str(seed))
        
        logger.info(f"Generating video from image with Modal Video: prompt: {prompt[:50]}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=form_data) as response:
                    response_content = await response.read()
                    
                    if response.status == 200:
                        logger.info("Video generated successfully from image with Modal Video")
                        return response_content
                    else:
                        error_text = response_content.decode('utf-8') if response_content else "Unknown error"
                        logger.error(f"Modal Video API error {response.status}: {error_text}")
                        raise Exception(f"Modal Video API error {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"Error generating video from image with Modal Video: {str(e)}")
            raise
    
    def is_available(self) -> bool:
        """Check if the Modal Video service is available (API URL and key configured)."""
        return bool(self.api_url and self.api_key)


# Global instance
modal_video_service = ModalVideoService()

# Backward compatibility alias
ltx_video_service = modal_video_service