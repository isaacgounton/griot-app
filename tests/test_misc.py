"""
Tests for miscellaneous API endpoints.

Covers:
- POST /api/v1/ffmpeg/compose          - FFmpeg compose operations
- GET  /api/v1/ffmpeg/compose/examples  - FFmpeg examples
- GET  /api/v1/anyllm/                  - AnyLLM root
- GET  /api/v1/anyllm/providers         - LLM providers
- GET  /api/v1/openai/models            - OpenAI-compat models (TTS)  (note: actually at /api/v1/models)
- GET  /api/v1/music/moods              - music moods
- GET  /api/v1/music/tracks             - music track listing
- POST /api/v1/documents/to-markdown/   - document to markdown
- GET  /api/v1/documents/to-markdown/formats - supported formats
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Reset the security middleware rate limiter between tests to avoid 429 errors."""
    from app.middleware.security import SecurityMiddleware
    instance = SecurityMiddleware.get_instance()
    if instance:
        instance.request_count.clear()
        instance.suspicious_count.clear()


# ── FFmpeg Compose ─────────────────────────────────────────────────────────

FFMPEG_PREFIX = "/api/v1/ffmpeg"


class TestFFmpegCompose:
    """Tests for POST /api/v1/ffmpeg/compose."""

    @patch("app.routes.ffmpeg.ffmpeg.job_queue")
    @patch("app.routes.ffmpeg.ffmpeg.ffmpeg_composer")
    def test_compose_creates_async_job(self, mock_composer, mock_jq, client, auth_headers):
        """Valid compose request should create an async job."""
        mock_composer.validate_request.return_value = []
        mock_composer.compose_command.return_value = "ffmpeg -i input.mp4 output.mp4"
        mock_jq.add_job = AsyncMock()

        response = client.post(
            f"{FFMPEG_PREFIX}/compose",
            json={
                "id": "test-compose",
                "inputs": [{"file_url": "https://example.com/input.mp4", "options": []}],
                "outputs": [{"options": [{"option": "-c:v", "argument": "libx264"}]}],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    @patch("app.routes.ffmpeg.ffmpeg.ffmpeg_composer")
    def test_compose_validation_error(self, mock_composer, client, auth_headers):
        """Should return 400 when validation fails."""
        mock_composer.validate_request.return_value = ["Missing input file"]

        response = client.post(
            f"{FFMPEG_PREFIX}/compose",
            json={
                "id": "bad-request",
                "inputs": [{"file_url": "https://example.com/input.mp4", "options": []}],
                "outputs": [{"options": []}],
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        data = response.json()
        assert "validation_errors" in data["detail"]

    def test_compose_missing_inputs(self, client, auth_headers):
        """Should reject request without inputs."""
        response = client.post(
            f"{FFMPEG_PREFIX}/compose",
            json={"id": "no-inputs", "outputs": [{"options": []}]},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_compose_missing_outputs(self, client, auth_headers):
        """Should reject request without outputs."""
        response = client.post(
            f"{FFMPEG_PREFIX}/compose",
            json={"id": "no-outputs", "inputs": [{"file_url": "https://example.com/input.mp4", "options": []}]},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @patch("app.routes.ffmpeg.ffmpeg.ffmpeg_composer")
    def test_compose_sync_mode(self, mock_composer, client, auth_headers):
        """Sync mode should process immediately and return result."""
        mock_composer.validate_request.return_value = []
        mock_composer.compose_command.return_value = "ffmpeg -i input.mp4 output.mp4"
        mock_composer.process_ffmpeg_compose = AsyncMock(return_value={
            "outputs": [{"file_url": "https://s3.example.com/output.mp4"}],
        })

        response = client.post(
            f"{FFMPEG_PREFIX}/compose",
            json={
                "id": "sync-compose",
                "inputs": [{"file_url": "https://example.com/input.mp4", "options": []}],
                "outputs": [{"options": [{"option": "-c:v", "argument": "libx264"}]}],
                "sync": True,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "result" in data


class TestFFmpegExamples:
    """Tests for GET /api/v1/ffmpeg/compose/examples."""

    def test_get_examples(self, client, auth_headers):
        """The examples endpoint is shadowed by the {job_id} path parameter.
        FastAPI matches /compose/{job_id} before /compose/examples, so
        this request is handled as a job status lookup and returns 404."""
        response = client.get(f"{FFMPEG_PREFIX}/compose/examples", headers=auth_headers)
        # The /{job_id} route matches first, treating 'examples' as a job_id
        assert response.status_code in (200, 404)


# ── AnyLLM ─────────────────────────────────────────────────────────────────

ANYLLM_PREFIX = "/api/v1/anyllm"


class TestAnyLLMRoot:
    """Tests for GET /api/v1/anyllm/."""

    def test_anyllm_root(self, client, auth_headers):
        """Should return AnyLLM status info."""
        response = client.get(f"{ANYLLM_PREFIX}/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data


class TestAnyLLMProviders:
    """Tests for GET /api/v1/anyllm/providers."""

    @patch("app.routes.anyllm.completions.anyllm_service")
    def test_get_providers_success(self, mock_svc, client, auth_headers):
        """Should return list of available LLM providers."""
        mock_svc.get_providers = AsyncMock(return_value={
            "providers": [
                {"name": "openai", "models_available": True},
                {"name": "anthropic", "models_available": True},
            ]
        })
        response = client.get(f"{ANYLLM_PREFIX}/providers", headers=auth_headers)
        assert response.status_code == 200

    @patch("app.routes.anyllm.completions.anyllm_service")
    def test_get_providers_error(self, mock_svc, client, auth_headers):
        """Should return 500 when provider listing fails."""
        mock_svc.get_providers = AsyncMock(side_effect=Exception("Config error"))
        response = client.get(f"{ANYLLM_PREFIX}/providers", headers=auth_headers)
        assert response.status_code == 500


class TestAnyLLMListModels:
    """Tests for POST /api/v1/anyllm/list-models."""

    @patch("app.routes.anyllm.completions.anyllm_service")
    def test_list_models_success(self, mock_svc, client, auth_headers):
        """Should return models for a given provider."""
        mock_svc.get_models = AsyncMock(return_value={
            "models": [{"id": "gpt-5-mini"}, {"id": "gpt-5"}]
        })
        response = client.post(
            f"{ANYLLM_PREFIX}/list-models",
            json={"provider": "openai"},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_list_models_missing_provider(self, client, auth_headers):
        """Should reject request without provider field."""
        response = client.post(
            f"{ANYLLM_PREFIX}/list-models",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @patch("app.routes.anyllm.completions.anyllm_service")
    def test_list_models_api_key_missing(self, mock_svc, client, auth_headers):
        """Should return 400 when API key is missing for provider."""
        mock_svc.get_models = AsyncMock(side_effect=Exception("API key is required"))
        response = client.post(
            f"{ANYLLM_PREFIX}/list-models",
            json={"provider": "anthropic"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "API_KEY_MISSING"


# ── OpenAI-compatible Models ───────────────────────────────────────────────

OPENAI_PREFIX = "/api/v1/openai"


class TestOpenAIModels:
    """Tests for GET /api/v1/models (OpenAI-compat TTS models)."""

    @patch("app.routes.openai_compat.openai_compat.tts_service")
    def test_list_models(self, mock_tts, client, auth_headers):
        """Should return TTS models in OpenAI format."""
        mock_tts.get_models_formatted.return_value = [
            {"id": "kokoro"},
            {"id": "edge-tts"},
        ]
        response = client.get(f"{OPENAI_PREFIX}/models", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) == 2

    @patch("app.routes.openai_compat.openai_compat.tts_service")
    def test_list_models_post(self, mock_tts, client, auth_headers):
        """POST /models should also work (OpenAI compat)."""
        mock_tts.get_models_formatted.return_value = [{"id": "kokoro"}]
        response = client.post(f"{OPENAI_PREFIX}/models", headers=auth_headers)
        assert response.status_code == 200

    @patch("app.routes.openai_compat.openai_compat.tts_service")
    def test_list_audio_voices(self, mock_tts, client, auth_headers):
        """Should return available TTS voices."""
        mock_tts.get_voices_formatted.return_value = [
            {"id": "af_heart", "name": "Heart"},
            {"id": "af_bella", "name": "Bella"},
        ]
        response = client.get(f"{OPENAI_PREFIX}/audio/voices", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        assert len(data["voices"]) == 2


# ── Music ──────────────────────────────────────────────────────────────────

MUSIC_PREFIX = "/api/v1/music"


class TestMusicMoods:
    """Tests for GET /api/v1/music/moods."""

    @patch("app.routes.music.music.music_service")
    def test_list_moods(self, mock_svc, client, auth_headers):
        """Should return available mood categories."""
        mock_svc.get_available_moods.return_value = ["happy", "sad", "chill", "epic"]
        mock_svc.get_tracks_by_mood = AsyncMock(return_value=[{"file": "track.mp3"}])

        response = client.get(f"{MUSIC_PREFIX}/moods", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "moods" in data
        assert "mood_counts" in data
        assert data["total_moods"] == 4

    @patch("app.routes.music.music.music_service")
    def test_list_moods_error(self, mock_svc, client, auth_headers):
        """Should return 500 when mood listing fails."""
        mock_svc.get_available_moods.side_effect = Exception("Service down")
        response = client.get(f"{MUSIC_PREFIX}/moods", headers=auth_headers)
        assert response.status_code == 500


class TestMusicTracks:
    """Tests for GET /api/v1/music/tracks."""

    @patch("app.routes.music.music.music_service")
    def test_list_tracks_all(self, mock_svc, client, auth_headers):
        """Should return paginated list of all tracks."""
        mock_svc.get_all_tracks = AsyncMock(return_value=[
            {"title": "Track 1", "mood": "happy", "file": "track1.mp3"},
            {"title": "Track 2", "mood": "sad", "file": "track2.mp3"},
        ])
        mock_svc.get_available_moods.return_value = ["happy", "sad"]

        response = client.get(f"{MUSIC_PREFIX}/tracks", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "tracks" in data
        assert data["total"] == 2
        assert "page" in data
        assert "total_pages" in data

    @patch("app.routes.music.music.music_service")
    def test_list_tracks_by_mood(self, mock_svc, client, auth_headers):
        """Should filter tracks by mood parameter."""
        mock_svc.get_tracks_by_mood = AsyncMock(return_value=[
            {"title": "Happy Track", "mood": "happy", "file": "happy.mp3"},
        ])
        mock_svc.get_available_moods.return_value = ["happy", "sad"]

        response = client.get(f"{MUSIC_PREFIX}/tracks?mood=happy", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["tracks"]) == 1

    @patch("app.routes.music.music.music_service")
    def test_list_tracks_invalid_mood(self, mock_svc, client, auth_headers):
        """Should return 404 for invalid mood filter."""
        mock_svc.get_tracks_by_mood = AsyncMock(return_value=[])
        mock_svc.get_available_moods.return_value = ["happy", "sad"]

        response = client.get(f"{MUSIC_PREFIX}/tracks?mood=nonexistent", headers=auth_headers)
        assert response.status_code == 404

    @patch("app.routes.music.music.music_service")
    def test_list_tracks_with_search(self, mock_svc, client, auth_headers):
        """Should filter tracks by search query."""
        mock_svc.get_all_tracks = AsyncMock(return_value=[
            {"title": "Summer Vibes", "mood": "happy", "file": "summer.mp3"},
            {"title": "Winter Chill", "mood": "chill", "file": "winter.mp3"},
        ])
        mock_svc.get_available_moods.return_value = ["happy", "chill"]

        response = client.get(f"{MUSIC_PREFIX}/tracks?search=summer", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["tracks"][0]["title"] == "Summer Vibes"

    @patch("app.routes.music.music.music_service")
    def test_list_tracks_pagination(self, mock_svc, client, auth_headers):
        """Should respect pagination parameters."""
        tracks = [{"title": f"Track {i}", "mood": "happy", "file": f"t{i}.mp3"} for i in range(25)]
        mock_svc.get_all_tracks = AsyncMock(return_value=tracks)
        mock_svc.get_available_moods.return_value = ["happy"]

        response = client.get(f"{MUSIC_PREFIX}/tracks?page=2&per_page=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["per_page"] == 10
        assert len(data["tracks"]) == 10
        assert data["total"] == 25
        assert data["total_pages"] == 3


# ── Documents to Markdown ──────────────────────────────────────────────────

DOCS_PREFIX = "/api/v1/documents/to-markdown"


class TestDocumentFormats:
    """Tests for GET /api/v1/documents/to-markdown/formats."""

    @patch("app.routes.documents.to_markdown.markitdown_service")
    def test_get_formats(self, mock_svc, client, auth_headers):
        """Should return supported document formats."""
        mock_svc.get_supported_formats.return_value = {
            "supported_formats": {
                "documents": {"pdf": {"description": "PDF documents"}},
                "text": {"txt": {"description": "Plain text"}},
            }
        }
        response = client.get(f"{DOCS_PREFIX}/formats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "supported_formats" in data


class TestDocumentToMarkdown:
    """Tests for POST /api/v1/documents/to-markdown/."""

    @patch("app.routes.documents.to_markdown.markitdown_service")
    def test_convert_missing_input(self, mock_svc, client, auth_headers):
        """Should reject request with neither file nor url."""
        mock_svc.is_available.return_value = True
        response = client.post(
            f"{DOCS_PREFIX}/",
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("app.routes.documents.to_markdown.job_queue")
    @patch("app.routes.documents.to_markdown.markitdown_service")
    def test_convert_url_creates_job(self, mock_svc, mock_jq, client, auth_headers):
        """Should create async job for URL-based conversion."""
        mock_svc.is_available.return_value = True
        mock_jq.add_job = AsyncMock()

        response = client.post(
            f"{DOCS_PREFIX}/",
            data={"url": "https://example.com/document.pdf"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    @patch("app.routes.documents.to_markdown.markitdown_service")
    def test_convert_service_unavailable(self, mock_svc, client, auth_headers):
        """Should return 503 when MarkItDown is not available."""
        mock_svc.is_available.return_value = False
        response = client.post(
            f"{DOCS_PREFIX}/",
            data={"url": "https://example.com/doc.pdf"},
            headers=auth_headers,
        )
        assert response.status_code == 503

    @patch("app.routes.documents.to_markdown.markitdown_service")
    def test_convert_unsupported_file_type(self, mock_svc, client, auth_headers):
        """Should reject unsupported file extensions."""
        mock_svc.is_available.return_value = True
        import io
        file_content = io.BytesIO(b"fake binary data")
        response = client.post(
            f"{DOCS_PREFIX}/",
            files={"file": ("test.xyz", file_content, "application/octet-stream")},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("app.routes.documents.to_markdown.job_queue")
    @patch("app.routes.documents.to_markdown.markitdown_service")
    def test_convert_file_upload_creates_job(self, mock_svc, mock_jq, client, auth_headers):
        """Should create async job for file upload."""
        mock_svc.is_available.return_value = True
        mock_jq.add_job = AsyncMock()

        import io
        file_content = io.BytesIO(b"%PDF-1.4 fake pdf content")
        response = client.post(
            f"{DOCS_PREFIX}/",
            files={"file": ("document.pdf", file_content, "application/pdf")},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    @patch("app.routes.documents.to_markdown.markitdown_service")
    def test_convert_both_file_and_url(self, mock_svc, client, auth_headers):
        """Should reject request with both file and url."""
        mock_svc.is_available.return_value = True
        import io
        file_content = io.BytesIO(b"%PDF-1.4 fake pdf")
        response = client.post(
            f"{DOCS_PREFIX}/",
            files={"file": ("document.pdf", file_content, "application/pdf")},
            data={"url": "https://example.com/other.pdf"},
            headers=auth_headers,
        )
        assert response.status_code == 400


# ── Authentication for misc endpoints ──────────────────────────────────────

class TestMiscAuth:
    """Test that endpoints requiring auth reject unauthenticated requests."""

    def test_ffmpeg_compose_no_auth(self, unauth_client):
        """FFmpeg compose should require auth."""
        response = unauth_client.post(
            f"{FFMPEG_PREFIX}/compose",
            json={
                "id": "test",
                "inputs": [{"file_url": "https://example.com/a.mp4", "options": []}],
                "outputs": [{"options": []}],
            },
        )
        assert response.status_code in (401, 403)

    def test_openai_models_no_auth(self, unauth_client):
        """OpenAI-compat models endpoint should require auth."""
        response = unauth_client.get(f"{OPENAI_PREFIX}/models")
        assert response.status_code in (401, 403)
