"""
MIME type utilities for audio formats.

Provides MIME type detection, validation, and conversion for various audio formats.
"""

import logging
from typing import Optional, Dict, Set

logger = logging.getLogger(__name__)

# Mapping of audio format to MIME types
AUDIO_FORMAT_MIME_TYPES: Dict[str, str] = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "opus": "audio/ogg",
    "aac": "audio/aac",
    "flac": "audio/flac",
    "pcm": "audio/L16",  # Raw PCM
    "ogg": "audio/ogg",
    "webm": "audio/webm",
    "m4a": "audio/mp4",
}

# Alternative MIME types for better compatibility
AUDIO_FORMAT_MIME_TYPES_ALT: Dict[str, Set[str]] = {
    "mp3": {"audio/mpeg", "audio/mp3"},
    "wav": {"audio/wav", "audio/x-wav"},
    "opus": {"audio/ogg", "audio/opus"},
    "aac": {"audio/aac", "audio/mp4"},
    "flac": {"audio/flac", "audio/x-flac"},
    "ogg": {"audio/ogg", "audio/x-ogg"},
    "webm": {"audio/webm"},
    "m4a": {"audio/mp4", "audio/x-m4a"},
}

# Format file extensions
AUDIO_FORMAT_EXTENSIONS: Dict[str, str] = {
    "mp3": ".mp3",
    "wav": ".wav",
    "opus": ".opus",
    "aac": ".aac",
    "flac": ".flac",
    "pcm": ".pcm",
    "ogg": ".ogg",
    "webm": ".webm",
    "m4a": ".m4a",
}

# FFmpeg supported formats
FFMPEG_SUPPORTED_FORMATS = {
    "mp3", "wav", "opus", "aac", "flac", "pcm",
    "ogg", "webm", "m4a", "vorbis", "wma"
}

# Browser compatible formats
BROWSER_COMPATIBLE_FORMATS = {"mp3", "wav", "ogg", "webm", "aac", "m4a"}

# Compression ratios (bytes per second of audio at 128kbps)
AUDIO_BITRATES: Dict[str, int] = {
    "mp3": 128,
    "aac": 128,
    "opus": 64,
    "flac": 600,  # Lossless, higher bitrate
    "wav": 1411,  # Uncompressed 44.1kHz 16-bit stereo
}


class MIMETypeError(Exception):
    """Exception for MIME type errors."""
    pass


class MIMETypeHandler:
    """Utilities for handling MIME types."""
    
    @staticmethod
    def get_mime_type(format_str: str) -> str:
        """
        Get MIME type for audio format.
        
        Args:
            format_str: Audio format (e.g., 'mp3', 'wav')
            
        Returns:
            MIME type string
            
        Raises:
            MIMETypeError: If format is not recognized
        """
        format_lower = format_str.lower().lstrip(".")
        
        if format_lower in AUDIO_FORMAT_MIME_TYPES:
            return AUDIO_FORMAT_MIME_TYPES[format_lower]
        
        raise MIMETypeError(f"Unknown audio format: {format_str}")
    
    @staticmethod
    def get_all_mime_types(format_str: str) -> Set[str]:
        """
        Get all possible MIME types for a format (primary + alternatives).
        
        Args:
            format_str: Audio format
            
        Returns:
            Set of MIME types
        """
        format_lower = format_str.lower().lstrip(".")
        
        result = set()
        if format_lower in AUDIO_FORMAT_MIME_TYPES:
            result.add(AUDIO_FORMAT_MIME_TYPES[format_lower])
        
        if format_lower in AUDIO_FORMAT_MIME_TYPES_ALT:
            result.update(AUDIO_FORMAT_MIME_TYPES_ALT[format_lower])
        
        return result
    
    @staticmethod
    def validate_mime_type(mime_type: str) -> bool:
        """
        Validate if a MIME type is a supported audio format.
        
        Args:
            mime_type: MIME type to validate
            
        Returns:
            True if valid audio MIME type
        """
        all_mimes = set()
        for mimes in AUDIO_FORMAT_MIME_TYPES_ALT.values():
            all_mimes.update(mimes)
        
        return mime_type in all_mimes
    
    @staticmethod
    def get_extension(format_str: str) -> str:
        """
        Get file extension for audio format.
        
        Args:
            format_str: Audio format
            
        Returns:
            File extension including dot
            
        Raises:
            MIMETypeError: If format is not recognized
        """
        format_lower = format_str.lower().lstrip(".")
        
        if format_lower in AUDIO_FORMAT_EXTENSIONS:
            return AUDIO_FORMAT_EXTENSIONS[format_lower]
        
        raise MIMETypeError(f"Unknown audio format: {format_str}")
    
    @staticmethod
    def get_bitrate(format_str: str) -> Optional[int]:
        """
        Get typical bitrate for audio format in kbps.
        
        Args:
            format_str: Audio format
            
        Returns:
            Bitrate in kbps or None if unknown
        """
        format_lower = format_str.lower().lstrip(".")
        return AUDIO_BITRATES.get(format_lower)
    
    @staticmethod
    def is_browser_compatible(format_str: str) -> bool:
        """
        Check if format is browser compatible.
        
        Args:
            format_str: Audio format
            
        Returns:
            True if format is browser compatible
        """
        format_lower = format_str.lower().lstrip(".")
        return format_lower in BROWSER_COMPATIBLE_FORMATS
    
    @staticmethod
    def is_ffmpeg_supported(format_str: str) -> bool:
        """
        Check if format is supported by FFmpeg.
        
        Args:
            format_str: Audio format
            
        Returns:
            True if format is FFmpeg supported
        """
        format_lower = format_str.lower().lstrip(".")
        return format_lower in FFMPEG_SUPPORTED_FORMATS
    
    @staticmethod
    def get_format_info(format_str: str) -> Dict:
        """
        Get comprehensive format information.
        
        Args:
            format_str: Audio format
            
        Returns:
            Dictionary with format information
            
        Raises:
            MIMETypeError: If format is not recognized
        """
        format_lower = format_str.lower().lstrip(".")
        
        if format_lower not in AUDIO_FORMAT_MIME_TYPES:
            raise MIMETypeError(f"Unknown audio format: {format_str}")
        
        return {
            "format": format_lower,
            "extension": AUDIO_FORMAT_EXTENSIONS.get(format_lower),
            "mime_type": AUDIO_FORMAT_MIME_TYPES[format_lower],
            "alternative_mimes": list(AUDIO_FORMAT_MIME_TYPES_ALT.get(format_lower, set())),
            "bitrate": AUDIO_BITRATES.get(format_lower),
            "browser_compatible": format_lower in BROWSER_COMPATIBLE_FORMATS,
            "ffmpeg_supported": format_lower in FFMPEG_SUPPORTED_FORMATS,
        }


