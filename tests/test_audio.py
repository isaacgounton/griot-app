"""
Tests for audio-related API endpoints.

Covers:
- POST /api/v1/audio/speech - TTS generation
- GET  /api/v1/audio/voices/all - all voices
- GET  /api/v1/audio/voices/formatted - formatted voices
- GET  /api/v1/audio/providers - provider info
- GET  /api/v1/audio/tts/providers - frontend-compatible providers
- GET  /api/v1/audio/models - TTS models
- GET  /api/v1/audio/capabilities - TTS capabilities
- GET  /api/v1/audio/audio-formats - audio format info
- POST /api/v1/audio/voice-sample - voice sample generation
- POST /api/v1/audio/transcriptions - transcription
- POST /api/v1/audio/music - music generation
- GET  /api/v1/audio/music/info - music generation info

NOTE: GET /api/v1/audio/voices is shadowed by the openai_compat router which
registers GET /audio/voices at /api/v1, using get_current_user instead of
get_api_key. Tests that hit that path need special handling.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

PREFIX = "/api/v1/audio"


@pytest.fixture(autouse=True)
def _clear_rate_limits():
    """Reset SecurityMiddleware rate limiting state before each test."""
    from app.middleware.security import SecurityMiddleware
    instance = SecurityMiddleware.get_instance()
    if instance:
        instance.request_count.clear()
    yield


# ── TTS Speech endpoint ─────────────────────────────────────────────────────

class TestSpeechEndpoint:
    """Tests for POST /api/v1/audio/speech."""

    def test_speech_missing_text(self, client):
        """Should reject request with no text or input field (400 from TTS validation)."""
        response = client.post(f"{PREFIX}/speech", json={})
        assert response.status_code == 400

    def test_speech_empty_text(self, client):
        """Should reject empty text string."""
        response = client.post(f"{PREFIX}/speech", json={"text": ""})
        assert response.status_code in (400, 422)

    @patch("app.routes.audio.text_to_speech.job_queue")
    @patch("app.routes.audio.text_to_speech.tts_service")
    @patch("app.routes.audio.text_to_speech.validate_tts_request")
    def test_speech_creates_job(self, mock_validate, mock_tts, mock_jq, client):
        """Valid TTS request should create an async job and return job_id."""
        mock_validate.return_value = {
            "text": "Hello world",
            "provider": "kokoro",
            "voice": "af_heart",
            "response_format": "mp3",
            "speed": 1.0,
            "volume_multiplier": 1.0,
            "stream": False,
            "sync": False,
            "stream_format": "audio",
            "remove_filter": False,
        }
        mock_jq.add_job = AsyncMock()

        response = client.post(
            f"{PREFIX}/speech",
            json={"text": "Hello world"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    @patch("app.routes.audio.text_to_speech.tts_service")
    @patch("app.routes.audio.text_to_speech.validate_tts_request")
    def test_speech_sync_mode(self, mock_validate, mock_tts, client):
        """Sync mode should return result immediately."""
        mock_validate.return_value = {
            "text": "Hello sync",
            "provider": "kokoro",
            "voice": "af_heart",
            "response_format": "mp3",
            "speed": 1.0,
            "volume_multiplier": 1.0,
            "stream": False,
            "sync": True,
            "stream_format": "audio",
            "remove_filter": False,
        }
        mock_tts.process_text_to_speech = AsyncMock(return_value={
            "audio_url": "https://s3.example.com/audio.mp3",
            "tts_engine": "kokoro",
        })

        response = client.post(
            f"{PREFIX}/speech",
            json={"text": "Hello sync", "sync": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["result"] is not None

    def test_speech_input_field_compatibility(self, client):
        """OpenAI-compatible 'input' field should also be accepted."""
        with patch("app.routes.audio.text_to_speech.job_queue") as mock_jq, \
             patch("app.routes.audio.text_to_speech.tts_service"), \
             patch("app.routes.audio.text_to_speech.validate_tts_request") as mock_validate:
            mock_validate.return_value = {
                "text": "Hello via input",
                "provider": "kokoro",
                "voice": "af_heart",
                "response_format": "mp3",
                "speed": 1.0,
                "volume_multiplier": 1.0,
                "stream": False,
                "sync": False,
                "stream_format": "audio",
                "remove_filter": False,
            }
            mock_jq.add_job = AsyncMock()

            response = client.post(
                f"{PREFIX}/speech",
                json={"input": "Hello via input"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data

    def test_speech_speed_out_of_range(self, client):
        """Speed > 2.0 should be rejected by Pydantic validation."""
        response = client.post(
            f"{PREFIX}/speech",
            json={"text": "Hello", "speed": 5.0},
        )
        assert response.status_code == 422

    def test_speech_volume_out_of_range(self, client):
        """Volume multiplier > 3.0 should be rejected by Pydantic validation."""
        response = client.post(
            f"{PREFIX}/speech",
            json={"text": "Hello", "volume_multiplier": 10.0},
        )
        assert response.status_code == 422

    def test_speech_text_too_long(self, client):
        """Text exceeding max_length should be rejected."""
        long_text = "x" * 5001
        response = client.post(
            f"{PREFIX}/speech",
            json={"text": long_text},
        )
        assert response.status_code == 422


# ── Voices endpoints ─────────────────────────────────────────────────────────

class TestVoicesEndpoints:
    """Tests for voice listing endpoints.

    NOTE: GET /api/v1/audio/voices is shadowed by the openai_compat router,
    so we skip that path and test /voices/all and /voices/formatted which
    are NOT shadowed.
    """

    @patch("app.routes.audio.text_to_speech.tts_service")
    def test_get_all_voices(self, mock_tts, client):
        """GET /voices/all should return all voices wrapped in voices key."""
        mock_tts.get_available_voices = AsyncMock(return_value={
            "kokoro": [{"name": "af_heart"}],
        })
        response = client.get(f"{PREFIX}/voices/all")
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data

    @patch("app.routes.audio.text_to_speech.tts_service")
    def test_get_voices_formatted(self, mock_tts, client):
        """GET /voices/formatted should return formatted voice list."""
        mock_tts.get_voices_formatted = MagicMock(return_value={
            "kokoro": [{"id": "af_heart", "name": "Heart"}],
        })
        response = client.get(f"{PREFIX}/voices/formatted")
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data


# ── Providers endpoints ──────────────────────────────────────────────────────

class TestProvidersEndpoints:
    """Tests for provider info endpoints."""

    @patch("app.routes.audio.text_to_speech.tts_service")
    def test_get_providers(self, mock_tts, client):
        """GET /providers should return providers, formats, models, default_provider."""
        mock_tts.get_supported_providers = MagicMock(return_value=["kokoro", "edge", "piper"])
        mock_tts.get_supported_formats = MagicMock(return_value={"kokoro": ["mp3", "wav"]})
        mock_tts.get_models = MagicMock(return_value={"kokoro": [{"id": "kokoro-v1"}]})
        mock_tts.default_provider = "kokoro"

        response = client.get(f"{PREFIX}/providers")
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert "formats" in data
        assert "models" in data
        assert "default_provider" in data

    @patch("app.routes.audio.text_to_speech.tts_service")
    def test_get_tts_providers_frontend(self, mock_tts, client):
        """GET /tts/providers should return frontend-compatible format."""
        mock_tts.get_supported_providers = MagicMock(return_value=["kokoro", "edge"])
        response = client.get(f"{PREFIX}/tts/providers")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    @patch("app.routes.audio.text_to_speech.tts_service")
    def test_get_voices_for_provider(self, mock_tts, client):
        """GET /tts/{provider}/voices should return voices for that provider."""
        mock_tts.get_available_voices = AsyncMock(return_value={
            "kokoro": [{"name": "af_heart"}],
        })
        response = client.get(f"{PREFIX}/tts/kokoro/voices")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data


# ── Models endpoints ─────────────────────────────────────────────────────────

class TestModelsEndpoints:
    """Tests for model listing endpoints.

    NOTE: GET /api/v1/audio/models is shadowed by openai_compat which registers
    GET /audio/models at /api/v1 using get_current_user. We test /models/formatted
    instead.
    """

    @patch("app.routes.audio.text_to_speech.tts_service")
    def test_get_models_formatted(self, mock_tts, client):
        """GET /models/formatted should return formatted models."""
        mock_tts.get_models_formatted = MagicMock(return_value=[
            {"id": "kokoro-v1", "name": "Kokoro V1"},
        ])
        response = client.get(f"{PREFIX}/models/formatted")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data


# ── Capabilities endpoint ────────────────────────────────────────────────────

class TestCapabilitiesEndpoint:
    """Tests for GET /capabilities."""

    def test_get_capabilities(self, client):
        """GET /capabilities should return provider capabilities."""
        response = client.get(f"{PREFIX}/capabilities")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "capabilities" in data
        caps = data["capabilities"]
        assert "providers" in caps
        assert "formats" in caps
        assert "speed_ranges" in caps


# ── Audio formats endpoint ───────────────────────────────────────────────────

class TestAudioFormatsEndpoints:
    """Tests for audio format endpoints."""

    def test_get_audio_formats(self, client):
        """GET /audio-formats should return format info and compatibility matrix."""
        response = client.get(f"{PREFIX}/audio-formats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "formats" in data
        assert "compatibility_matrix" in data

    def test_get_specific_format_info(self, client):
        """GET /audio-formats/mp3 should return info for mp3 format."""
        response = client.get(f"{PREFIX}/audio-formats/mp3")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "format" in data


# ── Voice sample endpoint ────────────────────────────────────────────────────

class TestVoiceSampleEndpoint:
    """Tests for POST /voice-sample."""

    @patch("app.services.s3.s3_service")
    @patch("app.routes.audio.text_to_speech.tts_service")
    def test_voice_sample_success(self, mock_tts, mock_s3_svc, client):
        """POST /voice-sample should generate and upload a sample."""
        mock_tts.generate_speech = AsyncMock(return_value=(b"audio-bytes", "kokoro"))
        mock_s3_svc.upload_file = AsyncMock(return_value="https://s3.example.com/sample.mp3")

        response = client.post(
            f"{PREFIX}/voice-sample",
            params={"voice": "af_heart", "provider": "kokoro"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "audio_url" in data
        assert data["voice"] == "af_heart"
        assert data["provider"] == "kokoro"

    def test_voice_sample_missing_voice(self, client):
        """POST /voice-sample without voice param should fail."""
        response = client.post(
            f"{PREFIX}/voice-sample",
            params={"provider": "kokoro"},
        )
        assert response.status_code == 422

    def test_voice_sample_missing_provider(self, client):
        """POST /voice-sample without provider param should fail."""
        response = client.post(
            f"{PREFIX}/voice-sample",
            params={"voice": "af_heart"},
        )
        assert response.status_code == 422


# ── Transcription endpoints ──────────────────────────────────────────────────

class TestTranscriptionEndpoints:
    """Tests for POST /transcriptions."""

    def test_transcription_missing_media_url(self, client):
        """Should reject request without media_url."""
        response = client.post(f"{PREFIX}/transcriptions", json={})
        assert response.status_code == 422

    def test_transcription_invalid_url(self, client):
        """Should reject request with invalid URL."""
        response = client.post(
            f"{PREFIX}/transcriptions",
            json={"media_url": "not-a-url"},
        )
        assert response.status_code == 422

    @patch("app.routes.audio.transcription.job_queue")
    @patch("app.routes.audio.transcription.get_transcription_service")
    def test_transcription_creates_job(self, mock_get_svc, mock_jq, client):
        """Valid transcription request should create async job."""
        mock_jq.add_job = AsyncMock()
        response = client.post(
            f"{PREFIX}/transcriptions",
            json={"media_url": "https://example.com/audio.mp3"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    @patch("app.routes.audio.transcription.get_transcription_service")
    def test_transcription_sync_mode(self, mock_get_svc, client):
        """Sync transcription should return result immediately."""
        mock_svc = MagicMock()
        mock_svc.process_media_transcription = AsyncMock(return_value={
            "text": "Hello world",
            "srt": "1\n00:00:00,000 --> 00:00:01,000\nHello world",
        })
        mock_get_svc.return_value = mock_svc

        response = client.post(
            f"{PREFIX}/transcriptions",
            json={
                "media_url": "https://example.com/audio.mp3",
                "sync": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["result"] is not None


# ── Music generation endpoints ───────────────────────────────────────────────

class TestMusicGenerationEndpoints:
    """Tests for POST /music and GET /music/info."""

    def test_music_info(self, client):
        """GET /music/info should return music generation capabilities."""
        response = client.get(f"{PREFIX}/music/info")
        assert response.status_code == 200
        data = response.json()
        assert "model_info" in data
        assert "parameters" in data
        assert "examples" in data

    def test_music_missing_description(self, client):
        """Should reject request without description."""
        response = client.post(f"{PREFIX}/music", json={})
        assert response.status_code == 422

    def test_music_empty_description(self, client):
        """Should reject empty description."""
        response = client.post(
            f"{PREFIX}/music",
            json={"description": ""},
        )
        assert response.status_code == 400

    def test_music_description_too_long(self, client):
        """Should reject description exceeding 500 characters."""
        response = client.post(
            f"{PREFIX}/music",
            json={"description": "x" * 501},
        )
        assert response.status_code == 400

    def test_music_invalid_model_size(self, client):
        """Should reject invalid model_size."""
        response = client.post(
            f"{PREFIX}/music",
            json={"description": "lo-fi beats", "model_size": "large"},
        )
        assert response.status_code == 400

    def test_music_invalid_output_format(self, client):
        """Should reject invalid output_format."""
        response = client.post(
            f"{PREFIX}/music",
            json={"description": "lo-fi beats", "output_format": "ogg"},
        )
        assert response.status_code == 400

    @patch("app.routes.audio.music.job_queue")
    @patch("app.routes.audio.music.music_generation_service")
    def test_music_creates_job(self, mock_svc, mock_jq, client):
        """Valid music request should create async job."""
        mock_jq.add_job = AsyncMock()
        response = client.post(
            f"{PREFIX}/music",
            json={"description": "lo-fi music with a soothing melody"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    def test_music_duration_out_of_range(self, client):
        """Duration outside 1-30 should be rejected."""
        response = client.post(
            f"{PREFIX}/music",
            json={"description": "lo-fi beats", "duration": 0},
        )
        assert response.status_code == 422

        response = client.post(
            f"{PREFIX}/music",
            json={"description": "lo-fi beats", "duration": 31},
        )
        assert response.status_code == 422


# ── Voice discovery endpoint ─────────────────────────────────────────────────

class TestVoiceDiscoveryEndpoint:
    """Tests for GET /voices/discover."""

    @patch("app.routes.audio.text_to_speech.get_voice_options")
    @patch("app.routes.audio.text_to_speech.tts_service")
    def test_discover_voices(self, mock_tts, mock_voice_opts, client):
        """GET /voices/discover should return filtered voice list."""
        mock_tts.get_available_voices = AsyncMock(return_value={
            "kokoro": [{"name": "af_heart"}],
        })
        mock_voice_opts.return_value = {
            "voices": [{"name": "af_heart", "provider": "kokoro"}],
            "total": 1,
        }
        response = client.get(f"{PREFIX}/voices/discover")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    @patch("app.routes.audio.text_to_speech.get_voice_options")
    @patch("app.routes.audio.text_to_speech.tts_service")
    def test_discover_voices_with_filters(self, mock_tts, mock_voice_opts, client):
        """GET /voices/discover with filters should pass them through."""
        mock_tts.get_available_voices = AsyncMock(return_value={})
        mock_voice_opts.return_value = {"voices": [], "total": 0}
        response = client.get(
            f"{PREFIX}/voices/discover",
            params={"gender": "Female", "language": "en-US", "limit": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
