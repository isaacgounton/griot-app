"""
Enhanced STT (Speech-to-Text) Service

Delegates transcription to the Speaches sidecar via the stt_client helper.
"""
import os
import tempfile
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from loguru import logger

from app.services.speaches.stt_client import transcribe_audio
from app.services.s3.s3 import s3_service
from app.utils.media import download_media_file

# Map short model size names to Speaches model identifiers
_MODEL_SIZE_MAP = {
    "tiny": "Systran/faster-whisper-tiny",
    "base": "Systran/faster-whisper-base",
    "small": "Systran/faster-whisper-small",
    "medium": "Systran/faster-whisper-medium",
    "large": "Systran/faster-whisper-large-v3",
    "large-v1": "Systran/faster-whisper-large-v1",
    "large-v2": "Systran/faster-whisper-large-v2",
    "large-v3": "Systran/faster-whisper-large-v3",
}


class STTService:
    """
    Enhanced Speech-to-Text service using Speaches sidecar.

    Provides high-quality transcription with word-level timestamps.
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "auto",
        compute_type: str = "int8"
    ):
        """
        Initialize STT service.

        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
            device: Kept for API compatibility (unused, model runs in Speaches sidecar)
            compute_type: Kept for API compatibility (unused, model runs in Speaches sidecar)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._speaches_model = _MODEL_SIZE_MAP.get(model_size, f"Systran/faster-whisper-{model_size}")
        logger.info(f"STTService initialized with speaches model: {self._speaches_model}")

    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        beam_size: int = 5,
        vad_filter: bool = True,
        vad_threshold: float = 0.35,
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Transcribe audio file to text with timestamps.

        Args:
            audio_path: Path to audio file
            language: Language code (optional, auto-detect if None)
            beam_size: Kept for API compatibility (unused, controlled by Speaches)
            vad_filter: Kept for API compatibility (unused, controlled by Speaches)
            vad_threshold: Kept for API compatibility (unused, controlled by Speaches)

        Returns:
            Tuple of (captions list, audio duration)
        """
        if not os.path.exists(audio_path):
            logger.bind(audio_path=audio_path).error("Audio file not found")
            return [], 0.0

        context_logger = logger.bind(
            audio_path=audio_path,
            language=language,
            model=self._speaches_model,
        )

        try:
            context_logger.debug("Starting Speaches transcription")

            # Call the Speaches sidecar via the stt_client helper
            segments, info = await transcribe_audio(
                file_path=audio_path,
                model=self._speaches_model,
                language=language,
                word_timestamps=True,
            )

            duration = info.duration
            captions = []

            # Extract word-level timestamps
            for segment in segments:
                if segment.words:
                    for word in segment.words:
                        captions.append({
                            "text": word.word.strip(),
                            "start_ts": float(word.start),
                            "end_ts": float(word.end),
                        })
                else:
                    # Fallback: use segment-level timestamps
                    captions.append({
                        "text": segment.text.strip(),
                        "start_ts": float(segment.start),
                        "end_ts": float(segment.end),
                    })

            context_logger.bind(
                caption_count=len(captions),
                duration=duration
            ).info("Speaches transcription completed")

            return captions, duration

        except Exception as e:
            context_logger.bind(error=str(e)).error("Speaches transcription failed")
            return [], 0.0

    async def transcribe_url(
        self,
        audio_url: str,
        language: Optional[str] = None,
        **kwargs
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Transcribe audio from URL.

        Args:
            audio_url: URL to audio file
            language: Language code (optional)
            **kwargs: Additional transcription parameters

        Returns:
            Tuple of (captions list, audio duration)
        """
        try:
            # Download audio file
            audio_path, _ = await download_media_file(audio_url)
            if not audio_path:
                logger.bind(audio_url=audio_url).error("Failed to download audio file")
                return [], 0.0

            # Transcribe
            captions, duration = await self.transcribe(audio_path, language, **kwargs)

            # Clean up downloaded file
            try:
                os.remove(audio_path)
            except Exception as e:
                logger.bind(audio_path=audio_path, error=str(e)).warning("Failed to clean up audio file")

            return captions, duration

        except Exception as e:
            logger.bind(audio_url=audio_url, error=str(e)).error("URL transcription failed")
            return [], 0.0

    async def process_job(self, job_id: str, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an STT job.

        Args:
            job_id: Job ID
            job_data: Job data containing audio_url, language, etc.

        Returns:
            Job result dictionary
        """
        try:
            audio_url = job_data["audio_url"]
            language = job_data.get("language")
            beam_size = job_data.get("beam_size", 5)
            vad_filter = job_data.get("vad_filter", True)
            vad_threshold = job_data.get("vad_threshold", 0.35)

            # Convert Pydantic URL objects to strings
            audio_url = str(audio_url) if audio_url else None

            # Transcribe audio
            captions, duration = await self.transcribe_url(
                audio_url,
                language=language,
                beam_size=beam_size,
                vad_filter=vad_filter,
                vad_threshold=vad_threshold,
            )

            if captions:
                return {
                    "status": "completed",
                    "captions": captions,
                    "duration": duration,
                    "language": language,
                    "caption_count": len(captions),
                }
            else:
                return {
                    "status": "failed",
                    "error": "Transcription failed or no speech detected"
                }

        except Exception as e:
            logger.bind(error=str(e), job_id=job_id).error("STT job processing failed")
            return {
                "status": "failed",
                "error": str(e)
            }


# Create STT service instance
stt_service = STTService()
