"""
Routes for text to speech conversion supporting multiple TTS providers.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.models import TextToSpeechRequest, JobResponse, JobType
from app.services.job_queue import job_queue
from app.services.audio.tts_service import tts_service
from app.middleware.tts_validation import validate_tts_request, TTSValidationError
from app.utils.voice_filters import get_voice_options
from app.utils.mime_types import MIMETypeHandler, get_format_compatibility_matrix, AUDIO_FORMAT_MIME_TYPES
import uuid
import logging
import json
import base64
import os

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Audio"])


@router.post("/speech")
async def create_speech_job(request: TextToSpeechRequest):
    """Convert text to speech using Kokoro, Piper, or Edge TTS providers. Supports streaming, synchronous, and async job-based modes."""
    try:
        # Get text content (supports both 'text' and 'input' fields)
        text_content = request.get_text_content()
        
        # Validate request using comprehensive validation
        try:
            validated = validate_tts_request(
                text=text_content,
                provider=request.provider,
                voice=request.voice,
                response_format=request.response_format,
                speed=request.speed,
                volume_multiplier=request.volume_multiplier,
                stream=request.stream,
                sync=request.sync,
                stream_format=request.stream_format,
                remove_filter=request.remove_filter
            )
            
            # Update request with validated values
            text_content = validated["text"]
            request.provider = validated["provider"]
            request.voice = validated["voice"]
            request.response_format = validated["response_format"]
            request.speed = validated["speed"]
            request.volume_multiplier = validated["volume_multiplier"]
            request.stream = validated["stream"]
            request.sync = validated["sync"]
            request.stream_format = validated["stream_format"]
            request.remove_filter = validated["remove_filter"]
            
        except TTSValidationError as e:
            raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
        
        # Handle sync requests
        if request.sync:
            try:
                # Process TTS synchronously
                result = await tts_service.process_text_to_speech("sync", {
                    "text": text_content,
                    "voice": request.voice,
                    "provider": request.provider,
                    "response_format": request.response_format,
                    "speed": request.speed,
                    "volume_multiplier": request.volume_multiplier,
                    "normalization_options": request.normalization_options.model_dump() if request.normalization_options else None,
                    "return_timestamps": request.return_timestamps,
                    "lang_code": request.lang_code,
                    "remove_filter": request.remove_filter
                })
                logger.info("Completed synchronous TTS")
                return {
                    "job_id": None,
                    "status": "completed",
                    "result": result
                }
            except Exception as e:
                logger.error(f"Error in synchronous TTS: {str(e)}")
                raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")
        
        # Handle streaming requests
        if request.stream:
            return await handle_streaming_speech(request, text_content)
        
        # Handle regular job-based requests
        return await handle_job_based_speech(request, text_content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create TTS job: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def handle_streaming_speech(request: TextToSpeechRequest, text_content: str):
    """Handle streaming TTS requests."""
    provider = request.provider or "edge"  # Default to edge for streaming
    
    if provider.lower() not in ["edge"]:
        raise HTTPException(status_code=400, detail="Streaming is only supported with Edge TTS provider")
    
    try:
        if request.stream_format == "sse":
            # Server-Sent Events streaming with JSON
            async def generate_sse_stream():
                try:
                    async for chunk in tts_service.generate_speech_stream(
                        text=text_content,
                        voice=request.voice,
                        provider=provider,
                        speed=request.speed,
                        remove_filter=request.remove_filter
                    ):
                        # Base64 encode the audio chunk
                        encoded_audio = base64.b64encode(chunk).decode('utf-8')
                        
                        # Create SSE event for audio delta
                        event_data = {
                            "type": "speech.audio.delta",
                            "audio": encoded_audio
                        }
                        
                        # Format as SSE event
                        yield f"data: {json.dumps(event_data)}\n\n"
                    
                    # Send completion event
                    completion_event = {
                        "type": "speech.audio.done",
                        "usage": {
                            "input_tokens": len(text_content.split()),
                            "output_tokens": 0,
                            "total_tokens": len(text_content.split())
                        }
                    }
                    yield f"data: {json.dumps(completion_event)}\n\n"
                    
                except Exception as e:
                    logger.error(f"Error during SSE streaming: {e}")
                    error_event = {
                        "type": "error",
                        "error": str(e)
                    }
                    yield f"data: {json.dumps(error_event)}\n\n"
            
            return StreamingResponse(
                generate_sse_stream(),
                media_type='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no'
                }
            )
        
        else:
            # Raw audio streaming (default)
            async def generate_audio_stream():
                async for chunk in tts_service.generate_speech_stream(
                    text=text_content,
                    voice=request.voice,
                    provider=provider,
                    speed=request.speed,
                    remove_filter=request.remove_filter
                ):
                    yield chunk
            
            # Determine MIME type based on response format
            mime_types = {
                "mp3": "audio/mpeg",
                "wav": "audio/wav",
                "opus": "audio/ogg",
                "aac": "audio/mp4",
                "flac": "audio/flac",
                "pcm": "audio/wav"
            }
            mime_type = mime_types.get(request.response_format.lower(), "audio/mpeg")
            
            return StreamingResponse(
                generate_audio_stream(),
                media_type=mime_type,
                headers={
                    'Content-Type': mime_type
                }
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Streaming failed: {e}")
        raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")


async def handle_job_based_speech(request: TextToSpeechRequest, text_content: str):
    """Handle regular job-based TTS requests."""
    # Create job parameters with advanced features
    job_params = {
        "text": text_content,
        "voice": request.voice,
        "provider": request.provider,
        "response_format": request.response_format,
        "speed": request.speed,
        "volume_multiplier": request.volume_multiplier,
        "normalization_options": request.normalization_options.model_dump() if request.normalization_options else None,
        "return_timestamps": request.return_timestamps,
        "lang_code": request.lang_code,
        "remove_filter": request.remove_filter
    }
    
    # Create a new job
    job_id = str(uuid.uuid4())
    
    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.TEXT_TO_SPEECH,
        process_func=tts_service.process_text_to_speech,
        data=job_params
    )
    
    logger.info(f"Created TTS job {job_id} with provider: {request.provider or 'default'}")
    
    return JobResponse(job_id=job_id)


# Additional endpoints for TTS provider information
@router.get("/voices")
async def get_available_voices(provider: str | None = None, language: str | None = None):
    """Get available voices, optionally filtered by provider and language."""
    try:
        voices = await tts_service.get_available_voices(provider)
        
        # Apply language filtering if specified
        if language:
            filtered_voices = {}
            for prov, voice_list in voices.items():
                filtered_voices[prov] = [
                    voice for voice in voice_list 
                    if voice.get("language", "").lower() == language.lower()
                ]
            return filtered_voices
        
        return voices
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get available voices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {str(e)}")


@router.get("/voices/formatted")
async def get_voices_formatted(provider: str | None = None):
    """Get formatted voice list in OpenAI-compatible format."""
    try:
        voices = tts_service.get_voices_formatted(provider)
        return {"voices": voices}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get formatted voices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {str(e)}")


@router.get("/voices/all")
async def get_all_voices():
    """Get all available voices from all providers."""
    try:
        voices = await tts_service.get_available_voices()
        return {"voices": voices}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get all voices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {str(e)}")


@router.get("/models")
async def get_available_models(provider: str | None = None):
    """Get available TTS models, optionally filtered by provider."""
    try:
        models = tts_service.get_models(provider)
        return {"models": models}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get available models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")


@router.get("/models/formatted")
async def get_models_formatted(provider: str | None = None):
    """Get formatted TTS model list in OpenAI-compatible format."""
    try:
        models = tts_service.get_models_formatted(provider)
        return {"models": models}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get formatted models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")


@router.get("/providers")
async def get_supported_providers():
    """Get supported TTS providers, formats, and models."""
    try:
        providers = tts_service.get_supported_providers()
        formats = tts_service.get_supported_formats()
        models = tts_service.get_models()
        
        return {
            "providers": providers,
            "formats": formats,
            "models": models,
            "default_provider": tts_service.default_provider
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get provider information: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get providers: {str(e)}")


# Frontend compatibility endpoints
@router.get("/tts/providers")
async def get_tts_providers():
    """Get TTS providers (frontend-compatible format)."""
    try:
        providers = tts_service.get_supported_providers()
        return {
            "success": True,
            "data": providers
        }
    except Exception as e:
        logger.error(f"Failed to get TTS providers: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/tts/{provider}/voices")
async def get_voices_for_provider(provider: str):
    """Get voices for a specific provider (frontend-compatible format)."""
    try:
        voices = await tts_service.get_available_voices(provider)
        provider_voices = voices.get(provider, [])
        
        return {
            "success": True,
            "data": provider_voices
        }
    except Exception as e:
        logger.error(f"Failed to get voices for provider {provider}: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Enhanced voice discovery endpoints
@router.get("/voices/discover")
async def discover_voices(
    provider: str | None = Query(None, description="Filter by provider"),
    gender: str | None = Query(None, description="Filter by gender (Male/Female/Neutral)"),
    language: str | None = Query(None, description="Filter by language code (e.g., en-US, fr-FR)"),
    use_case: str | None = Query(None, description="Use case preset (professional, casual, energetic, calm, male, female)"),
    search: str | None = Query(None, description="Search query for voice names"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results")
):
    """Discover voices with filtering by provider, gender, language, use case, or search query."""
    try:
        voices_dict = await tts_service.get_available_voices()
        
        # Use voice filter to discover voices
        result = get_voice_options(
            voices_dict=voices_dict,
            provider=provider,
            gender=gender,
            language=language,
            use_case=use_case,
            search_query=search,
            limit=limit
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Failed to discover voices: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/audio-formats")
async def get_audio_formats():
    """Get supported audio formats with MIME types, compatibility, and bitrate details."""
    try:
        formats_info = {}
        
        for format_name, mime_type in AUDIO_FORMAT_MIME_TYPES.items():
            try:
                info = MIMETypeHandler.get_format_info(format_name)
                formats_info[format_name] = info
            except Exception as e:
                logger.warning(f"Failed to get info for format {format_name}: {e}")
        
        return {
            "success": True,
            "formats": formats_info,
            "compatibility_matrix": get_format_compatibility_matrix()
        }
    except Exception as e:
        logger.error(f"Failed to get audio formats: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/audio-formats/{format_name}")
async def get_format_info(format_name: str):
    """Get detailed information about a specific audio format."""
    try:
        info = MIMETypeHandler.get_format_info(format_name)
        
        return {
            "success": True,
            "format": info
        }
    except Exception as e:
        logger.error(f"Failed to get format info: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/voice-sample")
async def generate_voice_sample(
    voice: str = Query(..., description="Voice name to generate sample for"),
    provider: str = Query(..., description="TTS provider (kokoro, piper, edge)"),
    response_format: str = Query("mp3", description="Audio format (mp3, wav, etc.)")
):
    """Generate a short voice sample for preview. Returns audio URL immediately."""
    try:
        # Sample text for voice preview
        sample_text = "Hello! This is a voice sample. How do you like this voice?"

        # Generate speech synchronously - returns (audio_data_bytes, actual_provider)
        audio_data, actual_provider = await tts_service.generate_speech(
            text=sample_text,
            voice=voice,
            provider=provider,
            response_format=response_format,
            speed=1.0
        )

        # Upload to S3
        from app.services.s3 import s3_service
        import re
        import tempfile

        job_id = str(uuid.uuid4())

        # Sanitize voice name for S3 filename (remove special characters)
        safe_voice_name = re.sub(r'[^a-zA-Z0-9_-]', '_', voice)
        filename = f"voice-samples/{provider}/{safe_voice_name}/{job_id}.{response_format}"

        # Write audio data to a temporary file for S3 upload
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{response_format}") as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(audio_data)

            audio_url = await s3_service.upload_file(
                file_path=temp_file_path,
                object_name=filename,
                content_type=f"audio/{response_format}"
            )
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file: {e}")

        logger.info(f"Generated voice sample for voice: {voice} (provider: {provider}), URL: {audio_url}")

        return {
            "success": True,
            "audio_url": audio_url,
            "voice": voice,
            "provider": provider
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate voice sample: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def get_tts_capabilities():
    """Get comprehensive TTS capabilities including providers, formats, and speed ranges."""
    try:
        from app.middleware.tts_validation import SPEED_RANGES, SUPPORTED_FORMATS
        
        capabilities = {
            "providers": list(SUPPORTED_FORMATS.keys()),
            "formats": SUPPORTED_FORMATS,
            "speed_ranges": {k: {"min": v[0], "max": v[1], "default": v[2]} for k, v in SPEED_RANGES.items()},
            "audio_formats": {
                format_name: MIMETypeHandler.get_format_info(format_name)
                for format_name in AUDIO_FORMAT_MIME_TYPES.keys()
            }
        }
        
        return {
            "success": True,
            "capabilities": capabilities
        }
    except Exception as e:
        logger.error(f"Failed to get TTS capabilities: {e}")
        return {
            "success": False,
            "error": str(e)
        } 