"""Speaches.ai sidecar service clients for TTS and STT."""

from app.services.speaches.speaches_client import speaches_client
from app.services.speaches.stt_client import transcribe_audio

__all__ = ["speaches_client", "transcribe_audio"]
