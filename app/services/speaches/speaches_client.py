"""OpenAI-compatible client for Speaches.ai sidecar service.

Speaches.ai provides TTS (Kokoro + Piper) and STT (faster-whisper) via an
OpenAI-compatible API. This client wraps the standard AsyncOpenAI SDK so the
rest of the codebase can call it without knowing the underlying transport.
"""

import os
import logging
from typing import Optional

import aiohttp
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Default base URL (docker-compose service name)
_DEFAULT_BASE_URL = "http://speaches:8000/v1"


class SpeachesClient:
    """Thin wrapper around AsyncOpenAI pointing at the Speaches sidecar."""

    def __init__(self) -> None:
        self._base_url = os.environ.get("SPEACHES_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")
        if not self._base_url.endswith("/v1"):
            self._base_url += "/v1"
        # Use SPEACHES_API_KEY if configured, otherwise a dummy key
        self._api_key = os.environ.get("SPEACHES_API_KEY", "") or "not-needed"
        self._client = AsyncOpenAI(base_url=self._base_url, api_key=self._api_key)
        logger.info(f"SpeachesClient initialized with base_url={self._base_url}")

    @property
    def raw_base(self) -> str:
        """Base URL without the /v1 suffix, for non-OpenAI endpoints."""
        return self._base_url.removesuffix("/v1")

    def _auth_headers(self) -> dict[str, str]:
        """Return auth headers for aiohttp calls if API key is configured."""
        if self._api_key and self._api_key != "not-needed":
            return {"Authorization": f"Bearer {self._api_key}"}
        return {}

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------
    async def health_check(self) -> bool:
        """Return True if the Speaches sidecar is reachable."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.raw_base}/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    return resp.status == 200
        except Exception as exc:
            logger.warning(f"Speaches health check failed: {exc}")
            return False

    # ------------------------------------------------------------------
    # TTS
    # ------------------------------------------------------------------
    async def generate_speech(
        self,
        text: str,
        voice: str = "af_heart",
        model: str = "speaches-ai/Kokoro-82M-v1.0-ONNX",
        response_format: str = "mp3",
        speed: float = 1.0,
    ) -> bytes:
        """Generate speech via the OpenAI-compatible TTS endpoint.

        Args:
            text: Input text.
            voice: Voice identifier (Kokoro or Piper voice name).
            model: TTS model name (e.g. "kokoro", a Piper model name).
            response_format: Output audio format (mp3, wav, opus, flac).
            speed: Playback speed multiplier.

        Returns:
            Raw audio bytes.
        """
        logger.info(f"Speaches TTS: model={model}, voice={voice}, format={response_format}, len={len(text)}")
        response = await self._client.audio.speech.create(
            model=model,
            voice=voice,  # type: ignore[arg-type]
            input=text,
            response_format=response_format,  # type: ignore[arg-type]
            speed=speed,
        )
        return response.read()

    # ------------------------------------------------------------------
    # STT
    # ------------------------------------------------------------------
    async def transcribe(
        self,
        file_path: str,
        model: str = "Systran/faster-whisper-base",
        language: Optional[str] = None,
        response_format: str = "verbose_json",
        temperature: float = 0.0,
        prompt: Optional[str] = None,
        timestamp_granularities: Optional[list[str]] = None,
    ) -> dict:
        """Transcribe audio via the OpenAI-compatible STT endpoint.

        Args:
            file_path: Path to the audio file on disk.
            model: Whisper model identifier.
            language: Optional language hint (ISO 639-1).
            response_format: Response format (json, verbose_json, text, srt, vtt).
            temperature: Sampling temperature (0 = deterministic).
            prompt: Optional text to guide the model's style.
            timestamp_granularities: Granularity levels, e.g. ["word", "segment"].

        Returns:
            Transcription result dict with 'text', 'segments', etc.
        """
        logger.info(f"Speaches STT: model={model}, lang={language}, temp={temperature}, file={file_path}")
        kwargs: dict = {
            "model": model,
            "language": language or "",
            "response_format": response_format,
            "temperature": temperature,
        }
        if prompt:
            kwargs["prompt"] = prompt
        if timestamp_granularities:
            kwargs["timestamp_granularities"] = timestamp_granularities
        with open(file_path, "rb") as audio_file:
            transcript = await self._client.audio.transcriptions.create(
                file=audio_file,
                **kwargs,  # type: ignore[arg-type]
            )
        # verbose_json returns an object with .text, .segments, etc.
        if hasattr(transcript, "model_dump"):
            return transcript.model_dump()
        # Handle unexpected response types gracefully
        try:
            return {"text": str(transcript), "raw_response": str(type(transcript))}
        except Exception as e:
            logger.error(f"Unexpected transcription response type: {type(transcript)}, error: {e}")
            return {"text": "", "error": f"Unexpected response type: {type(transcript)}"}

    # ------------------------------------------------------------------
    # Voice / Model discovery (non-OpenAI endpoints)
    # ------------------------------------------------------------------
    async def get_voices(self) -> list[dict]:
        """Fetch available TTS voices from Speaches."""
        try:
            async with aiohttp.ClientSession(headers=self._auth_headers()) as session:
                async with session.get(f"{self._base_url}/audio/voices") as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    return data if isinstance(data, list) else data.get("voices", [])
        except Exception as exc:
            logger.error(f"Failed to get Speaches voices: {exc}")
            return []

    async def get_models(self) -> list[dict]:
        """Fetch available models from Speaches."""
        try:
            models = await self._client.models.list()
            return [m.model_dump() for m in models.data]
        except Exception as exc:
            logger.error(f"Failed to get Speaches models: {exc}")
            return []

    # ------------------------------------------------------------------
    # VAD (Voice Activity Detection)
    # ------------------------------------------------------------------
    async def detect_speech_timestamps(self, file_path: str) -> list[dict]:
        """Detect speech timestamps using Speaches VAD endpoint."""
        try:
            async with aiohttp.ClientSession(headers=self._auth_headers()) as session:
                data = aiohttp.FormData()
                data.add_field("file", open(file_path, "rb"), filename=os.path.basename(file_path))
                async with session.post(f"{self._base_url}/audio/speech/timestamps", data=data) as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as exc:
            logger.error(f"Speaches VAD failed: {exc}")
            return []

    # ------------------------------------------------------------------
    # Model management
    # ------------------------------------------------------------------
    async def download_model(self, model_id: str) -> dict:
        """Request Speaches to download a model."""
        try:
            async with aiohttp.ClientSession(headers=self._auth_headers()) as session:
                async with session.post(f"{self._base_url}/models/{model_id}") as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as exc:
            logger.error(f"Failed to download model {model_id}: {exc}")
            return {"error": str(exc)}

    async def delete_model(self, model_id: str) -> dict:
        """Delete a model from Speaches."""
        try:
            async with aiohttp.ClientSession(headers=self._auth_headers()) as session:
                async with session.delete(f"{self._base_url}/models/{model_id}") as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as exc:
            logger.error(f"Failed to delete model {model_id}: {exc}")
            return {"error": str(exc)}


# Global singleton
speaches_client = SpeachesClient()
