"""
TTS Request Validation Middleware

Validates incoming TTS requests for:
- Text content length and format
- Audio format support
- Voice availability per provider
- Speed range validation
- Provider support
"""

import logging
from typing import Optional, Dict, Set
import os

logger = logging.getLogger(__name__)

# Supported audio formats per provider
SUPPORTED_FORMATS: Dict[str, Set[str]] = {
    "edge": {"mp3", "wav", "opus", "aac", "flac", "pcm"},
    "kokoro": {"wav", "mp3"},
    "piper": {"wav", "mp3"},
}

# Speed ranges per provider (min, max, default)
SPEED_RANGES: Dict[str, tuple[float, float, float]] = {
    "edge": (0.0, 2.0, 1.0),  # Match Edge TTS service limits
    "kokoro": (0.5, 2.0, 1.0),
    "piper": (0.5, 1.5, 1.0),
}

# Supported providers
SUPPORTED_PROVIDERS = {"edge", "kokoro", "piper"}

# Default TTS provider (consistent with TTS service)
DEFAULT_TTS_PROVIDER = os.environ.get("TTS_PROVIDER", "kokoro").lower()

# Text length limits
TEXT_LENGTH_LIMITS = {
    "sync": 5000,           # Synchronous requests
    "stream": 10000,        # Streaming requests
    "job": 15000,           # Job-based requests
}

class TTSValidationError(Exception):
    """Custom exception for TTS validation errors."""
    pass


class TTSValidator:
    """Validates TTS requests."""
    
    @staticmethod
    def validate_text_content(text: Optional[str], request_type: str = "sync") -> None:
        """
        Validate text content for TTS.
        
        Args:
            text: Text content to validate
            request_type: Type of request (sync, stream, or job)
            
        Raises:
            TTSValidationError: If validation fails
        """
        if not text:
            raise TTSValidationError("Text content cannot be empty")
        
        # Check for minimum content
        if len(text.strip()) < 1:
            raise TTSValidationError("Text cannot be only whitespace")
        
        # Check length limit based on request type
        limit = TEXT_LENGTH_LIMITS.get(request_type, TEXT_LENGTH_LIMITS["sync"])
        if len(text) > limit:
            raise TTSValidationError(
                f"Text exceeds maximum length of {limit} characters for {request_type} requests "
                f"(provided: {len(text)} characters)"
            )
    
    @staticmethod
    def validate_provider(provider: Optional[str]) -> str:
        """
        Validate TTS provider.
        
        Args:
            provider: Provider name to validate
            
        Returns:
            Validated provider name (lowercase)
            
        Raises:
            TTSValidationError: If provider is not supported
        """
        if not provider:
            return DEFAULT_TTS_PROVIDER  # Use same default as TTS service
        
        provider_lower = provider.lower()
        if provider_lower not in SUPPORTED_PROVIDERS:
            raise TTSValidationError(
                f"Unsupported provider '{provider}'. Supported providers: {', '.join(SUPPORTED_PROVIDERS)}"
            )
        
        return provider_lower
    
    @staticmethod
    def validate_audio_format(format_str: Optional[str], provider: str) -> str:
        """
        Validate audio format for the specified provider.
        
        Args:
            format_str: Audio format to validate
            provider: TTS provider
            
        Returns:
            Validated format (lowercase)
            
        Raises:
            TTSValidationError: If format is not supported
        """
        if not format_str:
            return "mp3"  # Default format
        
        format_lower = format_str.lower()
        supported = SUPPORTED_FORMATS.get(provider.lower(), {"mp3"})
        
        if format_lower not in supported:
            raise TTSValidationError(
                f"Audio format '{format_str}' not supported for provider '{provider}'. "
                f"Supported formats: {', '.join(sorted(supported))}"
            )
        
        return format_lower
    
    @staticmethod
    def validate_speed(speed: float, provider: str) -> float:
        """
        Validate playback speed for the specified provider.
        
        Args:
            speed: Speed multiplier to validate
            provider: TTS provider
            
        Returns:
            Validated speed
            
        Raises:
            TTSValidationError: If speed is out of range
        """
        provider_lower = provider.lower()
        if provider_lower not in SPEED_RANGES:
            raise TTSValidationError(f"Unsupported provider '{provider}'")
        
        min_speed, max_speed, _ = SPEED_RANGES[provider_lower]
        
        if speed < min_speed or speed > max_speed:
            raise TTSValidationError(
                f"Speed must be between {min_speed} and {max_speed} for provider '{provider}' "
                f"(provided: {speed})"
            )
        
        return speed
    
    @staticmethod
    def validate_voice(voice: Optional[str], provider: str) -> str:
        """
        Validate voice availability for the specified provider.
        
        Args:
            voice: Voice name to validate
            provider: TTS provider
            
        Returns:
            Voice name (or default if not provided)
            
        Raises:
            TTSValidationError: If voice is not supported
        """
        if not voice:
            # Return default voice for provider
            if provider.lower() == "kokoro":
                return "af_alloy"
            elif provider.lower() == "edge":
                return "alloy"  # Will be mapped to en-US-JennyNeural by the service
            elif provider.lower() == "piper":
                return "en_US-lessac-medium"
            else:
                return "af_alloy"  # Fallback default
        
        # For edge provider, accept any voice name
        # Edge TTS will handle validation itself and supports 500+ voices
        if provider.lower() == "edge":
            # Accept both OpenAI voice names and direct edge-tts names
            # No strict validation - let Edge TTS handle it
            logger.debug(f"Using Edge TTS voice: {voice}")
            return voice
        
        # For other providers, accept voice name without strict validation
        # (they have their own voice lists)
        return voice
    
    @staticmethod
    def validate_volume_multiplier(volume: float) -> float:
        """
        Validate volume multiplier.
        
        Args:
            volume: Volume multiplier to validate
            
        Returns:
            Validated volume multiplier
            
        Raises:
            TTSValidationError: If volume is invalid
        """
        if volume < 0.1 or volume > 2.0:
            raise TTSValidationError(
                f"Volume multiplier must be between 0.1 and 2.0 (provided: {volume})"
            )
        
        return volume
    
    @staticmethod
    def validate_request_type(stream: bool, sync: bool) -> str:
        """
        Validate and determine request type.
        
        Args:
            stream: Whether streaming is requested
            sync: Whether synchronous response is requested
            
        Returns:
            Request type ('stream', 'sync', or 'job')
            
        Raises:
            TTSValidationError: If request type is invalid
        """
        if stream and sync:
            raise TTSValidationError("Cannot use both 'stream' and 'sync' parameters together")
        
        if stream:
            return "stream"
        elif sync:
            return "sync"
        else:
            return "job"
    
    @staticmethod
    def validate_stream_format(stream_format: Optional[str]) -> str:
        """
        Validate streaming format.
        
        Args:
            stream_format: Stream format to validate
            
        Returns:
            Validated stream format
            
        Raises:
            TTSValidationError: If format is invalid
        """
        if not stream_format:
            return "audio"
        
        format_lower = stream_format.lower()
        valid_formats = {"audio", "sse"}
        
        if format_lower not in valid_formats:
            raise TTSValidationError(
                f"Invalid stream format '{stream_format}'. "
                f"Valid formats: {', '.join(valid_formats)}"
            )
        
        return format_lower


