import logging
from typing import Dict, Any, List, Optional
from app.services.ai.media_generation_strategy import MediaGenerationStrategy
from app.services.video.ltx_video_service import modal_video_service
from app.services.video.wavespeed_service import wavespeed_service
from app.services.pollinations.pollinations_service import pollinations_service

logger = logging.getLogger(__name__)


class AIVideoStrategy(MediaGenerationStrategy):
    """Strategy for generating video segments using AI video generation."""
    
    def get_strategy_name(self) -> str:
        return "AI Video Strategy (Modal Video/WaveSpeed)"
    
    async def generate_media_segments(
        self, 
        video_queries: List[Dict], 
        orientation: str,
        params: Dict[str, Any]
    ) -> List[Optional[Dict[str, Any]]]:
        """Generate video segments using AI video generation."""
        
        ai_video_provider = params.get('ai_video_provider', 'ltx_video')
        footage_quality = params.get('footage_quality', 'high')
        
        logger.info(f"Generating AI videos using provider: {ai_video_provider}")
        
        background_videos: List[Optional[Dict[str, Any]]] = []
        
        for i, query_data in enumerate(video_queries):
            query = query_data['query']

            try:
                video_url = await self._generate_ai_background_video(
                    query_data,  # Pass full query_data instead of just query
                    orientation,
                    footage_quality,
                    i,  # Use scene index as seed variation
                    ai_video_provider,
                    params  # Pass params to the method
                )
                
                # Validate the returned video_url
                if video_url and isinstance(video_url, str) and video_url.strip():
                    logger.info(f"Successfully generated AI video for query '{query}': {video_url}")
                    background_videos.append({
                        'download_url': video_url,
                        'start_time': query_data['start_time'],
                        'end_time': query_data['end_time'],
                        'duration': query_data['duration'],
                        'query': query,
                        'provider': f"ai_generated_{ai_video_provider}"
                    })
                else:
                    logger.warning(f"Failed to generate AI video for query: {query} - returned value: {video_url}")
                    background_videos.append(None)
                    
            except Exception as e:
                logger.error(f"Error generating AI video for query '{query}': {e}", exc_info=True)
                background_videos.append(None)
        
        return background_videos
    
    async def _generate_ai_background_video(
        self,
        query_data: dict,
        orientation: str,
        quality: str,
        seed_variation: int,
        provider: str = "ltx_video",
        params: Dict[str, Any] = None
    ) -> Optional[str]:
        """Generate AI video using specified provider with enhanced prompts."""

        try:
            # Initialize params if not provided
            if params is None:
                params = {}
            
            # Extract data from query_data
            query = query_data['query']
            duration = query_data.get('duration', 3.0)
            script_text = query_data.get('script_text', query)  # Full narration text
            semantics = query_data.get('semantics', {})  # Semantic analysis

            # Enhance the prompt with context
            enhanced_prompt = self._enhance_video_prompt(query, script_text, semantics)

            logger.info(f"Original query: {query}")
            logger.info(f"Enhanced prompt: {enhanced_prompt}")

            # Determine video dimensions
            if orientation == 'portrait':
                width, height = 720, 1280
            elif orientation == 'square':
                width, height = 720, 720
            else:  # landscape
                width, height = 1280, 720

            # Generate unique seed based on prompt and variation
            # IMPORTANT: Keep seed within int32 range (max 2147483647) for Pollinations AI compatibility
            import hashlib
            seed_base = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)
            # Use modulo to keep within int32 range
            seed = (seed_base + seed_variation) % (2**31 - 1)  # int32 max is 2147483647
            
            logger.info(f"Generating AI video: {width}x{height}, duration: {duration}s, seed: {seed} (provider: {provider})")

            if provider == "ltx_video":
                return await self._generate_modal_video(enhanced_prompt, width, height, duration, seed)
            elif provider == "wavespeed":
                return await self._generate_wavespeed_video(enhanced_prompt, width, height, duration, seed)
            elif provider == "pollinations":
                model = params.get('ai_video_model', 'veo')
                return await self._generate_pollinations_video(enhanced_prompt, width, height, duration, seed, model)
            else:
                logger.error(f"Unknown AI video provider: {provider}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating AI video for query '{query_data.get('query', 'unknown')}': {e}", exc_info=True)

    def _enhance_video_prompt(self, query: str, script_text: str, semantics: dict) -> str:
        """
        Enhance the video generation prompt with context from narration.

        Args:
            query: Original search query (2-4 words)
            script_text: Full narration text for this segment
            semantics: Semantic analysis (sentiment, domain, time context, etc.)

        Returns:
            Enhanced prompt for AI video generation
        """
        # Extract key context elements
        sentiment = semantics.get('sentiment', 'neutral')
        domain = semantics.get('domain', 'general')
        time_context = semantics.get('time_context', 'modern')

        # Build style modifiers based on sentiment
        sentiment_styles = {
            'positive': 'uplifting, bright, vibrant, optimistic',
            'negative': 'somber, muted colors, dramatic, serious',
            'neutral': 'professional, clean, balanced'
        }
        style = sentiment_styles.get(sentiment, 'professional, cinematic')

        # Build time period modifiers
        time_styles = {
            'historical': 'vintage, period-appropriate, classic',
            'modern': 'contemporary, current, present-day',
            'future': 'futuristic, advanced technology, sci-fi',
            'timeless': 'universal, classic, timeless'
        }
        time_style = time_styles.get(time_context, 'contemporary')

        # Extract key concepts from script_text if it's longer than query
        if len(script_text) > len(query) * 2:
            # Script has more context, use first 50 chars as additional context
            context_snippet = script_text[:50].strip()
            enhanced = f"{query}, {context_snippet}, {style}, {time_style}, cinematic, high quality"
        else:
            # Just use query with style enhancements
            enhanced = f"{query}, {style}, {time_style}, cinematic, high quality"

        # Ensure prompt isn't too long (video generators have limits)
        if len(enhanced) > 200:
            enhanced = enhanced[:197] + "..."

        return enhanced

    async def _generate_modal_video(
        self, 
        prompt: str, 
        width: int, 
        height: int, 
        duration: float, 
        seed: int
    ) -> Optional[str]:
        """Generate video using Modal Video service."""
        try:
            # Calculate frames from duration (assuming ~15 fps)
            num_frames = min(257, max(1, int(duration * 15)))
            
            video_data = await modal_video_service.generate_video(
                prompt=prompt,
                width=width,
                height=height,
                num_frames=num_frames,
                seed=seed
            )
            
            if video_data:
                # Upload video data to S3 and return URL
                import uuid
                import tempfile
                import os
                
                # Save video data to temporary file
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                    temp_file.write(video_data)
                    temp_video_path = temp_file.name
                
                try:
                    from app.services.s3.s3 import s3_service
                    
                    # Upload to S3
                    video_filename = f"modal_video_{uuid.uuid4()}.mp4"
                    video_url = await s3_service.upload_file(temp_video_path, f"videos/{video_filename}")
                    
                    if video_url:
                        logger.info(f"Successfully generated and uploaded LTX video for prompt: {prompt}")
                        return video_url
                    else:
                        logger.error("Failed to upload LTX video to S3")
                        return None
                        
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_video_path):
                        os.unlink(temp_video_path)
            else:
                logger.error("No video data returned from Modal Video service")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate video with Modal Video: {e}", exc_info=True)
            return None
    
    async def _generate_wavespeed_video(
        self, 
        prompt: str, 
        width: int, 
        height: int, 
        duration: float, 
        seed: int
    ) -> Optional[str]:
        """Generate video using WaveSpeed service."""
        try:
            # WaveSpeed service returns bytes directly like Modal Video
            # WaveSpeed only supports specific sizes: "832*480" (landscape) or "480*832" (portrait)
            # Map requested dimensions to nearest supported size
            if width >= height:
                # Landscape orientation
                size = "832*480"
            else:
                # Portrait orientation
                size = "480*832"
            
            duration_int = max(5, min(8, int(duration)))  # WaveSpeed supports 5-8 seconds
            
            logger.info(f"Generating WaveSpeed video: {size}, duration={duration_int}s, model=wan-2.2")
            
            video_data = await wavespeed_service.text_to_video(
                prompt=prompt,
                model="wan-2.2",  # Default model
                size=size,
                duration=duration_int,
                seed=seed if seed >= 0 else -1  # WaveSpeed uses -1 for random
            )
            
            if video_data:
                # Upload video data to S3 and return URL
                import uuid
                import tempfile
                import os
                
                # Save video data to temporary file
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                    temp_file.write(video_data)
                    temp_video_path = temp_file.name
                
                try:
                    from app.services.s3.s3 import s3_service
                    
                    # Upload to S3
                    video_filename = f"wavespeed_video_{uuid.uuid4()}.mp4"
                    video_url = await s3_service.upload_file(temp_video_path, f"videos/{video_filename}")
                    
                    if video_url:
                        logger.info(f"Successfully generated and uploaded WaveSpeed video for prompt: {prompt}")
                        return video_url
                    else:
                        logger.error("Failed to upload WaveSpeed video to S3")
                        return None
                        
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_video_path):
                        os.unlink(temp_video_path)
            else:
                logger.error("No video data returned from WaveSpeed service")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate video with WaveSpeed: {e}", exc_info=True)
            return None

    async def _generate_pollinations_video(
        self,
        prompt: str,
        width: int,
        height: int,
        duration: float,
        seed: int,
        model: str = "veo"
    ) -> Optional[str]:
        """Generate video using Pollinations AI service."""
        try:
            # Determine aspect ratio from dimensions
            if width > height:
                aspect_ratio = "16:9"
            elif width < height:
                aspect_ratio = "9:16"
            else:
                aspect_ratio = "1:1"

            # Pollinations AI VEO model only supports specific durations: [4, 6, 8]
            # Map the requested duration to the nearest supported duration
            supported_durations = [4, 6, 8]
            duration_int = int(round(duration))
            
            # Find closest supported duration
            closest_duration = min(supported_durations, key=lambda x: abs(x - duration_int))
            
            logger.info(f"Pollinations AI duration mapping: requested={duration_int}s -> using={closest_duration}s (supported: {supported_durations})")
            
            # Validate seed is within int32 range
            if seed < 0 or seed > 2147483647:
                logger.warning(f"Seed {seed} out of valid range [0, 2147483647], resetting to 0")
                seed = 0

            logger.info(f"Calling Pollinations AI generate_video with: model={model}, prompt_len={len(prompt)}, "
                       f"duration={closest_duration}s, aspect_ratio={aspect_ratio}, seed={seed}")

            # Pollinations AI returns binary video data (bytes)
            video_data = await pollinations_service.generate_video(
                prompt=prompt,
                model=model,
                duration=closest_duration,
                aspect_ratio=aspect_ratio,
                audio=False,  # We'll add audio separately
                seed=seed,
                private=True
            )

            # Validate the response
            if not video_data:
                logger.error(f"Pollinations AI generate_video returned None/empty for prompt: {prompt}")
                return None

            if not isinstance(video_data, bytes):
                logger.error(f"Pollinations AI generate_video returned unexpected type: {type(video_data)}")
                return None

            logger.info(f"Pollinations AI returned {len(video_data)} bytes of video data, uploading to S3...")

            # Save binary video data to temp file and upload to S3
            import uuid
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_file.write(video_data)
                temp_video_path = temp_file.name

            try:
                from app.services.s3.s3 import s3_service

                video_filename = f"pollinations_video_{uuid.uuid4()}.mp4"
                video_url = await s3_service.upload_file(temp_video_path, f"videos/{video_filename}")

                if video_url:
                    logger.info(f"Successfully generated and uploaded Pollinations AI video with model {model} for prompt: {prompt} -> {video_url}")
                    return video_url
                else:
                    logger.error("Failed to upload Pollinations AI video to S3")
                    return None
            finally:
                if os.path.exists(temp_video_path):
                    os.unlink(temp_video_path)

        except Exception as e:
            logger.error(f"Failed to generate video with Pollinations AI: {e}", exc_info=True)
            return None