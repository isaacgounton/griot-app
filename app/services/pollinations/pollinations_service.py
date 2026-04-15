"""
Pollinations AI Service

Integrates Pollinations AI APIs for text, image, audio, and video generation
following the official API documentation at https://pollinations.ai/docs

API Documentation: /API_DOCUMENTATION.md

All API calls go directly to the Pollinations API endpoints.
"""

import aiohttp
import logging
import os
from typing import Any

from app.services.s3.s3 import s3_service

logger = logging.getLogger(__name__)


class PollinationsError(Exception):
    """Custom exception for Pollinations AI API errors"""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class PollinationsService:
    """Service for interacting with Pollinations AI APIs

    Based on official API documentation:
    - Text: POST /v1/chat/completions
    - Image: POST /v1/images/generations
    - Audio TTS: POST /v1/audio/speech
    - Audio Transcription: POST /v1/audio/transcriptions
    - Video: POST /v1/videos/generations
    """

    def __init__(self):
        # Get configuration from environment
        self.api_key = os.environ.get("POLLINATIONS_API_KEY", "")
        # Use official Pollinations AI API by default for model discovery
        self.base_url = os.environ.get("POLLINATIONS_BASE_URL", "https://gen.pollinations.ai")
        self.default_model = os.environ.get("POLLINATIONS_MODEL", "openai")

        # Ensure URLs don't have trailing slash
        self.base_url = self.base_url.rstrip("/")

        # Timeout configuration
        self.timeout = aiohttp.ClientTimeout(
            total=600,      # 10 minutes total
            connect=30,     # 30 seconds to connect
            sock_read=120   # 2 minutes between reads
        )

        # Verify credentials
        if not self.api_key:
            logger.warning("POLLINATIONS_API_KEY not configured - API calls may fail")
        if not self.base_url:
            logger.warning("POLLINATIONS_BASE_URL not configured - using default")

        logger.info(f"Pollinations AI Service initialized - Base URL: {self.base_url}")

    def _get_headers(self) -> dict:
        """Get default headers for API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: dict | None = None,
        return_binary: bool = False,
        **kwargs
    ) -> Any:
        """Make HTTP request to Pollinations AI API"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        # Don't send Content-Type or json body on GET requests
        request_kwargs: dict[str, Any] = {"headers": headers, **kwargs}
        if method.upper() == "GET":
            headers.pop("Content-Type", None)
        else:
            request_kwargs["json"] = json_data

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                async with session.request(
                    method,
                    url,
                    **request_kwargs,
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise PollinationsError(
                            f"Pollinations AI API error: {error_text}",
                            status_code=response.status
                        )

                    if return_binary:
                        return await response.read()

                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        return await response.json()
                    else:
                        return await response.text()

            except aiohttp.ClientError as e:
                raise PollinationsError(f"Request failed: {str(e)}", status_code=503)

    async def generate_text(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        **kwargs
    ) -> str:
        """Generate text using the Pollinations /v1/chat/completions endpoint.

        Args:
            prompt: Text prompt for generation
            model: Pollinations model ID (e.g. 'openai', 'mistral', 'qwen-vision')
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens to generate
        """
        return await self.generate_text_chat(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    async def generate_text_chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        **kwargs
    ) -> str:
        """Generate chat response using the Pollinations /v1/chat/completions endpoint directly.

        Pollinations model IDs (e.g. 'openai', 'mistral', 'qwen-vision') are NOT
        anyllm provider names, so this method calls the Pollinations API directly
        rather than routing through anyllm.

        Args:
            messages: Array of message objects with role and content
            model: Pollinations model ID (default: service default model)
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens to generate
        """
        resolved_model = model or self.default_model

        payload: dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        try:
            data = await self._make_request("POST", "/v1/chat/completions", json_data=payload)

            # OpenAI-compatible response shape
            content = (
                data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content")
            )
            if not content:
                raise PollinationsError("Empty response from Pollinations API")

            return content

        except PollinationsError:
            raise
        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
            raise PollinationsError(str(e))

    async def generate_image(
        self,
        prompt: str,
        model: str = "flux",
        size: str | None = None,
        width: int | None = None,
        height: int | None = None,
        quality: str | None = None,
        seed: int | None = None,
        nologo: bool = True,
        nofeed: bool = True,
        private: bool = False,
        enhance: bool = False,
        negative_prompt: str | None = None,
        image: str | None = None,
        **kwargs
    ) -> dict:
        """Generate image using Pollinations AI.

        Endpoint: GET /image/{prompt}  (returns binary image data)

        Args:
            prompt: Text description of image (max 32,000 chars)
            model: Model ID (flux, kontext, gptimage, seedream, nanobanana, etc.)
            size: Image size as string (256x256, 512x512, 1024x1024)
            width: Custom width (1-2048)
            height: Custom height (1-2048)
            quality: Image quality (low, medium, high, hd) — gptimage only
            seed: Seed for reproducible results (-1 for random)
            nologo: Remove Pollinations logo
            nofeed: Don't add to public feed
            private: Mark image as private
            enhance: Enhance image quality with AI prompt improvement
            negative_prompt: What to avoid in the image
            guidance_scale: How closely to follow prompt (1-20)
            response_format: Response format (url or b64_json)
            image: Reference image URL for img2img editing
            **kwargs: Additional parameters

        Returns:
            dict with 'url' key containing the uploaded image URL
        """
        import urllib.parse

        # Sanitize prompt for URL: replace % with 'percent' to avoid 400 errors
        safe_prompt = prompt.replace("%", "percent")
        encoded_prompt = urllib.parse.quote(safe_prompt, safe="")

        # Build query parameters
        params: dict[str, str] = {"model": model}

        # Dimensions
        if size:
            parts = size.split("x")
            if len(parts) == 2:
                params["width"] = parts[0]
                params["height"] = parts[1]
        else:
            if width:
                params["width"] = str(width)
            if height:
                params["height"] = str(height)

        # Optional parameters
        if seed is not None and seed != -1:
            params["seed"] = str(seed)
        if negative_prompt:
            params["negative_prompt"] = negative_prompt
        if quality:
            params["quality"] = quality
        if image:
            params["image"] = image

        # Boolean parameters
        if nologo:
            params["nologo"] = "true"
        if nofeed:
            params["nofeed"] = "true"
        if private:
            params["private"] = "true"
        if enhance:
            params["enhance"] = "true"

        # Additional kwargs
        for key, value in kwargs.items():
            if value is not None:
                params[key] = str(value)

        # Pass API key as query param (more reliable for GET image endpoint)
        if self.api_key:
            params["key"] = self.api_key

        query_string = urllib.parse.urlencode(params)
        endpoint = f"/image/{encoded_prompt}?{query_string}"

        try:
            # GET request returns binary image data
            image_bytes = await self._make_request("GET", endpoint, return_binary=True)

            if not image_bytes or len(image_bytes) < 100:
                raise PollinationsError("Empty or invalid image response from Pollinations AI")

            # Upload to S3 to get a stable URL
            if s3_service:
                import tempfile
                import uuid as _uuid
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(image_bytes)
                    tmp_path = tmp.name
                try:
                    s3_key = f"pollinations/generated/{_uuid.uuid4()}.png"
                    url = await s3_service.upload_file_with_metadata(
                        tmp_path, s3_key, content_type="image/png", public=True
                    )
                    image_url = url["file_url"]
                finally:
                    import os as _os
                    if _os.path.exists(tmp_path):
                        _os.unlink(tmp_path)
                return {"url": image_url}

            # Fallback: return base64
            import base64
            b64 = base64.b64encode(image_bytes).decode()
            return {"b64_json": b64}

        except PollinationsError as e:
            logger.error(f"Image generation failed: {e}")
            raise

    async def edit_image(
        self,
        image_bytes: bytes,
        prompt: str,
        model: str = "kontext",
        seed: int | None = None,
        negative_prompt: str | None = None,
    ) -> bytes:
        """Edit an image using Pollinations AI (image-to-image).

        Uses GET /image/{prompt}?model={model}&image={url} which returns binary data.
        Models that support editing: kontext, nanobanana, seedream, klein.

        Args:
            image_bytes: Original image data as bytes
            prompt: Text description of desired edits
            model: Model to use for editing (kontext, nanobanana, seedream, klein, etc.)
            seed: Optional seed for reproducible results

        Returns:
            bytes: Edited image data
        """
        if not s3_service:
            raise PollinationsError("S3 service not available - cannot edit image")

        import tempfile
        import uuid

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_file.write(image_bytes)
            temp_path = temp_file.name

        try:
            # Upload original to S3 so Pollinations can access it via URL
            s3_key = f"pollinations/temp/{uuid.uuid4()}.png"
            upload_result = await s3_service.upload_file_with_metadata(
                temp_path, s3_key, content_type="image/png", public=True
            )
            image_url = upload_result["file_url"]

            # Use generate_image with the image param — returns dict with 'url'
            result = await self.generate_image(
                prompt=prompt,
                model=model,
                image=image_url,
                seed=seed,
                negative_prompt=negative_prompt,
                nologo=True,
                nofeed=True,
            )

            # generate_image now uploads to S3 and returns {"url": ...}
            if "url" in result:
                async with aiohttp.ClientSession() as session:
                    async with session.get(result["url"]) as resp:
                        if resp.status == 200:
                            return await resp.read()
                        raise PollinationsError(f"Failed to download edited image: {resp.status}")

            # If b64_json was returned (no S3)
            if "b64_json" in result:
                import base64
                return base64.b64decode(result["b64_json"])

            raise PollinationsError("No image data in generation response")

        finally:
            import os
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def generate_audio_tts(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "openai-audio",
        response_format: str = "mp3",
        speed: float = 1.0,
        return_url: bool = True,
        **kwargs
    ) -> str | bytes | None:
        """Generate audio/speech using Pollinations' dedicated audio endpoint.

        Endpoint: GET /audio/{text}

        Args:
            text: Text to speak
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer, etc.)
            model: Model to use (must be "openai-audio")
            response_format: Audio format (mp3, opus, aac, flac)
            speed: Speech speed (0.25 - 4.0)
            return_url: If True, return URL; if False, return binary audio
            **kwargs: Additional parameters

        Returns:
            str (URL) if return_url=True, bytes (audio data) if return_url=False
        """
        import uuid as _uuid
        from urllib.parse import quote, urlencode

        query_params: dict[str, Any] = {
            "voice": voice,
            "response_format": response_format,
        }
        if model:
            query_params["model"] = model
        if speed != 1.0:
            query_params["speed"] = speed

        for key, value in kwargs.items():
            if value is not None:
                query_params[key] = value

        endpoint = f"/audio/{quote(text, safe='')}?{urlencode(query_params)}"

        try:
            audio_data = await self._make_request("GET", endpoint, return_binary=True)
            if not audio_data:
                raise PollinationsError("Empty audio response from Pollinations AI")

            if not return_url:
                return audio_data

            ext = (response_format or "mp3").lower()
            content_type = {
                "mp3": "audio/mpeg",
                "wav": "audio/wav",
                "flac": "audio/flac",
                "opus": "audio/opus",
                "pcm": "audio/pcm",
                "aac": "audio/aac",
            }.get(ext, f"audio/{ext}")
            filename = f"pollinations_tts_{_uuid.uuid4().hex}.{ext}"
            content_url = await self.save_generated_content_to_s3(audio_data, filename, content_type)
            if content_url:
                return content_url

            logger.warning("S3 upload unavailable for Pollinations TTS; returning raw bytes")
            return audio_data
        except PollinationsError as e:
            logger.error(f"Audio TTS generation failed: {e}")
            raise

    async def transcribe_audio(
        self,
        audio_data: bytes,
        filename: str = "audio.mp3",
        model: str = "openai-audio",
        language: str | None = None,
        prompt: str | None = None,
        response_format: str = "json",
        temperature: float = 0.0,
        **kwargs
    ) -> dict:
        """Transcribe audio using Pollinations.

        Endpoint: POST /v1/audio/transcriptions

        Args:
            audio_data: Binary audio data
            filename: Original filename
            model: Model to use (default: "openai-audio")
            language: Language code (e.g., "en")
            prompt: Optional prompt for transcription
            response_format: Response format (json, text, srt, verbose_json, vtt)
            temperature: Sampling temperature (0.0 - 1.0)
            **kwargs: Additional parameters

        Returns:
            dict with transcription results
        """
        try:
            # For file uploads, we need to use multipart form data
            data = aiohttp.FormData()
            data.add_field("file", audio_data, filename=filename)
            data.add_field("model", model)

            if language:
                data.add_field("language", language)
            if prompt:
                data.add_field("prompt", prompt)
            if response_format:
                data.add_field("response_format", response_format)
            if temperature != 0.0:
                data.add_field("temperature", str(temperature))

            # Add any additional parameters
            for key, value in kwargs.items():
                if value is not None:
                    data.add_field(key, str(value))

            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/v1/audio/transcriptions",
                    data=data,
                    headers=headers
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise PollinationsError(
                            f"Pollinations audio transcription error: {error_text}",
                            status_code=response.status
                        )

                    return await response.json()

        except PollinationsError as e:
            logger.error(f"Transcription failed: {e}")
            raise

    async def generate_video(
        self,
        prompt: str,
        model: str = "veo",
        duration: int | None = None,
        aspect_ratio: str | None = None,
        audio: bool = False,
        seed: int | None = None,
        negative_prompt: str | None = None,
        width: int | None = None,
        height: int | None = None,
        image_url: str | None = None,
        private: bool = True,
        **kwargs
    ) -> bytes:
        """Generate video using Pollinations AI.

        Uses the dedicated GET /video/{prompt} endpoint, matching the current
        Pollinations public API and the n8n node implementation.

        Args:
            prompt: Text description of video
            model: Video model (veo, seedance, seedance-pro, wan, etc.)
            duration: Video duration in seconds
            aspect_ratio: Aspect ratio (16:9, 9:16, 1:1)
            audio: Enable audio generation
            seed: Seed for reproducible results
            negative_prompt: What to avoid in video
            width: Video width in pixels
            height: Video height in pixels
            image_url: Source image URL for image-to-video
            private: Mark as private
            **kwargs: Additional query parameters
        """
        from urllib.parse import quote, urlencode

        # Build query parameters (matching the n8n implementation)
        params: dict[str, Any] = {"model": model}
        if duration is not None:
            params["duration"] = duration
        if aspect_ratio:
            params["aspectRatio"] = aspect_ratio
        if audio:
            params["audio"] = "true"
        if seed is not None:
            params["seed"] = seed
        if negative_prompt:
            params["negative_prompt"] = negative_prompt
        if width:
            params["width"] = width
        if height:
            params["height"] = height
        if image_url:
            params["image"] = image_url
        for key, value in kwargs.items():
            if value is not None:
                params[key] = value

        encoded_prompt = quote(prompt, safe="")
        query_string = urlencode(params)
        url = f"{self.base_url}/video/{encoded_prompt}?{query_string}"

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            # Video generation uses a long timeout
            timeout = aiohttp.ClientTimeout(total=600, connect=30, sock_read=300)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise PollinationsError(
                            f"Pollinations video generation error: {error_text}",
                            status_code=response.status
                        )
                    return await response.read()
        except PollinationsError:
            raise
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            raise PollinationsError(f"Video generation failed: {str(e)}")

    async def save_generated_content_to_s3(
        self,
        content: bytes,
        filename: str,
        content_type: str = "application/octet-stream"
    ) -> str | None:
        """Save generated content to S3"""
        if not s3_service:
            logger.warning("S3 service not available - cannot save generated content")
            return None

        try:
            # Create temporary file
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name

            try:
                from datetime import datetime
                s3_key = f"pollinations/{datetime.now().strftime('%Y/%m/%d')}/{filename}"
                result = await s3_service.upload_file_with_metadata(
                    temp_path,
                    s3_key,
                    content_type=content_type,
                    public=True
                )
                logger.info(f"Content saved to S3: {result['file_url']}")
                return result["file_url"]
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
        except Exception as e:
            logger.error(f"Failed to save content to S3: {e}")
            return None

    async def list_image_models(self) -> list[str]:
        """List available image generation models from Pollinations AI.

        Endpoint: GET /image/models
        Filters out video models (only returns models with 'image' in output_modalities).
        """
        try:
            data = await self._make_request("GET", "/image/models")
            models = data if isinstance(data, list) else data.get("models", data.get("data", []))

            model_names = []
            for m in models:
                if isinstance(m, dict) and "name" in m:
                    outputs = m.get("output_modalities", [])
                    # Only include models that output images (not video)
                    if "video" not in outputs:
                        model_names.append(m["name"])
                elif isinstance(m, str):
                    model_names.append(m)

            return model_names if model_names else ["flux", "nanobanana", "turbo"]
        except Exception as e:
            logger.warning(f"Failed to fetch image models from Pollinations AI: {e}")
            return ["flux", "nanobanana", "turbo"]

    async def list_image_edit_models(self) -> list[dict[str, Any]]:
        """List image models that support editing (image input + image output).

        Filters /image/models for models with 'image' in both input_modalities
        and output_modalities (excludes video models).
        """
        try:
            data = await self._make_request("GET", "/image/models")
            models = data if isinstance(data, list) else data.get("models", data.get("data", []))

            # Models known to be broken for image editing on Pollinations
            broken_edit_models = {"gptimage", "gptimage-large"}

            edit_models = []
            for m in models:
                if not isinstance(m, dict):
                    continue
                name = m.get("name", "")
                if name in broken_edit_models:
                    continue
                inputs = m.get("input_modalities", [])
                outputs = m.get("output_modalities", [])
                # Must accept image input AND produce image output (not video)
                if "image" in inputs and "image" in outputs and "video" not in outputs:
                    edit_models.append({
                        "name": name,
                        "description": m.get("description", ""),
                    })

            return edit_models if edit_models else [
                {"name": "kontext", "description": "FLUX.1 Kontext - In-context editing"},
            ]
        except Exception as e:
            logger.warning(f"Failed to fetch image edit models: {e}")
            return [
                {"name": "kontext", "description": "FLUX.1 Kontext - In-context editing"},
            ]

    async def list_text_models(self) -> dict[str, Any]:
        """List available text generation models and voices from Pollinations AI

        Endpoint: GET /text/models or GET /v1/models
        """
        try:
            # Try official Pollinations AI API
            data = await self._make_request("GET", "/text/models")
            
            # If it's a list response from the API, convert to dict format
            if isinstance(data, list):
                # Extract model names from list of model objects
                model_names = []
                for item in data:
                    if isinstance(item, dict):
                        if "name" in item:
                            model_names.append(item["name"])
                    elif isinstance(item, str):
                        model_names.append(item)
                
                return {
                    "text_models": model_names if model_names else ["openai", "claude", "gemini"],
                    "voices": [
                        {"name": "alloy", "description": "Balanced voice"},
                        {"name": "echo", "description": "Clear voice"},
                        {"name": "fable", "description": "Expressive voice"},
                        {"name": "onyx", "description": "Deep voice"},
                        {"name": "nova", "description": "Bright voice"},
                        {"name": "shimmer", "description": "Gentle voice"}
                    ]
                }
            elif isinstance(data, dict):
                # Already in correct format or close to it
                if "text_models" not in data and "models" in data:
                    data["text_models"] = data.pop("models")
                if "voices" not in data:
                    data["voices"] = [
                        {"name": "alloy", "description": "Balanced voice"},
                        {"name": "echo", "description": "Clear voice"},
                        {"name": "fable", "description": "Expressive voice"},
                        {"name": "onyx", "description": "Deep voice"},
                        {"name": "nova", "description": "Bright voice"},
                        {"name": "shimmer", "description": "Gentle voice"}
                    ]
                return data
                
            # Fallback to defaults
            return {
                "text_models": ["openai", "openai-fast", "openai-large", "claude", "claude-fast", "gemini", "deepseek"],
                "voices": [
                    {"name": "alloy", "description": "Balanced voice"},
                    {"name": "echo", "description": "Clear voice"},
                    {"name": "fable", "description": "Expressive voice"},
                    {"name": "onyx", "description": "Deep voice"},
                    {"name": "nova", "description": "Bright voice"},
                    {"name": "shimmer", "description": "Gentle voice"}
                ]
            }
        except Exception as e:
            logger.warning(f"Failed to fetch text models from Griot AI: {e}")
            # Return sensible defaults based on API documentation
            return {
                "text_models": ["openai", "openai-fast", "openai-large", "claude", "claude-fast", "gemini", "deepseek"],
                "voices": [
                    {"name": "alloy", "description": "Balanced voice"},
                    {"name": "echo", "description": "Clear voice"},
                    {"name": "fable", "description": "Expressive voice"},
                    {"name": "onyx", "description": "Deep voice"},
                    {"name": "nova", "description": "Bright voice"},
                    {"name": "shimmer", "description": "Gentle voice"}
                ]
            }

    async def list_video_models(self) -> list[dict[str, Any]]:
        """List available video generation models from Pollinations AI.

        Fetches all models from GET /image/models and filters to those
        with 'video' in their output_modalities (matching the n8n pattern).
        """
        fallback = [
            {"name": "veo", "description": "Veo - Google video generation", "paid_only": True},
            {"name": "seedance", "description": "Seedance Lite - BytePlus video generation"},
            {"name": "seedance-pro", "description": "Seedance Pro - BytePlus video generation", "paid_only": True},
            {"name": "wan", "description": "Wan 2.6 - Alibaba video generation with audio"},
        ]
        try:
            data = await self._make_request("GET", "/image/models")

            if not isinstance(data, list):
                logger.warning(f"Unexpected /image/models response format: {type(data)}")
                return fallback

            video_models = []
            for model in data:
                if not isinstance(model, dict):
                    continue
                output_mods = model.get("output_modalities", [])
                if "video" in output_mods:
                    video_models.append({
                        "name": model.get("name", "unknown"),
                        "description": model.get("description", ""),
                        "input_modalities": model.get("input_modalities", []),
                        "paid_only": model.get("paid_only", False),
                    })

            return video_models if video_models else fallback
        except Exception as e:
            logger.warning(f"Failed to fetch video models from Pollinations AI: {e}")
            return fallback

    async def list_audio_models(self) -> list[str]:
        """List available audio/speech models from Griot AI

        Endpoint: GET /v1/audio/models
        """
        try:
            data = await self._make_request("GET", "/v1/audio/models")

            # Handle various response formats
            if isinstance(data, dict) and "models" in data and isinstance(data["models"], list):
                models_list = data["models"]
                # Extract model names from model objects
                model_names = []
                for model in models_list:
                    if isinstance(model, dict) and "name" in model:
                        model_names.append(model["name"])
                    elif isinstance(model, str):
                        model_names.append(model)
                
                return model_names if model_names else ["openai-audio"]
            elif isinstance(data, list):
                # If it's already a list, extract names if they're objects
                model_names = []
                for model in data:
                    if isinstance(model, dict) and "name" in model:
                        model_names.append(model["name"])
                    elif isinstance(model, str):
                        model_names.append(model)
                
                return model_names if model_names else ["openai-audio"]
            elif isinstance(data, dict):
                if "data" in data and isinstance(data["data"], list):
                    # Handle nested data format
                    model_names = []
                    for model in data["data"]:
                        if isinstance(model, dict) and "name" in model:
                            model_names.append(model["name"])
                        elif isinstance(model, str):
                            model_names.append(model)
                    
                    return model_names if model_names else ["openai-audio"]
                # Return keys if it's a dict of models
                return list(data.keys())

            logger.warning(f"Unexpected audio models response format: {type(data)}")
            return ["openai-audio"]
        except Exception as e:
            logger.warning(f"Failed to fetch audio models from Pollinations AI: {e}")
            # Return sensible defaults based on API documentation
            return ["openai-audio"]


# Create singleton instance
pollinations_service = PollinationsService()
