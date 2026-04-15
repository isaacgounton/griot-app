"""
Edge TTS service - High-quality text-to-speech using Microsoft Edge's TTS engine.

This service provides a modern, production-ready implementation of Edge TTS with:
- Streaming and non-streaming audio generation
- Multi-format audio output (MP3, WAV, OPUS, AAC, FLAC, PCM)
- OpenAI-compatible voice name mappings
- Comprehensive voice discovery with language filtering
- Automatic text preprocessing and cleanup
- FFmpeg-based audio format conversion
- Detailed error logging and validation
"""

import tempfile
import subprocess
import os
import re
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, AsyncGenerator

# Optional dependencies - Edge TTS functionality
try:
    import edge_tts
    import emoji
    EDGE_TTS_AVAILABLE: bool = True
except ImportError:
    edge_tts = None  # type: ignore
    emoji = None  # type: ignore
    EDGE_TTS_AVAILABLE: bool = False

# Configure logging
logger = logging.getLogger(__name__)

# OpenAI voice names mapped to edge-tts equivalents
# Supports OpenAI-compatible voice names with fallback to direct edge-tts voice names
VOICE_MAPPING = {
    'alloy': 'en-US-JennyNeural',
    'ash': 'en-US-AndrewNeural',
    'ballad': 'en-GB-ThomasNeural',
    'coral': 'en-AU-NatashaNeural',
    'echo': 'en-US-GuyNeural',
    'fable': 'en-GB-SoniaNeural',
    'nova': 'en-US-AriaNeural',
    'onyx': 'en-US-EricNeural',
    'sage': 'en-US-JennyNeural',
    'shimmer': 'en-US-EmmaNeural',
    'verse': 'en-US-BrianNeural',
}

# Default configuration
DEFAULT_VOICE = 'en-US-AriaNeural'
DEFAULT_LANGUAGE = 'en-US'

# TTS Models (OpenAI compatible)
TTS_MODELS = [
    {"id": "tts-1", "name": "Text-to-speech v1"},
    {"id": "tts-1-hd", "name": "Text-to-speech v1 HD"},
    {"id": "gpt-4o-mini-tts", "name": "GPT-4o mini TTS"}
]