def validate_tts_request(
    text: Optional[str],
    provider: Optional[str] = None,
    voice: Optional[str] = None,
    response_format: Optional[str] = None,
    speed: float = 1.0,
    volume_multiplier: float = 1.0,
    stream: bool = False,
    sync: bool = False,
    stream_format: Optional[str] = None,
    remove_filter: bool = False
) -> Dict[str, Optional[str] | bool | float]:
    """
    Comprehensive TTS request validation.
    
    Args:
        text: Text to convert to speech
        provider: TTS provider
        voice: Voice name
        response_format: Audio format
        speed: Playback speed
        volume_multiplier: Volume multiplier
        stream: Enable streaming
        sync: Synchronous response
        stream_format: Streaming format
        remove_filter: Skip text processing
        
    Returns:
        Dictionary with validated parameters
        
    Raises:
        TTSValidationError: If any validation fails
    """
    try:
        # Determine request type
        request_type = TTSValidator.validate_request_type(stream, sync)
        
        # Validate text content
        TTSValidator.validate_text_content(text, request_type)
        
        # Validate provider
        provider = TTSValidator.validate_provider(provider)
        
        # Validate audio format
        response_format = TTSValidator.validate_audio_format(response_format, provider)
        
        # Validate speed
        speed = TTSValidator.validate_speed(speed, provider)
        
        # Validate voice
        voice = TTSValidator.validate_voice(voice, provider)
        
        # Validate volume multiplier
        volume_multiplier = TTSValidator.validate_volume_multiplier(volume_multiplier)
        
        # Validate stream format if streaming
        if stream:
            stream_format = TTSValidator.validate_stream_format(stream_format)
        
        return {
            "text": text,
            "provider": provider,
            "voice": voice,
            "response_format": response_format,
            "speed": speed,
            "volume_multiplier": volume_multiplier,
            "stream": stream,
            "sync": sync,
            "stream_format": stream_format,
            "remove_filter": remove_filter,
            "request_type": request_type
        }
    
    except TTSValidationError:
        raise
    except Exception as e:
        logger.error(f"Unexpected validation error: {e}")
        raise TTSValidationError(f"Validation error: {str(e)}")
