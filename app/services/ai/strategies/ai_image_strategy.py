import logging
from typing import Dict, Any, List, Optional
from app.services.ai.media_generation_strategy import MediaGenerationStrategy
from app.services.text.image_prompt_generator import image_prompt_generator
from app.services.image.together_ai_service import together_ai_service
from app.services.image.modal_image_service import modal_image_service
from app.services.pollinations import pollinations_service
from app.services.image.image_to_video import image_to_video_service
from app.services.s3.s3 import s3_service

logger = logging.getLogger(__name__)


class AIImageStrategy(MediaGenerationStrategy):
    """Strategy for generating video segments using AI-generated images with motion effects."""
    
    def get_strategy_name(self) -> str:
        return "AI Image Strategy (Together.ai/Flux/Pollinations + Motion)"
    
    async def generate_media_segments(
        self, 
        video_queries: List[Dict], 
        orientation: str,
        params: Dict[str, Any]
    ) -> List[Optional[Dict[str, Any]]]:
        """Generate video segments using AI-generated images with motion effects."""
        
        image_provider = params.get('image_provider', 'together')
        image_model = params.get('image_model') or params.get('aiImageModel')  # Support both naming conventions
        footage_quality = params.get('footage_quality', 'high')
        motion_params = params.get('motion_params', {})
        
        logger.info(f"Generating AI images with motion using provider: {image_provider}, model: {image_model}")
        
        background_videos: List[Optional[Dict[str, Any]]] = []
        
        for i, query_data in enumerate(video_queries):
            query = query_data['query']

            try:
                video_url = await self._generate_ai_image_to_video(
                    query_data,  # Pass full query_data instead of just query
                    orientation,
                    footage_quality,
                    i,  # Use scene index as seed variation
                    image_provider,
                    image_model,  # Pass the image model
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
                        'query': query,
                        'provider': f"ai_generated_{image_provider}"
                    })
                else:
                    logger.warning(f"Failed to generate AI image for query: {query}")
                    background_videos.append(None)
                    
            except Exception as e:
                logger.error(f"Error generating AI image for query '{query}': {e}")
                background_videos.append(None)
        
        return background_videos
    
    async def _generate_ai_image_to_video(
        self,
        query_data: dict,
        orientation: str,
        quality: str,
        seed_variation: int,
        image_provider: str = "together",
        image_model: Optional[str] = None,  # Add image model parameter
        effect_type: str = 'ken_burns',  # Currently unused but may be needed for future motion effects
        zoom_speed: float = 10.0,
        pan_direction: str = 'right',  # Currently unused but may be needed for future motion effects
        ken_burns_keypoints: Optional[List] = None  # Currently unused but may be needed for future motion effects
    ) -> Optional[str]:
        """Generate AI image and convert to video with motion effects."""

        try:
            # Extract data from query_data
            query = query_data['query']
            duration = query_data.get('duration', 3.0)
            script_text = query_data.get('script_text', query)  # Full narration text
            full_script = query_data.get('full_script', script_text)  # Complete script
            segment_position = query_data.get('index', seed_variation) + 1  # 1-based index
            total_segments = query_data.get('total_segments', 5)  # Total segments
            semantics = query_data.get('semantics', {})  # Semantic analysis

            # Step 1: Generate enhanced image prompt with full context
            logger.info(f"Generating image prompt for query: {query}")
            logger.info(f"Full narration context: {script_text[:100]}...")
            image_prompt = await image_prompt_generator.generate_image_prompt_for_segment(
                script_text=script_text,  # Full segment narration
                full_script=full_script,  # Complete script context
                segment_position=segment_position,
                total_segments=total_segments,
                search_query=query,  # Search keywords for visual themes
                semantics=semantics  # Sentiment, domain, etc.
            )
            
            logger.info(f"Enhanced prompt: {image_prompt}")
            
            # Step 2: Determine image dimensions with proper validation
            width, height = self._get_validated_dimensions(orientation)
            
            # Step 3: Generate AI image
            image_data = None
            
            if image_provider == "together":
                image_data = await self._generate_together_image(
                    image_prompt, width, height, seed_variation, image_model
                )
            elif image_provider == "modal_image":
                image_data = await self._generate_flux_image(
                    image_prompt, width, height, seed_variation
                )
            elif image_provider == "pollinations":
                image_data = await self._generate_pollinations_image(
                    image_prompt, width, height, seed_variation, image_model
                )
            else:
                raise ValueError(f"Unknown image provider: {image_provider}")
            
            if not image_data:
                logger.error(f"No image data generated for query: {query}")
                return None

            # Step 4: Get or upload image URL
            # Pollinations returns a dict with a pre-uploaded URL;
            # other providers return raw bytes that need S3 upload.
            import uuid
            import tempfile
            import os

            if isinstance(image_data, dict):
                image_url = image_data.get('url')
                if not image_url:
                    logger.error("Provider returned dict without 'url' key")
                    return None
                logger.info(f"Using pre-uploaded image URL: {image_url}")
            else:
                logger.info("Uploading generated image to S3...")
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                    temp_file.write(image_data)
                    temp_image_path = temp_file.name
                try:
                    image_filename = f"ai_image_{uuid.uuid4()}.png"
                    image_url = await s3_service.upload_file(temp_image_path, f"images/{image_filename}")
                finally:
                    if os.path.exists(temp_image_path):
                        os.unlink(temp_image_path)

                if not image_url:
                    logger.error("Failed to upload image to S3")
                    return None
                logger.info(f"Uploaded AI image to S3: {image_url}")

            # Step 5: Convert image to video with motion effects
            video_params = {
                'image_url': image_url,
                'video_length': duration,
                'zoom_speed': zoom_speed,
                'frame_rate': 30,
                'should_add_captions': False,
                'match_length': 'video',
                'effect_type': effect_type,
                'pan_direction': pan_direction,
                'ken_burns_keypoints': ken_burns_keypoints,
            }

            video_result = await image_to_video_service.image_to_video(video_params)

            if video_result and (video_result.get('video_url') or video_result.get('final_video_url')):
                video_url = video_result.get('video_url') or video_result.get('final_video_url')
                logger.info(f"Successfully converted AI image to video for query: {query}")
                return video_url
            else:
                logger.error("Image-to-video conversion failed: no video URL returned")
                return None
                    
        except Exception as e:
            logger.error(f"Error in AI image to video generation for query '{query}': {e}")
            return None
    
    def _get_validated_dimensions(self, orientation: str) -> tuple[int, int]:
        """Get validated dimensions for AI image generation with provider constraints."""
        
        # Together.ai constraints: height must be between 64 and 1792
        # Width constraints are similar but more flexible
        # Keep dimensions reasonable for video generation
        
        if orientation == 'portrait':
            width = 768   # Within Together.ai limits
            height = 1024 # Within Together.ai limits (64-1792)
        elif orientation == 'square':
            width = 768   # Square format
            height = 768  # Within Together.ai limits
        else:  # landscape
            width = 1024  # Standard landscape
            height = 576  # Within Together.ai limits (64-1792)
        
        # Additional validation for Together.ai
        if height < 64:
            height = 64
        elif height > 1792:
            height = 1792
        
        if width < 64:
            width = 64
        elif width > 1792:  # Together.ai also has width limits
            width = 1792
        
        logger.info(f"Using validated dimensions: {width}x{height} for orientation: {orientation}")
        return width, height
    
    async def _generate_together_image(
        self, 
        prompt: str, 
        width: int, 
        height: int, 
        seed_variation: int,
        model: Optional[str] = None
    ) -> Optional[bytes]:
        """Generate image using Together.ai service."""
        try:
            # Generate unique seed based on prompt and variation
            import hashlib
            seed_base = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
            seed = (seed_base + seed_variation) % 2147483647
            
            logger.info(f"Generating Together.ai image: {width}x{height}, seed: {seed}, model: {model}")
            
            image_data = await together_ai_service.generate_image_from_b64(
                prompt=prompt,
                width=width,
                height=height,
                steps=4,  # Fast generation
                model=model  # Pass the model parameter
            )
            
            return image_data
            
        except Exception as e:
            logger.error(f"Failed to generate image with Together.ai: {e}")
            return None
    
    async def _generate_flux_image(
        self, 
        prompt: str, 
        width: int, 
        height: int, 
        seed_variation: int
    ) -> Optional[bytes]:
        """Generate image using Flux service."""
        try:
            # Generate unique seed based on prompt and variation
            import hashlib
            seed_base = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
            seed = (seed_base + seed_variation) % 2147483647
            
            logger.info(f"Generating Modal Image: {width}x{height}, seed: {seed}")

            image_data = await modal_image_service.generate_image(
                prompt=prompt,
                width=width,
                height=height,
                seed=seed,
                num_inference_steps=4  # Fast generation
            )
            
            if image_data:
                return image_data
            else:
                logger.error("No image data returned from Flux service")
                return None
            
        except Exception as e:
            logger.error(f"Failed to generate image with Flux: {e}")
            return None
    
    async def _generate_pollinations_image(
        self,
        prompt: str,
        width: int,
        height: int,
        seed_variation: int,
        model: Optional[str] = None
    ) -> Optional[bytes]:
        """Generate image using Pollinations service."""
        try:
            # Generate unique seed based on prompt and variation
            # Pollinations requires seed <= 2^31 - 1 (2147483647)
            import hashlib
            seed_base = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
            seed = (seed_base + seed_variation) % 2147483647

            image_model = model or 'flux'
            logger.info(f"Generating Pollinations image: {width}x{height}, seed: {seed}, model: {image_model}")

            image_data = await pollinations_service.generate_image(
                prompt=prompt,
                width=width,
                height=height,
                seed=seed,
                model=image_model,
                enhance=True,
                nologo=True
            )
            
            if image_data:
                return image_data
            else:
                logger.error("No image data returned from Pollinations service")
                return None
            
        except Exception as e:
            logger.error(f"Failed to generate image with Pollinations: {e}")
            return None