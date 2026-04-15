"""
Media Agent Tools

Provides the Media Agent with executable tools for media operations:
- Script generation
- Text-to-speech audio creation
- AI image generation  
- Video creation and editing
- Audio mixing and music
- Captioning
- Social media posting

These tools guide users through workflow steps and provide status updates.
For actual processing, the agent directs users to the appropriate API endpoints.
"""

import logging
import os
import time
from typing import Dict, Any, Optional, List, Tuple

import requests

from app.utils.auth import API_KEY as APP_API_KEY

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal API helpers
# ---------------------------------------------------------------------------

def _get_protocol_aware_base_url() -> str:
    """Get protocol-aware base URL for internal API calls."""
    configured_url = os.getenv("AGENT_INTERNAL_API_BASE_URL")

    if configured_url:
        # Use configured URL but ensure HTTPS in production
        if configured_url.startswith('http://') and os.getenv('NODE_ENV') == 'production':
            return configured_url.replace('http://', 'https://')
        return configured_url
    else:
        # Default: use environment-aware defaults
        if os.getenv('NODE_ENV') == 'production':
            return 'https://griot.ai/api/v1'
        return 'http://127.0.0.1:8000/api/v1'

INTERNAL_API_BASE_URL = _get_protocol_aware_base_url()
INTERNAL_API_ENABLED = bool(INTERNAL_API_BASE_URL)


def _get_internal_api_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Create request headers for internal API calls."""
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("API_KEY") or APP_API_KEY
    if api_key:
        headers["X-API-Key"] = api_key
    if extra:
        headers.update(extra)
    return headers


def _post_internal(endpoint: str, payload: Dict[str, Any], timeout: float = 30.0) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """POST helper for internal API calls."""
    if not INTERNAL_API_ENABLED:
        return False, None, "Internal API base URL is not configured."

    url = f"{INTERNAL_API_BASE_URL}{endpoint}"
    try:
        response = requests.post(url, json=payload, headers=_get_internal_api_headers(), timeout=timeout)
        response.raise_for_status()
        return True, response.json(), None
    except requests.RequestException as exc:
        logger.warning("Internal API POST %s failed: %s", endpoint, exc)
        return False, None, str(exc)


def _get_internal(endpoint: str, timeout: float = 15.0) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """GET helper for internal API calls."""
    if not INTERNAL_API_ENABLED:
        return False, None, "Internal API base URL is not configured."

    url = f"{INTERNAL_API_BASE_URL}{endpoint}"
    try:
        response = requests.get(url, headers=_get_internal_api_headers(), timeout=timeout)
        response.raise_for_status()
        return True, response.json(), None
    except requests.RequestException as exc:
        logger.warning("Internal API GET %s failed: %s", endpoint, exc)
        return False, None, str(exc)


def _poll_job_until_complete(job_id: str, timeout: float = 180.0, interval: float = 5.0) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Poll the job status endpoint until completion or timeout.

    Returns:
        (job_data, error_message)
    """
    start_time = time.time()
    while time.time() - start_time <= timeout:
        ok, payload, error = _get_internal(f"/jobs/{job_id}/status")
        if not ok or not payload:
            return None, error or "Unable to retrieve job status."

        job_data = payload.get("data") or {}
        status = (job_data.get("status") or "").lower()

        if status in {"completed", "success"}:
            return job_data, None
        if status in {"failed", "error"}:
            job_error = job_data.get("error") or error or "Job reported failure."
            return None, str(job_error)

        time.sleep(interval)

    return None, "Job polling timed out before completion."