class EdgeTTSService:
    """Production-ready Edge TTS service with streaming, format conversion, and voice management."""

    def __init__(self):
        """Initialize Edge TTS service."""
        logger.info("Initializing Edge TTS service")

        if EDGE_TTS_AVAILABLE:
            logger.info("✓ Edge TTS dependencies available (edge-tts, emoji)")
        else:
            logger.warning("⚠ Edge TTS dependencies not available. Please install: pip install edge-tts emoji")
    
    @staticmethod
    def is_ffmpeg_available() -> bool:
        """Check if FFmpeg is installed and accessible."""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    @staticmethod
    def prepare_text_for_tts(text: str, remove_filter: bool = False) -> str:
        """
        Prepare text for TTS by cleaning Markdown and adding contextual hints.
        
        Args:
            text: Raw text containing potential Markdown formatting
            remove_filter: If True, skip text processing
            
        Returns:
            Cleaned text suitable for TTS
        """
        if remove_filter or not text:
            return text
        
        # Remove emojis
        if emoji is not None:
            text = emoji.replace_emoji(text, replace='')
        
        # Add context for headers
        def header_replacer(match: re.Match[str]) -> str:  # type: ignore
            level: int = len(match.group(1))  # Number of '#' symbols
            header_text: str = match.group(2).strip()
            if level == 1:
                return f"Title — {header_text}\n"
            elif level == 2:
                return f"Section — {header_text}\n"
            else:
                return f"Subsection — {header_text}\n"
        
        text = re.sub(r"^(#{1,6})\s+(.*)", header_replacer, text, flags=re.MULTILINE)
        
        # Remove links while keeping the link text
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        
        # Describe inline code
        text = re.sub(r"`([^`]+)`", r"code snippet: \1", text)
        
        # Remove bold/italic symbols but keep the content
        text = re.sub(r"(\*\*|__|\*|_)", '', text)
        
        # Remove code blocks (multi-line) with a description
        text = re.sub(r"```([\s\S]+?)```", r"(code block omitted)", text)
        
        # Remove image syntax but add alt text if available
        text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"Image: \1", text)
        
        # Remove HTML tags
        text = re.sub(r"</?[^>]+(>|$)", '', text)
        
        # Normalize line breaks
        text = re.sub(r"\n{2,}", '\n\n', text)  # Ensure consistent paragraph separation
        
        # Replace multiple spaces within lines
        text = re.sub(r" {2,}", ' ', text)
        
        # Trim leading and trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def speed_to_rate(speed: float) -> str:
        """
        Convert a multiplicative speed value to edge-tts rate format.
        
        Args:
            speed: Multiplicative speed value (0.0-2.0, where 1.0 is normal speed)
            
        Returns:
            Formatted rate string (e.g., "+50%" or "-50%")
            
        Raises:
            ValueError: If speed is not between 0 and 2.0
        """
        if speed < 0 or speed > 2.0:
            raise ValueError("Speed must be between 0 and 2.0 (inclusive).")
        
        # Convert speed to percentage change
        percentage_change = (speed - 1) * 100
        
        # Format with a leading "+" or "-" as required
        return f"{percentage_change:+.0f}%"
    

    async def generate_speech_stream(
        self,
        text: str,
        voice: str = DEFAULT_VOICE,
        speed: float = 1.0,
        remove_filter: bool = False
    ) -> AsyncGenerator[bytes, None]:
        """
        Generate streaming TTS audio using Edge TTS.

        Args:
            text: Text to convert to speech
            voice: Voice name (OpenAI compatible or direct edge-tts voice)
            speed: Playback speed (0.0 to 2.0, where 1.0 is normal)
            remove_filter: Skip text preprocessing if True

        Yields:
            Audio chunk bytes

        Raises:
            RuntimeError: If TTS generation fails or dependencies not available
        """
        async for chunk in self._generate_speech_stream_via_library(text, voice, speed, remove_filter):
            yield chunk
    
    async def _generate_speech_stream_via_library(
        self,
        text: str,
        voice: str,
        speed: float,
        remove_filter: bool
    ) -> AsyncGenerator[bytes, None]:
        """
        Generate streaming TTS audio using the direct Edge TTS library.
        """
        if not EDGE_TTS_AVAILABLE:
            raise RuntimeError(
                "Edge TTS functionality is not available. "
                "Please install: pip install edge-tts emoji"
            )
        
        try:
            # Prepare text for TTS
            prepared_text = self.prepare_text_for_tts(text, remove_filter)

            # Log original and prepared text for debugging
            logger.info(f"Streaming - Original text length: {len(text)}, Prepared text length: {len(prepared_text)}")

            if not prepared_text or not prepared_text.strip():
                logger.error(
                    f"Text is empty after preprocessing for streaming. "
                    f"Original text: '{text[:100]}...', "
                    f"remove_filter: {remove_filter}"
                )
                raise ValueError(
                    f"Text is empty after preprocessing. "
                    f"Original text had {len(text)} characters. "
                    f"Try setting remove_filter=True to skip text preprocessing."
                )

            # Determine the edge-tts voice to use
            edge_tts_voice = VOICE_MAPPING.get(voice, voice)

            # Validate voice name
            logger.info(f"Streaming with Edge TTS voice: {edge_tts_voice} (requested: {voice})")

            # Convert speed to SSML rate format
            try:
                speed_rate = self.speed_to_rate(speed)
            except ValueError as e:
                logger.warning(f"Invalid speed value {speed}: {e}. Using default speed.")
                speed_rate = "+0%"

            logger.info(
                f"Streaming TTS: text_len={len(prepared_text)}, "
                f"voice={edge_tts_voice}, speed={speed_rate}"
            )

            # Create the communicator for streaming
            assert edge_tts is not None, "Edge TTS should be available at this point"
            communicator = edge_tts.Communicate(
                text=prepared_text,
                voice=edge_tts_voice,
                rate=speed_rate
            )

            # Stream the audio data
            try:
                async for chunk in communicator.stream():
                    if chunk.get("type") == "audio" and "data" in chunk:
                        yield chunk["data"]
            except Exception as stream_error:
                logger.error(
                    f"Edge TTS streaming failed: {stream_error}. "
                    f"Voice: {edge_tts_voice}, Text length: {len(prepared_text)}, "
                    f"Text preview: '{prepared_text[:100]}...'"
                )
                raise
        
        except Exception as e:
            logger.error(f"Failed to generate streaming speech: {e}", exc_info=True)
            raise RuntimeError(f"Speech streaming failed: {str(e)}")
    
    async def generate_speech(
        self,
        text: str,
        voice: str = DEFAULT_VOICE,
        response_format: str = "mp3",
        speed: float = 1.0,
        remove_filter: bool = False
    ) -> str:
        """
        Generate TTS audio using Edge TTS and optionally convert format.
        
        Args:
            text: Text to convert to speech
            voice: Voice name (OpenAI compatible or direct edge-tts voice)
            response_format: Audio format (mp3, wav, opus, aac, flac, pcm)
            speed: Playback speed (0.0 to 2.0, where 1.0 is normal)
            remove_filter: Skip text preprocessing if True
            
        Returns:
            Path to generated audio file

        Raises:
            RuntimeError: If TTS generation fails or dependencies not available
        """
        return await self._generate_speech_via_library(text, voice, response_format, speed, remove_filter)

    
    async def _generate_speech_via_library(
        self,
        text: str,
        voice: str,
        response_format: str,
        speed: float,
        remove_filter: bool
    ) -> str:
        """
        Generate TTS audio using the direct Edge TTS library (fallback).
        """
        if not EDGE_TTS_AVAILABLE:
            raise RuntimeError(
                "Edge TTS functionality is not available. "
                "Please install: pip install edge-tts emoji"
            )
        
        try:
            # Prepare text for TTS
            prepared_text = self.prepare_text_for_tts(text, remove_filter)

            # Log original and prepared text for debugging
            logger.info(f"Original text length: {len(text)}, Prepared text length: {len(prepared_text)}")
            logger.debug(f"Original text preview: {text[:200]}...")
            logger.debug(f"Prepared text preview: {prepared_text[:200]}...")

            if not prepared_text or not prepared_text.strip():
                logger.error(
                    f"Text is empty after preprocessing. "
                    f"Original text: '{text[:100]}...', "
                    f"Prepared text: '{prepared_text}', "
                    f"remove_filter: {remove_filter}"
                )
                raise ValueError(
                    f"Text is empty after preprocessing. "
                    f"Original text had {len(text)} characters. "
                    f"Try setting remove_filter=True to skip text preprocessing."
                )

            # Determine the edge-tts voice to use
            edge_tts_voice = VOICE_MAPPING.get(voice, voice)

            # Validate voice name
            logger.info(f"Using Edge TTS voice: {edge_tts_voice} (requested: {voice})")

            # Convert speed to SSML rate format
            try:
                speed_rate = self.speed_to_rate(speed)
            except ValueError as e:
                logger.warning(f"Invalid speed value {speed}: {e}. Using default speed.")
                speed_rate = "+0%"

            # Create temporary file for MP3 output
            temp_mp3_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_mp3_path = temp_mp3_file.name
            temp_mp3_file.close()

            logger.info(
                f"Generating TTS: text_len={len(prepared_text)}, "
                f"voice={edge_tts_voice}, format={response_format}, speed={speed_rate}"
            )

            # Generate the MP3 file using Edge TTS
            assert edge_tts is not None, "Edge TTS should be available at this point"
            communicator = edge_tts.Communicate(
                text=prepared_text,
                voice=edge_tts_voice,
                rate=speed_rate
            )

            try:
                await communicator.save(temp_mp3_path)
            except Exception as comm_error:
                logger.error(
                    f"Edge TTS Communicate.save() failed: {comm_error}. "
                    f"Voice: {edge_tts_voice}, Text length: {len(prepared_text)}, "
                    f"Text preview: '{prepared_text[:100]}...'"
                )
                raise
            
            # Validate that the file was created and has content
            if not os.path.exists(temp_mp3_path):
                raise RuntimeError(f"Edge TTS failed to create output file at {temp_mp3_path}")
            
            file_size = os.path.getsize(temp_mp3_path)
            if file_size == 0:
                os.unlink(temp_mp3_path)
                raise RuntimeError(
                    f"Edge TTS generated empty audio file. "
                    f"Voice '{edge_tts_voice}' may be invalid. "
                    f"Text preview: '{prepared_text[:100]}...'"
                )
            
            if file_size < 200:  # Very small file, likely corrupted
                logger.warning(f"Generated audio file is very small ({file_size} bytes). "
                             "This might indicate an issue.")
            
            logger.info(f"Generated MP3: {temp_mp3_path} ({file_size} bytes)")
            
            # If MP3 is requested, return the generated file directly
            if response_format.lower() == "mp3":
                return temp_mp3_path
            
            # For other formats, check if FFmpeg is available
            if not self.is_ffmpeg_available():
                logger.warning(f"FFmpeg not available. Returning MP3 instead of {response_format}")
                return temp_mp3_path
            
            # Convert to requested format using FFmpeg
            return await self._convert_audio_format(temp_mp3_path, response_format)
        
        except Exception as e:
            logger.error(f"Failed to generate speech: {e}", exc_info=True)
            raise RuntimeError(f"Speech generation failed: {str(e)}")
    
    async def _convert_audio_format(self, input_path: str, output_format: str) -> str:
        """
        Convert audio file to the requested format using FFmpeg.
        
        Args:
            input_path: Path to input MP3 file
            output_format: Target audio format
            
        Returns:
            Path to converted audio file
            
        Raises:
            RuntimeError: If conversion fails
        """
        # Create temporary file for converted output
        converted_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}")
        converted_path = converted_file.name
        converted_file.close()
        
        # Build FFmpeg command with codec/container mappings
        codec_map = {
            "aac": "aac",
            "mp3": "libmp3lame",
            "wav": "pcm_s16le",
            "opus": "libopus",
            "flac": "flac",
            "pcm": "pcm_s16le"
        }
        
        container_map = {
            "aac": "mp4",        # AAC in MP4 container
            "mp3": "mp3",
            "wav": "wav",
            "opus": "ogg",       # OPUS in OGG container
            "flac": "flac",
            "pcm": "wav"         # PCM in WAV container
        }
        
        codec = codec_map.get(output_format.lower(), "aac")
        container = container_map.get(output_format.lower(), output_format)
        
        ffmpeg_command = [
            "ffmpeg",
            "-i", input_path,
            "-c:a", codec,
        ]
        
        # Add bitrate for compressed formats
        if output_format.lower() not in ["wav", "flac", "pcm"]:
            ffmpeg_command.extend(["-b:a", "192k"])
        
        # Add format-specific options
        ffmpeg_command.extend([
            "-f", container,
            "-y",  # Overwrite without prompt
            converted_path
        ])
        
        try:
            logger.info(f"Converting audio to {output_format} format")
            subprocess.run(
                ffmpeg_command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60  # 60 second timeout
            )
            
            # Clean up original MP3 file
            Path(input_path).unlink(missing_ok=True)
            
            logger.info(f"Audio converted successfully: {converted_path}")
            return converted_path
        
        except subprocess.CalledProcessError as e:
            # Clean up files on error
            Path(converted_path).unlink(missing_ok=True)
            Path(input_path).unlink(missing_ok=True)
            
            error_msg = (
                f"FFmpeg conversion failed: "
                f"{e.stderr.decode('utf-8', 'ignore') if e.stderr else str(e)}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        except subprocess.TimeoutExpired:
            # Clean up files on timeout
            Path(converted_path).unlink(missing_ok=True)
            Path(input_path).unlink(missing_ok=True)
            
            error_msg = "FFmpeg conversion timed out after 60 seconds"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def get_available_voices(self, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of available Edge TTS voices with optional language filtering.
        
        Args:
            language: Language code to filter voices (e.g., 'en-US'),
                     'all' for all languages, or None for default language
            
        Returns:
            List of voice information dictionaries with keys:
            - name: Voice short name (e.g., 'en-US-AriaNeural')
            - gender: Voice gender (Male/Female)
            - language: Language locale (e.g., 'en-US')
            - display_name: Human-readable voice name
            
        Raises:
            RuntimeError: If Edge TTS is not available
        """
        try:
            if not EDGE_TTS_AVAILABLE or edge_tts is None:
                raise RuntimeError("Edge TTS is not available")

            all_voices = await edge_tts.list_voices()

            # Determine filter language
            filter_language = language or DEFAULT_LANGUAGE

            # Filter voices
            if filter_language and filter_language.lower() != 'all':
                filtered_voices: List[Dict[str, Any]] = [
                    {
                        "name": voice['ShortName'],
                        "gender": voice.get('Gender', 'Unknown'),
                        "language": voice['Locale'],  # Keep original format (en-US) for consistency with other providers
                        "display_name": voice.get('FriendlyName') or voice['ShortName']
                    }
                    for voice in all_voices
                    if voice['Locale'].lower() == filter_language.lower()
                ]
            else:
                # Return all voices or voices for the default language
                filtered_voices = [
                    {
                        "name": voice['ShortName'],
                        "gender": voice.get('Gender', 'Unknown'),
                        "language": voice['Locale'],  # Keep original format (en-US) for consistency with other providers
                        "display_name": voice.get('FriendlyName') or voice['ShortName']
                    }
                    for voice in all_voices
                ]

            logger.info(f"Retrieved {len(filtered_voices)} voices for language filter: {filter_language}")
            return filtered_voices

        except Exception as e:
            logger.error(f"Failed to get available voices: {e}", exc_info=True)
            return []
    
    @staticmethod
    def get_supported_models() -> List[Dict[str, str]]:
        """
        Get list of supported TTS models (OpenAI compatible).
        
        Returns:
            List of model information dictionaries
        """
        return TTS_MODELS
    
    @staticmethod
    def get_models_formatted() -> List[Dict[str, str]]:
        """
        Get formatted list of models (ID only format).
        
        Returns:
            List of model IDs in format: [{"id": "tts-1"}, ...]
        """
        return [{"id": model["id"]} for model in TTS_MODELS]
    
    @staticmethod
    def get_voices_formatted() -> List[Dict[str, str]]:
        """
        Get formatted list of OpenAI-compatible voices.

        Returns:
            List of voice mappings in format: [{"id": "alloy", "name": "en-US-JennyNeural"}, ...]
        """
        return [{"id": k, "name": v} for k, v in VOICE_MAPPING.items()]

    async def validate_voice(self, voice_name: str) -> bool:
        """
        Validate if a voice is available for Edge TTS.

        Args:
            voice_name: Voice name to validate

        Returns:
            True if voice is available, False otherwise
        """
        try:
            if not EDGE_TTS_AVAILABLE or edge_tts is None:
                return False

            all_voices = await edge_tts.list_voices()
            voice_names = [voice['ShortName'] for voice in all_voices]
            is_valid = voice_name in voice_names

            if not is_valid:
                logger.warning(f"Voice '{voice_name}' not found in Edge TTS voices. Available voices: {voice_names[:10]}...")

            return is_valid

        except Exception as e:
            logger.error(f"Failed to validate voice '{voice_name}': {e}", exc_info=True)
            return False


# Global service instance
edge_tts_service = EdgeTTSService()