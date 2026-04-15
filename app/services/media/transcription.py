"""
Enhanced transcription service using the Speaches sidecar for STT.

This service delegates transcription to the Speaches sidecar (which runs
faster-whisper under the hood) via its OpenAI-compatible API, removing the
need to load whisper models in-process.
"""
import asyncio
import tempfile
import os
import logging
import subprocess
import json
from typing import Dict, Any, List, Tuple, Optional

from app.services.speaches.speaches_client import speaches_client
from app.services.s3.s3 import s3_service
from app.utils.media import download_media_file

logger = logging.getLogger(__name__)

# Map short model size names to Speaches model identifiers
_MODEL_SIZE_MAP = {
    "tiny": "Systran/faster-whisper-tiny",
    "base": "Systran/faster-whisper-base",
    "small": "Systran/faster-whisper-small",
    "medium": "Systran/faster-whisper-medium",
    "large-v1": "Systran/faster-whisper-large-v1",
    "large-v2": "Systran/faster-whisper-large-v2",
    "large-v3": "Systran/faster-whisper-large-v3",
}


class TranscriptionService:
    """Enhanced transcription service using the Speaches sidecar."""

    def __init__(self, model_size="base", compute_type="int8"):
        """
        Initialize transcription service.

        Args:
            model_size: Model size - tiny, base, small, medium, large-v1, large-v2, large-v3
            compute_type: Kept for API compatibility (unused, model runs in Speaches sidecar)
        """
        self.model_size = model_size
        self.compute_type = compute_type
        self._speaches_model = _MODEL_SIZE_MAP.get(model_size, f"Systran/faster-whisper-{model_size}")
        logger.info(f"Initialized TranscriptionService with speaches model: {self._speaches_model}")

    async def download_media(self, media_url: str) -> Tuple[str, str]:
        """
        Download media file from URL.

        Args:
            media_url: URL of the media file

        Returns:
            Tuple of (local file path, file extension)
        """
        return await download_media_file(media_url, temp_dir="temp")

    async def transcribe(
        self,
        file_path: str,
        include_text: bool = True,
        include_srt: bool = True,
        word_timestamps: bool = False,
        include_segments: bool = False,
        language: Optional[str] = None,
        max_words_per_line: int = 10,
        model_name: str = "base",  # Keep for compatibility but use instance model
        beam_size: int = 5,
        temperature: float = 0.0,
        initial_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe media file using the Speaches sidecar.

        Args:
            file_path: Path to media file
            include_text: Whether to include plain text transcription in the result
            include_srt: Whether to include SRT format
            word_timestamps: Whether to include word-level timestamps
            include_segments: Whether to include timestamped segments
            language: Source language code (optional)
            max_words_per_line: Maximum number of words per line in SRT (default: 10)
            model_name: Kept for compatibility (uses instance model)
            beam_size: Kept for API compatibility (unused, controlled by Speaches)

        Returns:
            Dict containing the transcription results (same format as old service)
        """
        processed_file = None
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            logger.info(f"Starting Speaches transcription for: {file_path}")

            # Preprocess audio file to ensure compatibility
            processed_file = await self._preprocess_audio(file_path)

            # Run transcription via Speaches sidecar (async, no thread pool needed)
            result = await self._transcribe_async(
                processed_file, word_timestamps, language,
                temperature=temperature, initial_prompt=initial_prompt,
            )

            # Prepare response in same format as old service
            response = {}

            # Include text if requested
            if include_text:
                response["text"] = result["text"]

            # Include word timestamps if requested
            if word_timestamps:
                response["words"] = result["words"]

            # Include segments if requested
            if include_segments:
                response["segments"] = result["segments"]

            # Generate and save SRT if requested
            if include_srt and result.get('segments'):
                srt_path = file_path + ".srt"
                self._generate_srt(result['segments'], srt_path, max_words_per_line)

                # Upload SRT to S3
                srt_object_name = os.path.basename(srt_path)
                srt_url = await s3_service.upload_file(srt_path, f"transcriptions/{srt_object_name}")

                # Remove signature parameters from URL
                if '?' in srt_url:
                    srt_url = srt_url.split('?')[0]

                response["srt_url"] = srt_url

                # Delete local SRT file
                os.unlink(srt_path)

            # Add metadata
            response.update({
                "duration": result["duration"],
                "language": result["language"],
                "language_probability": result.get("language_probability", 1.0)
            })

            logger.info(f"Transcription completed successfully. Duration: {result.get('duration', 0):.2f}s")
            return response

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Transcription failed: {str(e)}")
        finally:
            # Clean up the downloaded file
            if os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    logger.info(f"Deleted temporary file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {file_path}: {e}")

            # Clean up the processed file if it's different from the original
            if processed_file and processed_file != file_path and os.path.exists(processed_file):
                try:
                    os.unlink(processed_file)
                    logger.info(f"Deleted processed audio file: {processed_file}")
                except Exception as e:
                    logger.warning(f"Failed to delete processed file {processed_file}: {e}")

    async def _transcribe_async(
        self,
        audio_path: str,
        word_timestamps: bool,
        language: Optional[str] = None,
        temperature: float = 0.0,
        initial_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe audio via the Speaches sidecar.

        Args:
            audio_path: Path to audio file
            word_timestamps: Include word timestamps
            language: Language code or None for auto-detection
            temperature: Sampling temperature (0 = deterministic)
            initial_prompt: Optional text to guide the model

        Returns:
            Transcription results
        """
        logger.info(f"Starting Speaches transcription with model: {self._speaches_model}")

        try:
            # Call the Speaches sidecar via its OpenAI-compatible API
            raw = await speaches_client.transcribe(
                file_path=audio_path,
                model=self._speaches_model,
                language=language,
                response_format="verbose_json",
                temperature=temperature,
                prompt=initial_prompt,
                timestamp_granularities=["word", "segment"] if word_timestamps else None,
            )

            # Extract metadata
            duration = raw.get("duration", 0.0)
            detected_language = raw.get("language", language or "en")
            language_probability = raw.get("language_probability", 1.0) if "language_probability" in raw else 1.0

            logger.info(f"Detected language: {detected_language}")

            # Convert segments to the same dict format the rest of the codebase expects
            raw_segments = raw.get("segments", [])
            all_segments = []
            word_timestamps_list = []
            full_text = ""

            for i, seg in enumerate(raw_segments):
                segment_dict = {
                    "id": i,
                    "start": seg.get("start", 0.0),
                    "end": seg.get("end", 0.0),
                    "text": seg.get("text", "").strip(),
                    "avg_logprob": seg.get("avg_logprob", 0.0),
                    "no_speech_prob": seg.get("no_speech_prob", 0.0),
                    "duration": seg.get("end", 0.0) - seg.get("start", 0.0),
                }
                all_segments.append(segment_dict)
                full_text += seg.get("text", "") + " "

                # Process word-level timestamps
                if word_timestamps and "words" in seg:
                    for w in seg["words"]:
                        word_timestamps_list.append({
                            "word": w.get("word", ""),
                            "start": w.get("start", 0.0),
                            "end": w.get("end", 0.0),
                            "probability": w.get("probability", 1.0),
                        })

            result = {
                "text": full_text.strip(),
                "duration": duration,
                "language": detected_language,
                "language_probability": language_probability,
                "segments": all_segments,
                "words": word_timestamps_list if word_timestamps else [],
            }

            logger.info(f"Transcription completed: {len(all_segments)} segments, {len(word_timestamps_list)} words")
            return result

        except Exception as e:
            logger.error(f"Speaches transcription failed: {e}")
            raise

    def _generate_srt(self, segments: List[Dict], output_path: str, max_words_per_line: int = 10):
        """
        Generate SRT file from transcription result with controlled line length.

        Args:
            segments: List of segment dictionaries
            output_path: Path to save the SRT file
            max_words_per_line: Maximum number of words per line (default: 10)
        """
        with open(output_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, start=1):
                start_time = self._format_timestamp(segment["start"])
                end_time = self._format_timestamp(segment["end"])
                text = segment["text"].strip()

                # Apply max words per line formatting
                formatted_text = self._format_text_with_max_words(text, max_words_per_line)

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{formatted_text}\n\n")

        logger.info(f"Generated SRT file with max {max_words_per_line} words per line: {output_path}")

    def _format_text_with_max_words(self, text: str, max_words_per_line: int) -> str:
        """
        Format text with a maximum number of words per line.

        Args:
            text: The text to format
            max_words_per_line: Maximum number of words per line

        Returns:
            Formatted text with line breaks
        """
        words = text.split()
        if len(words) <= max_words_per_line:
            return text

        formatted_lines = []
        for i in range(0, len(words), max_words_per_line):
            line = ' '.join(words[i:i+max_words_per_line])
            formatted_lines.append(line)

        return '\n'.join(formatted_lines)

    def _format_timestamp(self, seconds: float) -> str:
        """
        Format seconds as SRT timestamp: HH:MM:SS,mmm

        Args:
            seconds: Time in seconds

        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)

        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

    async def _preprocess_audio(self, file_path: str) -> str:
        """
        Preprocess audio file to ensure compatibility with Speaches STT.

        This method handles problematic audio codecs and formats by converting
        them to a standard format that the STT service can reliably process.

        Args:
            file_path: Path to the original media file

        Returns:
            Path to the preprocessed audio file (may be the same as input if no preprocessing needed)

        Raises:
            RuntimeError: If preprocessing fails
        """
        try:
            # First, try to get media info to understand the file format
            logger.info(f"Analyzing audio format for: {file_path}")

            # Use ffprobe to check the audio streams
            ffprobe_cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_streams", "-select_streams", "a:0", file_path
            ]

            try:
                result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
                probe_data = json.loads(result.stdout)

                # Check if we have audio streams
                if not probe_data.get("streams"):
                    logger.warning(f"No audio streams found in {file_path}")
                    # Try to extract audio from video
                    return await self._extract_audio_from_video(file_path)

                audio_stream = probe_data["streams"][0]
                codec_name = audio_stream.get("codec_name", "unknown")
                logger.info(f"Detected audio codec: {codec_name}")

                # Check if the codec is problematic for STT
                problematic_codecs = ["aac", "mp3", "opus", "vorbis", "flac"]

                if codec_name in problematic_codecs or codec_name == "unknown":
                    logger.info(f"Audio codec {codec_name} may cause issues, converting to WAV")
                    return await self._convert_to_wav(file_path)
                else:
                    logger.info(f"Audio codec {codec_name} should work fine, using original file")
                    return file_path

            except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to analyze audio format: {e}, attempting conversion")
                # If we can't analyze the file, try converting it
                return await self._convert_to_wav(file_path)

        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            # If preprocessing fails, try using the original file
            logger.warning("Using original file despite preprocessing failure")
            return file_path

    async def _extract_audio_from_video(self, file_path: str) -> str:
        """
        Extract audio track from video file.

        Args:
            file_path: Path to the video file

        Returns:
            Path to the extracted audio file

        Raises:
            RuntimeError: If extraction fails
        """
        try:
            # Create output file with .wav extension
            base_name = os.path.splitext(file_path)[0]
            audio_file = f"{base_name}_audio.wav"

            logger.info(f"Extracting audio from video: {file_path} -> {audio_file}")

            # Use ffmpeg to extract audio and convert to WAV
            ffmpeg_cmd = [
                "ffmpeg", "-i", file_path,
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # PCM 16-bit little-endian
                "-ar", "16000",  # 16kHz sample rate (good for Whisper)
                "-ac", "1",  # Mono
                "-y",  # Overwrite output file
                audio_file
            ]

            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True)

            if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
                logger.info(f"Successfully extracted audio: {audio_file}")
                return audio_file
            else:
                raise RuntimeError("Extracted audio file is empty or doesn't exist")

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            logger.error(f"FFmpeg audio extraction failed: {error_msg}")
            raise RuntimeError(f"Failed to extract audio: {error_msg}")

    async def _convert_to_wav(self, file_path: str) -> str:
        """
        Convert audio file to WAV format for better compatibility.

        Args:
            file_path: Path to the original audio/video file

        Returns:
            Path to the converted WAV file

        Raises:
            RuntimeError: If conversion fails
        """
        try:
            # Create output file with .wav extension
            base_name = os.path.splitext(file_path)[0]
            wav_file = f"{base_name}_converted.wav"

            logger.info(f"Converting to WAV: {file_path} -> {wav_file}")

            # Use ffmpeg to convert to standard WAV format
            ffmpeg_cmd = [
                "ffmpeg", "-i", file_path,
                "-acodec", "pcm_s16le",  # PCM 16-bit little-endian
                "-ar", "16000",  # 16kHz sample rate (optimal for Whisper)
                "-ac", "1",  # Mono (reduces processing time)
                "-y",  # Overwrite output file
                wav_file
            ]

            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True)

            if os.path.exists(wav_file) and os.path.getsize(wav_file) > 0:
                logger.info(f"Successfully converted to WAV: {wav_file}")
                return wav_file
            else:
                raise RuntimeError("Converted WAV file is empty or doesn't exist")

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            logger.error(f"FFmpeg conversion failed: {error_msg}")
            raise RuntimeError(f"Failed to convert audio: {error_msg}")

    async def process_media_transcription(self, job_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process media transcription job - compatible with existing job queue system.

        Args:
            job_id: Job identifier (unused but required for job queue signature)
            data: Job parameters

        Returns:
            Transcription results in expected format
        """
        try:
            # Extract parameters with defaults matching old service
            media_url = data.get('media_url')
            file_path = data.get('file_path')  # Direct file path (from file upload)
            include_text = data.get('include_text', True)
            include_srt = data.get('include_srt', True)
            word_timestamps = data.get('word_timestamps', False)
            include_segments = data.get('include_segments', False)
            language = data.get('language')
            max_words_per_line = data.get('max_words_per_line', 10)
            beam_size = data.get('beam_size', 5)  # Kept for API compatibility
            model_size = data.get('model_size', 'base')
            temperature = data.get('temperature', 0.0)
            initial_prompt = data.get('initial_prompt')

            # Resolve the model to use for this request
            speaches_model = _MODEL_SIZE_MAP.get(model_size, f"Systran/faster-whisper-{model_size}")
            # Temporarily override instance model for this request
            original_model = self._speaches_model
            self._speaches_model = speaches_model

            if not media_url and not file_path:
                raise ValueError("media_url or file_path is required")

            if file_path:
                logger.info(f"Processing transcription job {job_id} for uploaded file: {file_path}")
            else:
                logger.info(f"Processing transcription job {job_id} for: {media_url}")
                # Download media file
                file_path, _ = await self.download_media(str(media_url))

            # Perform transcription using Speaches sidecar
            result = await self.transcribe(
                file_path=file_path,
                include_text=include_text,
                include_srt=include_srt,
                word_timestamps=word_timestamps,
                include_segments=include_segments,
                language=language,
                max_words_per_line=max_words_per_line,
                beam_size=beam_size,
                temperature=temperature,
                initial_prompt=initial_prompt,
            )
            # Restore original model
            self._speaches_model = original_model

            logger.info(f"Transcription job {job_id} completed successfully")
            return result

        except Exception as e:
            logger.error(f"Transcription job {job_id} failed: {str(e)}")
            raise Exception(f"Transcription failed: {str(e)}")

# Lazy-loaded singleton instance
transcription_service = None

def get_transcription_service():
    """Get or create transcription service instance."""
    global transcription_service
    if transcription_service is None:
        transcription_service = TranscriptionService(model_size="base", compute_type="int8")
    return transcription_service