def _fetch_postiz_integrations() -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Fetch Postiz integrations from the internal API."""
    ok, payload, error = _get_internal("/postiz/integrations")
    if not ok or payload is None:
        return None, error or "Unable to load Postiz integrations."

    integrations: Optional[List[Dict[str, Any]]] = None
    if isinstance(payload, list):
        integrations = payload
    elif isinstance(payload, dict):
        maybe_list = payload.get("data")
        if isinstance(maybe_list, list):
            integrations = maybe_list

    if integrations is None:
        return None, "Unexpected response when loading Postiz integrations."

    return integrations, None


def _normalize_identifier(value: str) -> str:
    """Normalize identifiers for comparison (lowercase alphanumeric)."""
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _resolve_postiz_integrations(
    platforms: List[str],
) -> Tuple[List[str], List[Dict[str, Any]], List[str], Optional[str]]:
    """
    Resolve user-supplied platform names to Postiz integration IDs.

    Returns:
        (integration_ids, integration_metadata, missing_platforms, error_message)
    """
    integrations, error = _fetch_postiz_integrations()
    if integrations is None:
        return [], [], platforms, error

    id_lookup: Dict[str, Dict[str, Any]] = {
        item["id"]: item for item in integrations if isinstance(item, dict) and item.get("id")
    }

    resolved_ids: List[str] = []
    resolved_meta: List[Dict[str, Any]] = []
    missing: List[str] = []

    for platform in platforms:
        if not platform:
            continue
        candidate = platform.strip()
        if not candidate:
            continue

        lowered = candidate.lower()
        normalized = _normalize_identifier(candidate)

        matched_integration: Optional[Dict[str, Any]] = None

        # Direct ID match
        for integration_id, integration in id_lookup.items():
            if lowered == integration_id.lower():
                matched_integration = integration
                break

        # Support prefixes like "integration:ID" or "postiz:ID"
        if matched_integration is None and ":" in lowered:
            _, suffix = lowered.split(":", 1)
            for integration_id, integration in id_lookup.items():
                if suffix == integration_id.lower():
                    matched_integration = integration
                    break

        # Match against provider or name
        if matched_integration is None:
            for integration in integrations:
                provider = _normalize_identifier(str(integration.get("provider", "")))
                name = _normalize_identifier(str(integration.get("name", "")))
                if normalized in {provider, name} and integration.get("id"):
                    matched_integration = integration
                    break

        if matched_integration:
            resolved_ids.append(matched_integration["id"])
            resolved_meta.append(matched_integration)
        else:
            missing.append(candidate)

    if not resolved_ids:
        return [], [], missing, "No matching Postiz integrations were found."

    return resolved_ids, resolved_meta, missing, None


# ============================================================================
# TOOL 1: Generate Script
# ============================================================================

def generate_script(
    topic: str,
    script_type: str = "facts",
    language: str = "english",
    max_duration: int = 60,
) -> Dict[str, Any]:
    """
    Guide script generation from a topic.
    
    Creates engaging video scripts for various styles (facts, story, educational).
    Supports 30+ languages.
    
    Args:
        topic: The topic or subject for the script
        script_type: Type of script ('facts', 'story', 'educational', 'motivational')
        language: Output language (default: 'english')
        max_duration: Maximum script duration in seconds
    
    Returns:
        {
            "success": bool,
            "message": str,
            "next_step": str,
            "api_endpoint": str,
            "estimated_duration": int,
        }
    
    Example:
        generate_script(
            topic="Amazing facts about the ocean",
            script_type="facts",
            max_duration=30
        )
    """
    try:
        estimated_words = max(200, int(max_duration * 2.8))  # ~2.8 words per second
        
        return {
            "success": True,
            "message": f"Ready to generate script: '{topic}' ({script_type} style, {language}, ~{max_duration}s)",
            "next_step": f"POST /api/text/script with topic='{topic}', script_type='{script_type}', language='{language}'",
            "api_endpoint": "/api/text/script",
            "estimated_words": estimated_words,
            "estimated_duration": max_duration,
            "language": language,
            "script_type": script_type,
        }
    except Exception as e:
        logger.error(f"Script guidance failed: {str(e)}")
        return {
            "success": False,
            "error": f"Script generation guidance failed: {str(e)}",
        }


# ============================================================================
# TOOL 2: Generate TTS Audio
# ============================================================================

def generate_tts_audio(
    text: str,
    language: str = "en-us",
    voice: Optional[str] = None,
    speed: float = 1.0,
    poll: bool = True,
    poll_timeout: float = 120.0,
    poll_interval: float = 3.0,
) -> Dict[str, Any]:
    """
    Convert text to speech audio. Returns an S3 URL to the generated audio file.

    Generates natural-sounding voice narration with multiple voice options
    and language support.

    Args:
        text: Text to convert to speech
        language: Language code ('en-us', 'es', 'fr', 'hi', 'it', 'pt', 'ja', 'zh')
        voice: Specific voice ID (optional, defaults to 'af_heart')
        speed: Speech speed (0.5 = 50% slower, 2.0 = 2x faster)
        poll: When True, poll job until completion before returning
        poll_timeout: Maximum seconds to wait while polling
        poll_interval: Delay between polling attempts in seconds

    Returns:
        {
            "success": bool,
            "message": str,
            "audio_url": str,  # S3 URL to generated audio
        }

    Example:
        generate_tts_audio(
            text="Welcome to our amazing video",
            language="en-us",
            voice="af_bella"
        )
    """
    try:
        text_preview = text[:100] + "..." if len(text) > 100 else text
        voice_name = voice or "af_heart"

        api_parameters: Dict[str, Any] = {
            "text": text,
            "voice": voice_name,
            "provider": "kokoro",
            "speed": speed,
        }

        success, response_payload, error = _post_internal("/audio/speech", api_parameters)

        if not success or not response_payload:
            message = (
                f"Ready to generate TTS audio: voice {voice_name}, speed {speed}x. "
                f"Submit parameters to /api/v1/audio/speech to start the job."
            )
            if error:
                message += f" (Note: automatic execution unavailable: {error})"
            return {
                "success": True,
                "message": message,
                "text_preview": text_preview,
                "api_endpoint": "/api/v1/audio/speech",
                "parameters": api_parameters,
            }

        # Check for immediate sync result
        immediate_result = response_payload.get("result")
        if isinstance(immediate_result, dict) and immediate_result.get("audio_url"):
            return {
                "success": True,
                "message": f"Audio generated successfully using voice {voice_name}.",
                "text_preview": text_preview,
                "audio_url": immediate_result["audio_url"],
                "details": immediate_result,
            }

        job_id = response_payload.get("job_id")
        if not job_id:
            return {
                "success": False,
                "message": "TTS request did not return a job ID or audio URL.",
                "details": response_payload,
                "text_preview": text_preview,
            }

        if poll:
            job_data, poll_error = _poll_job_until_complete(job_id, timeout=poll_timeout, interval=poll_interval)
            if job_data and not poll_error:
                result_payload = job_data.get("result") or {}
                audio_url = result_payload.get("audio_url")
                message = f"Audio generated successfully using voice {voice_name}."
                if audio_url:
                    message += f" Download: {audio_url}"
                return {
                    "success": True,
                    "message": message,
                    "text_preview": text_preview,
                    "audio_url": audio_url,
                    "job_id": job_id,
                    "details": result_payload,
                }
            if poll_error:
                return {
                    "success": False,
                    "message": f"TTS job failed: {poll_error}",
                    "job_id": job_id,
                    "text_preview": text_preview,
                }

        return {
            "success": True,
            "message": f"TTS job {job_id} started. Poll /api/v1/jobs/{job_id}/status for result.",
            "text_preview": text_preview,
            "job_id": job_id,
        }
    except Exception as e:
        logger.error(f"TTS generation failed: {str(e)}")
        return {
            "success": False,
            "error": f"TTS generation failed: {str(e)}",
        }


# ============================================================================
# TOOL 3: Get Available Voices
# ============================================================================

def get_available_voices(provider: str = "kokoro") -> Dict[str, Any]:
    """
    Get list of available TTS voices.
    
    Returns all supported voices, languages, and their IDs for use
    in generate_tts_audio().
    
    Returns:
        {
            "success": bool,
            "voices_by_language": dict,
            "languages": [str],
        }
    
    Example:
        voices = get_available_voices()
    """
    try:
        # TTS voice configuration
        voices_config = {
            "en-us": [
                "af_heart", "af_alloy", "af_aoede", "af_bella", "af_jessica",
                "af_kore", "af_nicole", "af_nova", "af_river", "af_sarah",
                "af_sky", "am_adam", "am_echo", "am_eric", "am_fenrir",
                "am_liam", "am_michael", "am_onyx", "am_puck", "bm_george",
                "bm_lewis"
            ],
            "en-gb": [
                "bf_alan", "bf_isla", "bm_daniel", "bm_fable", "bm_griffin",
                "bm_hal", "bm_james", "bm_luke", "bm_male", "bm_santa"
            ],
            "es": ["em_alex", "ef_dora", "em_santa"],
            "fr": ["ff_siwis", "fm_alan", "fm_santa"],
            "hi": ["hf_alpha", "hf_beta", "hm_omega", "hm_santa"],
            "it": ["if_sara", "im_nicola", "im_santa"],
            "pt": ["pf_dora", "pm_alex", "pm_santa"],
            "ja": ["jf_alpha", "jf_gongitsune", "jf_nezumi", "jf_tebukuro", "jm_santa"],
            "zh": ["zf_xiaoxiao", "zf_xiaoyi", "zm_yunjian", "zm_yunxi", "zm_yunxia", "zm_yunyang"]
        }
        
        return {
            "success": True,
            "voices_by_language": voices_config,
            "languages": list(voices_config.keys()),
            "provider": provider,
            "voice_count": sum(len(v) for v in voices_config.values()),
        }
    except Exception as e:
        logger.error(f"Voice retrieval failed: {str(e)}")
        return {
            "success": False,
            "error": f"Voice retrieval failed: {str(e)}",
        }


# ============================================================================
# TOOL 4: Generate Image
# ============================================================================

def generate_image(
    prompt: str,
    model: str = "modal_image",
    width: int = 1024,
    height: int = 1024,
    seed: Optional[int] = None,
    provider: Optional[str] = None,
    steps: Optional[int] = None,
    sync: bool = False,
    poll: bool = True,
    poll_timeout: float = 180.0,
    poll_interval: float = 5.0,
) -> Dict[str, Any]:
    """
    Generate an AI image from a text prompt.
    
    Creates custom visuals using text descriptions with multiple AI models.
    
    Args:
        prompt: Text description of the image to generate
        model: AI model identifier or shorthand ('modal_image', 'kontext', 'dall-e-3', etc.)
        width: Image width in pixels (512, 768, 1024, 1280)
        height: Image height in pixels
        seed: Seed for reproducible results (optional)
        provider: Optional provider override ('modal_image', 'together', etc.)
        steps: Optional number of inference steps
        sync: When True, wait for the API's synchronous response instead of creating a job
        poll: When True, poll the job endpoint until completion before returning
        poll_timeout: Maximum seconds to wait while polling
        poll_interval: Delay between polling attempts in seconds
    
    Returns:
        {
            "success": bool,
            "message": str,
            "api_endpoint": str,
            "parameters": dict,
        }
    
    Example:
        generate_image(
            prompt="Beautiful ocean sunset with dolphins",
            model="modal_image",
            width=1024,
            height=1024
        )
    """
    try:
        prompt_preview = prompt[:80] + "..." if len(prompt) > 80 else prompt

        normalized_model = (model or "").strip()
        normalized_provider = (provider or "").strip().lower()

        if not normalized_provider:
            if "/" in normalized_model:
                normalized_provider = "modal_image" if "modal_image" in normalized_model.lower() else "together"
            elif normalized_model.lower() in {"modal_image", "flux.1-schnell", "flux_schnell"}:
                normalized_provider = "together"
                normalized_model = "black-forest-labs/FLUX.1-schnell"
            else:
                normalized_provider = "together"
        else:
            if normalized_provider == "together" and normalized_model.lower() in {"flux.1-schnell", "flux_schnell"}:
                normalized_model = "black-forest-labs/FLUX.1-schnell"

        api_parameters = {
            "prompt": prompt,
            "model": normalized_model,
            "width": width,
            "height": height,
            "provider": normalized_provider,
            "sync": sync,
        }

        if steps is not None:
            api_parameters["steps"] = steps
        if seed is not None:
            api_parameters["seed"] = seed

        # Attempt to call internal API when available
        success, response_payload, error = _post_internal("/images/generate", api_parameters)

        if not success or not response_payload:
            message = (
                f"Ready to generate image via API: {normalized_model} ({normalized_provider}), {width}x{height}. "
                f"Submit parameters to /api/v1/images/generate to start the job."
            )
            if error:
                message += f" (Note: automatic job execution unavailable: {error})"
            return {
                "success": True,
                "message": message,
                "prompt_preview": prompt_preview,
                "api_endpoint": "/api/v1/images/generate",
                "parameters": api_parameters,
            }

        job_id = response_payload.get("job_id")
        immediate_url = response_payload.get("image_url")

        if immediate_url:
            return {
                "success": True,
                "message": f"Image generated successfully using {normalized_model}.",
                "prompt_preview": prompt_preview,
                "image_url": immediate_url,
                "details": response_payload,
                "sync": True,
            }

        status_info: Dict[str, Any] = {
            "job_id": job_id,
            "status_endpoint": f"/api/v1/jobs/{job_id}/status" if job_id else None,
            "parameters": api_parameters,
        }

        if not job_id:
            return {
                "success": False,
                "message": "Image generation request did not return a job ID or image URL.",
                "details": response_payload,
                "prompt_preview": prompt_preview,
            }

        if job_id and poll:
            job_data, poll_error = _poll_job_until_complete(job_id, timeout=poll_timeout, interval=poll_interval)
            if job_data and not poll_error:
                result_payload = job_data.get("result") or {}
                image_url = result_payload.get("image_url")
                message = f"Image job {job_id} completed successfully."
                if image_url:
                    message += f" Download: {image_url}"
                status_info.update({
                    "status": job_data.get("status"),
                    "result": result_payload,
                    "image_url": image_url,
                    "completed": True,
                })
                return {
                    "success": True,
                    "message": message,
                    "prompt_preview": prompt_preview,
                    **status_info,
                }

            if poll_error:
                status_info["polling_error"] = poll_error

        return {
            "success": True,
            "message": (
                f"Image generation job {job_id} started using {normalized_model}. "
                "Polling is disabled or timed out; fetch status when ready."
            ),
            "prompt_preview": prompt_preview,
            **status_info,
        }
    except Exception as e:
        logger.error(f"Image generation guidance failed: {str(e)}")
        return {
            "success": False,
            "error": f"Image generation guidance failed: {str(e)}",
        }


# ============================================================================
# TOOL 5: Get Available Image Models
# ============================================================================

def get_available_models() -> Dict[str, Any]:
    """
    Get list of available image generation models.
    
    Returns:
        {
            "success": bool,
            "models": [str],
        }
    """
    try:
        available_models = [
            "modal_image",
            "flux-realism",
            "flux-pro",
            "kontext",
            "dall-e-3",
            "midjourney",
            "stable-diffusion-3",
        ]
        
        return {
            "success": True,
            "models": available_models,
            "recommended": "modal_image",
            "model_count": len(available_models),
        }
    except Exception as e:
        logger.error(f"Model retrieval failed: {str(e)}")
        return {
            "success": False,
            "error": f"Model retrieval failed: {str(e)}",
        }


# ============================================================================
# TOOL 6: Create Video Clip
# ============================================================================

def create_video_clip(
    image_url: str,
    duration: float = 3.0,
    effect: str = "none",
    fps: int = 24,
    poll: bool = True,
    poll_timeout: float = 300.0,
    poll_interval: float = 5.0,
) -> Dict[str, Any]:
    """
    Create a video clip from an image with optional effects. Returns an S3 URL.

    Turns static images into video clips with zoom, pan, fade effects.

    Args:
        image_url: URL or path to the image
        duration: Video duration in seconds
        effect: Motion effect ('none', 'zoom', 'zoom_out', 'pan', 'ken_burns')
        fps: Frames per second (24, 30, 60)
        poll: When True, poll job until completion
        poll_timeout: Maximum seconds to wait
        poll_interval: Delay between polls

    Returns:
        {
            "success": bool,
            "message": str,
            "video_url": str,  # S3 URL to generated video
        }

    Example:
        create_video_clip(
            image_url="https://example.com/image.jpg",
            duration=3.0,
            effect="zoom"
        )
    """
    try:
        image_preview = image_url[:80] + "..." if len(image_url) > 80 else image_url

        api_parameters: Dict[str, Any] = {
            "image_url": image_url,
            "video_length": duration,
            "effect_type": effect,
            "frame_rate": fps,
        }

        success, response_payload, error = _post_internal("/videos/generations", api_parameters)

        if not success or not response_payload:
            message = f"Ready to create video clip: {effect} effect, {duration}s, {fps}fps."
            if error:
                message += f" (Note: automatic execution unavailable: {error})"
            return {
                "success": True,
                "message": message,
                "image_preview": image_preview,
                "api_endpoint": "/api/v1/videos/generations",
                "parameters": api_parameters,
            }

        job_id = response_payload.get("job_id")
        if not job_id:
            return {
                "success": False,
                "message": "Video clip request did not return a job ID.",
                "details": response_payload,
            }

        if poll:
            job_data, poll_error = _poll_job_until_complete(job_id, timeout=poll_timeout, interval=poll_interval)
            if job_data and not poll_error:
                result_payload = job_data.get("result") or {}
                video_url = result_payload.get("final_video_url") or result_payload.get("video_url") or result_payload.get("url")
                message = f"Video clip created successfully ({effect} effect, {duration}s)."
                if video_url:
                    message += f" Download: {video_url}"
                return {
                    "success": True,
                    "message": message,
                    "image_preview": image_preview,
                    "video_url": video_url,
                    "job_id": job_id,
                    "details": result_payload,
                }
            if poll_error:
                return {
                    "success": False,
                    "message": f"Video clip job failed: {poll_error}",
                    "job_id": job_id,
                }

        return {
            "success": True,
            "message": f"Video clip job {job_id} started. Poll /api/v1/jobs/{job_id}/status for result.",
            "image_preview": image_preview,
            "job_id": job_id,
        }
    except Exception as e:
        logger.error(f"Video clip creation failed: {str(e)}")
        return {
            "success": False,
            "error": f"Video clip creation failed: {str(e)}",
        }


# ============================================================================
# TOOL 7: Add Captions to Video
# ============================================================================

def add_captions_to_video(
    video_url: str,
    captions: Optional[str] = None,
    style: str = "classic",
    position: str = "bottom_center",
    font_size: int = 24,
    poll: bool = True,
    poll_timeout: float = 300.0,
    poll_interval: float = 5.0,
) -> Dict[str, Any]:
    """
    Add captions or subtitles to a video. Returns an S3 URL.

    Adds styled captions with auto-transcription option.

    Args:
        video_url: URL or path to the video
        captions: Caption text (optional; omit for auto-transcription)
        style: Caption style ('classic', 'karaoke', 'highlight', 'underline', 'word_by_word')
        position: Caption position ('bottom_center', 'top_left', etc.)
        font_size: Font size in pixels
        poll: When True, poll job until completion
        poll_timeout: Maximum seconds to wait
        poll_interval: Delay between polls

    Returns:
        {
            "success": bool,
            "message": str,
            "video_url": str,  # S3 URL to captioned video
        }

    Example:
        add_captions_to_video(
            video_url="https://example.com/video.mp4",
            style="karaoke"
        )
    """
    try:
        caption_info = "auto-transcription" if not captions else f"custom captions ({len(captions)} chars)"

        api_parameters: Dict[str, Any] = {
            "video_url": video_url,
            "settings": {
                "style": style,
                "position": position,
                "font_size": font_size,
            },
        }
        if captions:
            api_parameters["captions"] = captions

        success, response_payload, error = _post_internal("/videos/add-captions", api_parameters)

        if not success or not response_payload:
            message = f"Ready to add captions: {style} style, {position}, {caption_info}."
            if error:
                message += f" (Note: automatic execution unavailable: {error})"
            return {
                "success": True,
                "message": message,
                "api_endpoint": "/api/v1/videos/add-captions",
                "parameters": api_parameters,
            }

        job_id = response_payload.get("job_id")
        if not job_id:
            return {
                "success": False,
                "message": "Captions request did not return a job ID.",
                "details": response_payload,
            }

        if poll:
            job_data, poll_error = _poll_job_until_complete(job_id, timeout=poll_timeout, interval=poll_interval)
            if job_data and not poll_error:
                result_payload = job_data.get("result") or {}
                video_result_url = result_payload.get("final_video_url") or result_payload.get("video_url") or result_payload.get("url")
                message = f"Captions added successfully ({style} style, {caption_info})."
                if video_result_url:
                    message += f" Download: {video_result_url}"
                return {
                    "success": True,
                    "message": message,
                    "video_url": video_result_url,
                    "job_id": job_id,
                    "details": result_payload,
                }
            if poll_error:
                return {
                    "success": False,
                    "message": f"Captions job failed: {poll_error}",
                    "job_id": job_id,
                }

        return {
            "success": True,
            "message": f"Captions job {job_id} started. Poll /api/v1/jobs/{job_id}/status for result.",
            "job_id": job_id,
        }
    except Exception as e:
        logger.error(f"Caption addition failed: {str(e)}")
        return {
            "success": False,
            "error": f"Caption addition failed: {str(e)}",
        }


# ============================================================================
# TOOL 8: Add Audio to Video
# ============================================================================

def add_audio_to_video(
    video_url: str,
    audio_url: str,
    video_volume: int = 50,
    audio_volume: int = 100,
    poll: bool = True,
    poll_timeout: float = 300.0,
    poll_interval: float = 5.0,
) -> Dict[str, Any]:
    """
    Mix audio with a video file. Returns an S3 URL.

    Combines video and audio tracks with customizable volume levels.

    Args:
        video_url: URL or path to the video file
        audio_url: URL or path to the audio file
        video_volume: Video audio volume (0-100)
        audio_volume: New audio volume (0-100)
        poll: When True, poll job until completion
        poll_timeout: Maximum seconds to wait
        poll_interval: Delay between polls

    Returns:
        {
            "success": bool,
            "message": str,
            "video_url": str,  # S3 URL to combined video
        }

    Example:
        add_audio_to_video(
            video_url="https://example.com/video.mp4",
            audio_url="https://example.com/audio.wav",
            video_volume=20,
            audio_volume=80
        )
    """
    try:
        api_parameters: Dict[str, Any] = {
            "video_url": video_url,
            "audio_url": audio_url,
            "video_volume": video_volume,
            "audio_volume": audio_volume,
        }

        success, response_payload, error = _post_internal("/videos/add-audio", api_parameters)

        if not success or not response_payload:
            message = f"Ready to mix audio: video volume {video_volume}%, audio volume {audio_volume}%."
            if error:
                message += f" (Note: automatic execution unavailable: {error})"
            return {
                "success": True,
                "message": message,
                "api_endpoint": "/api/v1/videos/add-audio",
                "parameters": api_parameters,
            }

        job_id = response_payload.get("job_id")
        if not job_id:
            return {
                "success": False,
                "message": "Add-audio request did not return a job ID.",
                "details": response_payload,
            }

        if poll:
            job_data, poll_error = _poll_job_until_complete(job_id, timeout=poll_timeout, interval=poll_interval)
            if job_data and not poll_error:
                result_payload = job_data.get("result") or {}
                video_result_url = result_payload.get("url") or result_payload.get("video_url") or result_payload.get("final_video_url")
                message = f"Audio mixed successfully (video vol {video_volume}%, audio vol {audio_volume}%)."
                if video_result_url:
                    message += f" Download: {video_result_url}"
                return {
                    "success": True,
                    "message": message,
                    "video_url": video_result_url,
                    "job_id": job_id,
                    "details": result_payload,
                }
            if poll_error:
                return {
                    "success": False,
                    "message": f"Add-audio job failed: {poll_error}",
                    "job_id": job_id,
                }

        return {
            "success": True,
            "message": f"Add-audio job {job_id} started. Poll /api/v1/jobs/{job_id}/status for result.",
            "job_id": job_id,
        }
    except Exception as e:
        logger.error(f"Audio mixing failed: {str(e)}")
        return {
            "success": False,
            "error": f"Audio mixing failed: {str(e)}",
        }


# ============================================================================
# TOOL 9: Merge Videos
# ============================================================================

def merge_videos(
    video_urls: List[str],
    transition: str = "fade",
    transition_duration: float = 0.5,
    poll: bool = True,
    poll_timeout: float = 300.0,
    poll_interval: float = 5.0,
) -> Dict[str, Any]:
    """
    Merge multiple video clips into a single video. Returns an S3 URL.

    Concatenates videos with smooth transition effects between clips.

    Args:
        video_urls: List of video URLs or paths to merge
        transition: Transition effect ('none', 'fade', 'dissolve', 'slide', 'wipe')
        transition_duration: Duration of transition in seconds
        poll: When True, poll job until completion
        poll_timeout: Maximum seconds to wait
        poll_interval: Delay between polls

    Returns:
        {
            "success": bool,
            "message": str,
            "video_url": str,  # S3 URL to merged video
        }

    Example:
        merge_videos(
            video_urls=[
                "https://example.com/clip1.mp4",
                "https://example.com/clip2.mp4",
            ],
            transition="fade"
        )
    """
    try:
        if len(video_urls) < 2:
            return {
                "success": False,
                "error": "At least 2 video URLs are required for merging",
            }

        api_parameters: Dict[str, Any] = {
            "video_urls": video_urls,
            "transition": transition,
            "transition_duration": transition_duration,
        }

        success, response_payload, error = _post_internal("/videos/merge", api_parameters)

        if not success or not response_payload:
            message = f"Ready to merge {len(video_urls)} clips: {transition} transition ({transition_duration}s)."
            if error:
                message += f" (Note: automatic execution unavailable: {error})"
            return {
                "success": True,
                "message": message,
                "clip_count": len(video_urls),
                "api_endpoint": "/api/v1/videos/merge",
                "parameters": api_parameters,
            }

        job_id = response_payload.get("job_id")
        if not job_id:
            return {
                "success": False,
                "message": "Merge request did not return a job ID.",
                "details": response_payload,
            }

        if poll:
            job_data, poll_error = _poll_job_until_complete(job_id, timeout=poll_timeout, interval=poll_interval)
            if job_data and not poll_error:
                result_payload = job_data.get("result") or {}
                video_result_url = result_payload.get("url") or result_payload.get("video_url") or result_payload.get("final_video_url")
                message = f"Merged {len(video_urls)} clips successfully ({transition} transition)."
                if video_result_url:
                    message += f" Download: {video_result_url}"
                return {
                    "success": True,
                    "message": message,
                    "video_url": video_result_url,
                    "clip_count": len(video_urls),
                    "job_id": job_id,
                    "details": result_payload,
                }
            if poll_error:
                return {
                    "success": False,
                    "message": f"Merge job failed: {poll_error}",
                    "job_id": job_id,
                }

        return {
            "success": True,
            "message": f"Merge job {job_id} started. Poll /api/v1/jobs/{job_id}/status for result.",
            "clip_count": len(video_urls),
            "job_id": job_id,
        }
    except Exception as e:
        logger.error(f"Video merge failed: {str(e)}")
        return {
            "success": False,
            "error": f"Video merge failed: {str(e)}",
        }


# ============================================================================
# TOOL 10: Get Music Tracks
# ============================================================================

def get_music_tracks(
    style: str = "background",
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Get available background music tracks.
    
    Returns music library tracks by style for use in videos.
    
    Args:
        style: Music style ('background', 'upbeat', 'calm', 'dramatic', 'energetic')
        limit: Maximum number of tracks to return
    
    Returns:
        {
            "success": bool,
            "available_tracks": int,
            "api_endpoint": str,
        }
    
    Example:
        tracks = get_music_tracks(style="upbeat", limit=5)
    """
    try:
        return {
            "success": True,
            "message": f"Music library ready: searching for {style} tracks (limit: {limit})",
            "api_endpoint": "/api/music/tracks",
            "parameters": {
                "style": style,
                "limit": limit,
            },
        }
    except Exception as e:
        logger.error(f"Music retrieval failed: {str(e)}")
        return {
            "success": False,
            "error": f"Music retrieval failed: {str(e)}",
        }


