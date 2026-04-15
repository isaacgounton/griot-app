"""
OpenAI-compatible endpoints for TTS models and voices.
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from app.services.audio.tts_service import tts_service
from app.services.audio.edge_tts_service import edge_tts_service
from app.utils.auth import get_current_user
import logging
import os
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["OpenAI Compatibility"])


@router.get("/models")
@router.post("/models")
async def list_models(current_user: Dict[str, Any] = Depends(get_current_user)):
    """List available TTS models in OpenAI-compatible format. Includes Kokoro and Edge TTS providers."""
    try:
        models = tts_service.get_models_formatted()
        return {"models": models}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")


@router.get("/audio/models")
@router.post("/audio/models")
async def list_audio_models(current_user: Dict[str, Any] = Depends(get_current_user)):
    """List available audio/TTS models in OpenAI-compatible format."""
    return await list_models()


@router.get("/audio/voices")
@router.post("/audio/voices")
async def list_audio_voices(current_user: Dict[str, Any] = Depends(get_current_user)):
    """List available voices for audio generation in OpenAI-compatible format."""
    try:
        voices = tts_service.get_voices_formatted()
        return {"voices": voices}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {str(e)}")


@router.get("/voices")
@router.post("/voices")
async def list_voices(request: Request, current_user: Dict[str, Any] = Depends(get_current_user)):
    """List Edge TTS voices with optional language filtering."""
    try:
        # Get language parameter from query string or request body
        language = None
        if request.method == "GET":
            language = request.query_params.get("language") or request.query_params.get("locale")
        elif request.method == "POST" and hasattr(request, "json"):
            try:
                data = await request.json()
                language = data.get("language") or data.get("locale")
            except:
                pass
        
        voices = await edge_tts_service.get_available_voices(language)
        return {"voices": voices}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {str(e)}")


@router.get("/voices/all")
@router.post("/voices/all")
async def list_all_voices(current_user: Dict[str, Any] = Depends(get_current_user)):
    """List all available Edge TTS voices."""
    try:
        voices = await edge_tts_service.get_available_voices("all")
        return {"voices": voices}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get all voices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {str(e)}")


# ElevenLabs compatibility endpoints
@router.post("/elevenlabs/text-to-speech/{voice_id}")
async def elevenlabs_text_to_speech(voice_id: str, request: Request, current_user: Dict[str, Any] = Depends(get_current_user)):
    """ElevenLabs-compatible text-to-speech endpoint using Edge TTS."""
    try:
        # Parse the incoming JSON payload
        try:
            payload = await request.json()
            if not payload or 'text' not in payload:
                raise HTTPException(status_code=400, detail="Missing 'text' in request body")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {str(e)}")

        text = payload['text']

        # Use Edge TTS service to generate speech
        try:
            audio_file_path = await edge_tts_service.generate_speech(
                text=text,
                voice=voice_id,
                response_format='mp3',
                speed=1.0,
                remove_filter=False  # Enable text preprocessing by default
            )
        except ValueError as e:
            # If text preprocessing fails, retry without filter
            if "empty after preprocessing" in str(e).lower():
                logger.warning(f"Text preprocessing removed all content. Retrying without filter...")
                audio_file_path = await edge_tts_service.generate_speech(
                    text=text,
                    voice=voice_id,
                    response_format='mp3',
                    speed=1.0,
                    remove_filter=True  # Skip text preprocessing
                )
            else:
                raise
        
        # Read the file and return as streaming response
        def file_generator():
            with open(audio_file_path, 'rb') as f:
                yield f.read()
            # Clean up the file after sending
            try:
                os.unlink(audio_file_path)
            except OSError:
                pass
        
        return StreamingResponse(
            file_generator(),
            media_type="audio/mpeg",
            headers={
                'Content-Disposition': 'attachment; filename="speech.mp3"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ElevenLabs TTS failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


# Azure Cognitive Services compatibility
@router.post("/azure/cognitiveservices/v1")
async def azure_cognitive_services_tts(request: Request, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Azure Cognitive Services-compatible TTS endpoint. Accepts SSML payloads."""
    try:
        # Parse the SSML payload
        try:
            ssml_data = await request.body()
            ssml_string = ssml_data.decode('utf-8')
            if not ssml_string:
                raise HTTPException(status_code=400, detail="Missing SSML payload")

            # Extract the text and voice from SSML
            root = ET.fromstring(ssml_string)
            
            # Find the voice element
            voice_element = root.find('.//{http://www.w3.org/2001/10/synthesis}voice')
            if voice_element is None:
                raise HTTPException(status_code=400, detail="No voice element found in SSML")
            
            text = voice_element.text or ""
            voice = voice_element.get('name')
            
            if not voice:
                raise HTTPException(status_code=400, detail="No voice name specified in SSML")
                
        except ET.ParseError as e:
            raise HTTPException(status_code=400, detail=f"Invalid SSML payload: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing SSML: {str(e)}")

        # Use Edge TTS service to generate speech
        try:
            audio_file_path = await edge_tts_service.generate_speech(
                text=text,
                voice=voice,
                response_format='mp3',
                speed=1.0,
                remove_filter=False  # Enable text preprocessing by default
            )
        except ValueError as e:
            # If text preprocessing fails, retry without filter
            if "empty after preprocessing" in str(e).lower():
                logger.warning(f"Text preprocessing removed all content. Retrying without filter...")
                audio_file_path = await edge_tts_service.generate_speech(
                    text=text,
                    voice=voice,
                    response_format='mp3',
                    speed=1.0,
                    remove_filter=True  # Skip text preprocessing
                )
            else:
                raise
        
        # Read the file and return as streaming response
        def file_generator():
            with open(audio_file_path, 'rb') as f:
                yield f.read()
            # Clean up the file after sending
            try:
                os.unlink(audio_file_path)
            except OSError:
                pass
        
        return StreamingResponse(
            file_generator(),
            media_type="audio/mpeg",
            headers={
                'Content-Disposition': 'attachment; filename="speech.mp3"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Azure TTS failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")