class StreamHeaders:
    """Utilities for generating streaming response headers."""
    
    @staticmethod
    def get_audio_stream_headers(format_str: str, is_sse: bool = False) -> Dict[str, str]:
        """
        Get proper HTTP headers for audio streaming.
        
        Args:
            format_str: Audio format
            is_sse: Whether this is Server-Sent Events streaming
            
        Returns:
            Dictionary of headers
        """
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
        
        if is_sse:
            headers["Content-Type"] = "text/event-stream"
        else:
            try:
                mime_type = MIMETypeHandler.get_mime_type(format_str)
                headers["Content-Type"] = mime_type
            except MIMETypeError:
                headers["Content-Type"] = "audio/mpeg"  # Default to MP3
        
        return headers
    
    @staticmethod
    def get_cors_headers() -> Dict[str, str]:
        """
        Get CORS headers for audio endpoints.
        
        Returns:
            Dictionary of CORS headers
        """
        return {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",
        }


def validate_audio_format(format_str: str, strict: bool = False) -> str:
    """
    Validate audio format and return normalized format name.
    
    Args:
        format_str: Audio format to validate
        strict: If True, only accept browser-compatible formats
        
    Returns:
        Normalized format name
        
    Raises:
        MIMETypeError: If format is invalid
    """
    if not format_str:
        return "mp3"
    
    format_lower = format_str.lower().lstrip(".")
    
    if format_lower not in AUDIO_FORMAT_MIME_TYPES:
        raise MIMETypeError(
            f"Invalid audio format '{format_str}'. "
            f"Supported formats: {', '.join(sorted(AUDIO_FORMAT_MIME_TYPES.keys()))}"
        )
    
    if strict and not MIMETypeHandler.is_browser_compatible(format_lower):
        raise MIMETypeError(
            f"Format '{format_str}' is not browser compatible. "
            f"Browser-compatible formats: {', '.join(sorted(BROWSER_COMPATIBLE_FORMATS))}"
        )
    
    return format_lower


def get_format_compatibility_matrix() -> Dict[str, Dict[str, bool]]:
    """
    Get compatibility matrix for audio formats.
    
    Returns:
        Dictionary with compatibility info
    """
    return {
        format_name: {
            "browser": MIMETypeHandler.is_browser_compatible(format_name),
            "ffmpeg": MIMETypeHandler.is_ffmpeg_supported(format_name),
            "bitrate": MIMETypeHandler.get_bitrate(format_name),
        }
        for format_name in AUDIO_FORMAT_MIME_TYPES.keys()
    }