# ============================================================================
# TOOL 11: Post to Social Media
# ============================================================================

def post_to_social_media(
    content: str,
    video_url: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    post_type: str = "video",
    schedule_time: Optional[str] = None,
    delivery_mode: str = "now",
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Post content to social media platforms.
    
    Posts videos to multiple platforms (TikTok, Instagram, YouTube, Facebook, LinkedIn).
    
    Args:
        content: Caption or description text
        video_url: URL to the media file (video/image/audio) to attach
        platforms: List of target platforms or integration identifiers
        post_type: Content type descriptor ('video', 'reel', 'short', etc.) for messaging
        schedule_time: ISO datetime to schedule post (optional)
        delivery_mode: Postiz delivery mode ('now', 'schedule', 'draft')
        tags: Optional list of tags/hashtags for the post
    
    Returns:
        {
            "success": bool,
            "message": str,
            "api_endpoint": str,
            "platforms": [str],
            "integrations": [str],
        }
    
    Example:
        post_to_social_media(
            content="Check out these amazing ocean facts! 🌊",
            video_url="https://example.com/video.mp4",
            platforms=["tiktok", "instagram"],
            delivery_mode="schedule",
            schedule_time="2025-01-15T09:30:00Z"
        )
    """
    try:
        selected_platforms = platforms or ["tiktok"]

        if not INTERNAL_API_ENABLED:
            schedule_info = f"scheduled for {schedule_time}" if schedule_time else "posting immediately"
            return {
                "success": True,
                "message": (
                    f"Postiz integration not configured for automatic scheduling. "
                    f"Prepare to post to {', '.join(selected_platforms)} ({schedule_info})."
                ),
                "platforms": selected_platforms,
                "post_type": post_type,
                "parameters": {
                    "content": content,
                    "video_url": video_url,
                    "platforms": selected_platforms,
                    "delivery_mode": delivery_mode,
                    "schedule_time": schedule_time,
                },
            }

        integration_ids, integration_meta, missing_platforms, integration_error = _resolve_postiz_integrations(selected_platforms)
        if integration_error:
            return {
                "success": False,
                "error": integration_error,
                "missing_platforms": missing_platforms,
            }

        if missing_platforms:
            return {
                "success": False,
                "error": f"Could not map platforms to Postiz integrations: {', '.join(missing_platforms)}",
            }

        publish_mode = delivery_mode.lower().strip()
        valid_modes = {"now", "schedule", "draft"}
        if publish_mode not in valid_modes:
            publish_mode = "now"

        if schedule_time and publish_mode == "now":
            publish_mode = "schedule"

        if publish_mode == "schedule" and not schedule_time:
            return {
                "success": False,
                "error": "A schedule_time is required when delivery_mode is 'schedule'.",
            }

        api_endpoint = "/postiz/schedule-now"
        if publish_mode == "schedule":
            api_endpoint = "/postiz/schedule"
        elif publish_mode == "draft":
            api_endpoint = "/postiz/create-draft"

        final_content = content.strip() if content else ""
        if not final_content:
            final_content = "🚀 New AI-generated content is ready to share!"
        media_urls: Optional[List[str]] = None
        if video_url:
            media_urls = [video_url]
            if video_url not in final_content:
                final_content = f"{final_content}\n\nMedia: {video_url}".strip()

        payload: Dict[str, Any] = {
            "content": final_content,
            "integrations": integration_ids,
            "post_type": publish_mode,
        }

        if publish_mode == "schedule":
            payload["schedule_date"] = schedule_time

        if tags:
            payload["tags"] = tags

        if media_urls:
            payload["media_urls"] = media_urls

        success, response_payload, error = _post_internal(api_endpoint, payload, timeout=60.0)
        if not success or response_payload is None:
            return {
                "success": False,
                "error": error or "Failed to schedule post via Postiz.",
                "parameters": payload,
                "api_endpoint": f"/api/v1{api_endpoint}",
            }

        scheduled_platforms = [
            meta.get("name") or meta.get("provider") or meta.get("id") for meta in integration_meta
        ]
        schedule_desc = (
            f"scheduled for {schedule_time}" if publish_mode == "schedule" else ("saved as draft" if publish_mode == "draft" else "queued to publish now")
        )

        return {
            "success": True,
            "message": f"Post successfully handled by Postiz ({schedule_desc}) for {', '.join(str(p) for p in scheduled_platforms)}.",
            "api_endpoint": f"/api/v1{api_endpoint}",
            "platforms": scheduled_platforms,
            "integrations": integration_ids,
            "post_type": post_type,
            "delivery_mode": publish_mode,
            "postiz_response": response_payload,
        }
    except Exception as e:
        logger.error(f"Social media post guidance failed: {str(e)}")
        return {
            "success": False,
            "error": f"Social media posting guidance failed: {str(e)}",
        }


# ============================================================================
# TOOL 12: Generate Social Caption
# ============================================================================

def generate_social_caption(
    topic: str,
    platform: str = "tiktok",
    tone: str = "engaging",
) -> Dict[str, Any]:
    """
    Generate platform-optimized captions/hashtags.
    
    Creates tailored captions and hashtags for specific social media platforms.
    
    Args:
        topic: Topic or content description
        platform: Target platform ('tiktok', 'instagram', 'youtube', 'facebook', 'linkedin')
        tone: Tone of caption ('engaging', 'professional', 'funny', 'emotional')
    
    Returns:
        {
            "success": bool,
            "caption_example": str,
            "platform": str,
            "tone": str,
        }
    
    Example:
        caption_data = generate_social_caption(
            topic="Amazing ocean facts video",
            platform="tiktok",
            tone="engaging"
        )
    """
    try:
        # Sample captions for different platforms
        platform_templates = {
            "tiktok": f"😱 {topic} will blow your mind! 🤯 #FYP #viral #trending",
            "instagram": f"✨ {topic} ✨ #instagram #reels #content",
            "youtube": f"{topic} - Don't miss this! Subscribe for more! 👍",
            "facebook": f"Check out: {topic} 👍 Share with your friends!",
            "linkedin": f"Insights: {topic} #professional #innovation",
        }
        
        sample_caption = platform_templates.get(platform, f"{topic} #trending")
        
        return {
            "success": True,
            "caption_example": sample_caption,
            "platform": platform,
            "tone": tone,
            "message": f"Platform-optimized caption ready for {platform} ({tone} tone)",
            "hashtags": [word for word in sample_caption.split() if word.startswith("#")],
        }
    except Exception as e:
        logger.error(f"Caption generation guidance failed: {str(e)}")
        return {
            "success": False,
            "error": f"Caption generation guidance failed: {str(e)}",
        }
