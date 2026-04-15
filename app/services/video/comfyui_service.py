import os
import aiohttp
import asyncio
import time
import logging
import random

logger = logging.getLogger(__name__)


class ComfyUIService:
    """Service for ComfyUI video generation integration."""
    
    def __init__(self):
        self.api_key = os.getenv("COMFYUI_API_KEY")
        self.base_url = os.getenv("COMFYUI_URL", "")
        self.username = os.getenv("COMFYUI_USERNAME")
        self.password = os.getenv("COMFYUI_PASSWORD")
        
        # Remove trailing slash for consistency
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
        
        if not self.base_url:
            logger.warning("COMFYUI_URL not found in environment variables")
        
        logger.info(f"ComfyUI service initialized with base URL: {self.base_url}")
        if self.username:
            logger.info(f"ComfyUI service configured with username: {self.username}")
            logger.debug(f"ComfyUI password configured: {'Yes' if self.password else 'No'}")
        if self.api_key:
            logger.info("ComfyUI service configured with API key")
        if not self.is_available():
            logger.warning("ComfyUI service is not properly configured")
    
    def is_available(self) -> bool:
        """Check if ComfyUI service is available and configured."""
        return bool(self.base_url and (self.api_key or (self.username and self.password)))
    
    async def verify_connection(self) -> bool:
        """Verify that ComfyUI server is accessible and responding."""
        if not self.is_available():
            return False
            
        try:
            auth = None
            if self.username and self.password:
                auth = aiohttp.BasicAuth(self.username, self.password)
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/"
                async with session.get(url, auth=auth, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    return response.status == 200
        except Exception as e:
            logger.warning(f"ComfyUI connection verification failed: {str(e)}")
            return False
    
    
    async def text_to_video(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1280,
        height: int = 704,
        num_frames: int = 121,
        max_wait_time: int = 600  # 10 minutes max wait for ComfyUI
    ) -> bytes:
        """
        Generate a video from a text prompt using ComfyUI.
        
        Args:
            prompt: Text prompt describing the video content
            negative_prompt: Negative prompt for what to avoid
            width: Video width in pixels
            height: Video height in pixels  
            num_frames: Number of frames to generate
            max_wait_time: Maximum time to wait for completion in seconds
            
        Returns:
            Video binary data as bytes
        """
        if not self.is_available():
            raise ValueError("ComfyUI service is not available (URL and auth not configured)")
        
        # Submit the generation request
        prompt_id = await self._submit_video_request(prompt, negative_prompt, width, height, num_frames)
        
        # Wait for completion and get result
        return await self._wait_for_completion_and_download(prompt_id, max_wait_time)
    
    async def _submit_video_request(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        num_frames: int
    ) -> str:
        """Submit a video generation request to ComfyUI."""
        
        # Generate random seed
        seed = random.randint(1, 0xFFFFFFFF - 1)
        
        # Create workflow based on n8n configuration
        workflow = {
            "3": {
                "inputs": {
                    "seed": seed,
                    "steps": 20,
                    "cfg": 5,
                    "sampler_name": "uni_pc",
                    "scheduler": "simple",
                    "denoise": 1,
                    "model": ["48", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["55", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"}
            },
            "6": {
                "inputs": {
                    "text": prompt,
                    "clip": ["38", 0]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Positive Prompt)"}
            },
            "7": {
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["38", 0]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Negative Prompt)"}
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["39", 0]
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE Decode"}
            },
            "37": {
                "inputs": {
                    "unet_name": "wan2.2_ti2v_5B_fp16.safetensors",
                    "weight_dtype": "default"
                },
                "class_type": "UNETLoader",
                "_meta": {"title": "Load Diffusion Model"}
            },
            "38": {
                "inputs": {
                    "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                    "type": "wan",
                    "device": "default"
                },
                "class_type": "CLIPLoader",
                "_meta": {"title": "Load CLIP"}
            },
            "39": {
                "inputs": {
                    "vae_name": "wan2.2_vae.safetensors"
                },
                "class_type": "VAELoader",
                "_meta": {"title": "Load VAE"}
            },
            "48": {
                "inputs": {
                    "shift": 8,
                    "model": ["37", 0]
                },
                "class_type": "ModelSamplingSD3",
                "_meta": {"title": "ModelSamplingSD3"}
            },
            "55": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "length": num_frames,
                    "batch_size": 1,
                    "vae": ["39", 0]
                },
                "class_type": "Wan22ImageToVideoLatent",
                "_meta": {"title": "Wan22ImageToVideoLatent"}
            },
            "57": {
                "inputs": {
                    "fps": 24,
                    "images": ["8", 0]
                },
                "class_type": "CreateVideo",
                "_meta": {"title": "Create Video"}
            },
            "58": {
                "inputs": {
                    "filename_prefix": "video/ComfyUI",
                    "format": "auto",
                    "codec": "auto",
                    "video-preview": "",
                    "video": ["57", 0]
                },
                "class_type": "SaveVideo",
                "_meta": {"title": "Save Video"}
            }
        }
        
        payload = {
            "client_id": "griot",
            "prompt": workflow
        }
        
        # Create auth
        auth = None
        if self.username and self.password:
            auth = aiohttp.BasicAuth(self.username, self.password)
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/prompt"
            
            logger.info(f"Submitting ComfyUI video generation request to {url}")
            logger.debug(f"Payload: {payload}")
            
            async with session.post(url, json=payload, auth=auth, headers=headers) as response:
                logger.info(f"ComfyUI response status: {response.status}")
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"ComfyUI request failed:")
                    logger.error(f"  Status: {response.status}")
                    logger.error(f"  URL: {url}")
                    logger.error(f"  Response: {error_text}")
                    logger.error(f"  Headers: {dict(response.headers)}")
                    
                    # Check if it's an authentication issue
                    if response.status == 401:
                        raise Exception(f"ComfyUI authentication failed. Check username/password or API key.")
                    elif response.status == 404:
                        raise Exception(f"ComfyUI endpoint not found. Check if the URL is correct: {url}")
                    else:
                        raise Exception(f"ComfyUI request failed with status {response.status}: {error_text}")
                
                try:
                    result = await response.json()
                    logger.debug(f"ComfyUI response: {result}")
                except Exception as e:
                    response_text = await response.text()
                    logger.error(f"Failed to parse ComfyUI response as JSON: {response_text}")
                    raise Exception(f"Invalid JSON response from ComfyUI: {str(e)}")
                
                # Check for API errors in response
                if "error" in result:
                    error_info = result["error"]
                    error_msg = f"ComfyUI API error: {error_info.get('type', 'unknown')} - {error_info.get('message', 'no message')}"
                    logger.error(error_msg)
                    logger.error(f"Error details: {error_info.get('details', 'none')}")
                    if "node_errors" in result and result["node_errors"]:
                        logger.error(f"Node errors: {result['node_errors']}")
                    raise Exception(error_msg)
                
                prompt_id = result.get("prompt_id")
                
                if not prompt_id:
                    logger.error(f"No prompt_id in ComfyUI response: {result}")
                    raise Exception("No prompt_id returned from ComfyUI")
                
                logger.info(f"ComfyUI request submitted successfully with prompt_id: {prompt_id}")
                return prompt_id
    
    async def _wait_for_completion_and_download(self, prompt_id: str, max_wait_time: int) -> bytes:
        """Wait for ComfyUI to complete generation and download the result."""
        
        start_time = time.time()
        
        # Create auth
        auth = None
        if self.username and self.password:
            auth = aiohttp.BasicAuth(self.username, self.password)
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < max_wait_time:
                try:
                    # Check status
                    history_url = f"{self.base_url}/history/{prompt_id}"
                    
                    async with session.get(history_url, auth=auth, headers=headers) as response:
                        if response.status == 200:
                            history = await response.json()
                            
                            # Check if our prompt_id is in history and completed
                            if prompt_id in history and history[prompt_id].get("status", {}).get("completed", False):
                                status_info = history[prompt_id].get("status", {})
                                
                                if status_info.get("status_str") == "success":
                                    logger.info(f"ComfyUI generation completed successfully for prompt_id: {prompt_id}")
                                    
                                    # Get the output filename from the history
                                    outputs = history[prompt_id].get("outputs", {})
                                    
                                    # Find the video output (node 58 is SaveVideo)
                                    video_output = None
                                    for node_output in outputs.values():
                                        if "images" in node_output and len(node_output["images"]) > 0:
                                            for image_info in node_output["images"]:
                                                if image_info.get("type") == "output":
                                                    video_output = image_info
                                                    break
                                    
                                    if video_output:
                                        filename = video_output.get("filename")
                                        subfolder = video_output.get("subfolder", "")
                                        
                                        # Download the video
                                        view_url = f"{self.base_url}/view"
                                        params = {
                                            "type": "output",
                                            "filename": filename
                                        }
                                        if subfolder:
                                            params["subfolder"] = subfolder
                                        
                                        async with session.get(view_url, params=params, auth=auth, headers=headers) as download_response:
                                            if download_response.status == 200:
                                                video_data = await download_response.read()
                                                logger.info(f"Successfully downloaded video from ComfyUI: {len(video_data)} bytes")
                                                return video_data
                                            else:
                                                error_text = await download_response.text()
                                                raise Exception(f"Failed to download video: {download_response.status} - {error_text}")
                                    else:
                                        raise Exception("No video output found in ComfyUI results")
                                else:
                                    # Generation failed
                                    error_msg = f"ComfyUI generation failed with status: {status_info.get('status_str', 'unknown')}"
                                    logger.error(error_msg)
                                    raise Exception(error_msg)
                        
                        elif response.status == 404:
                            # Job not found yet, continue waiting
                            pass
                        else:
                            logger.warning(f"Unexpected response from ComfyUI history endpoint: {response.status}")
                
                except Exception as e:
                    logger.warning(f"Error checking ComfyUI status: {e}")
                
                # Wait before next check
                await asyncio.sleep(10)
                logger.debug(f"Waiting for ComfyUI completion... ({time.time() - start_time:.1f}s elapsed)")
            
            # Timeout reached
            elapsed = time.time() - start_time
            error_msg = f"ComfyUI generation timed out after {elapsed:.1f} seconds"
            logger.error(error_msg)
            raise Exception(error_msg)


# Global service instance
comfyui_service = ComfyUIService()