"""
Tests for media-related API endpoints:
- Media download (POST /api/v1/media/download)
- Download extractors (GET /api/v1/media/extractors)
- Download info (GET /api/v1/media/info)
- Metadata (POST /api/v1/media/metadata)
- YouTube transcripts (POST /api/v1/media/youtube-transcripts)
- Silence detection (POST /api/v1/media/silence/)
- Silence analysis (POST /api/v1/media/silence/analyze)
- Conversion formats (GET /api/v1/media/conversions/formats)
- Media conversion (POST /api/v1/media/conversions/)
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

BASE = "/api/v1/media"


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Reset the SecurityMiddleware rate-limit state before each test
    so that rapid test execution doesn't trigger 429 responses."""
    from app.middleware.security import SecurityMiddleware
    instance = SecurityMiddleware.get_instance()
    if instance is not None:
        instance.request_count.clear()
        instance.suspicious_count.clear()
        instance.temp_blocked_ips.clear()
    yield


@pytest.fixture
def media_client(client):
    """Client with get_current_user also overridden for media routes."""
    from app.main import app
    from app.utils.auth import get_current_user

    async def override_get_current_user(request=None):
        return {"user_id": "1", "user_role": "admin", "user_email": "test@test.com"}

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


# ── Download endpoints ────────────────────────────────────────────────────────

class TestMediaDownload:
    """Tests for POST /api/v1/media/download."""

    def test_download_creates_job(self, media_client):
        """POST /download with valid URL should return 202 with job_id."""
        with patch("app.routes.media.download.job_queue") as mock_jq:
            mock_jq.add_job = AsyncMock()
            response = media_client.post(
                f"{BASE}/download",
                json={"url": "https://www.youtube.com/watch?v=test123"},
            )
            assert response.status_code == 202
            data = response.json()
            assert "job_id" in data

    def test_download_missing_url(self, media_client):
        """POST /download without url field should return 422."""
        response = media_client.post(f"{BASE}/download", json={})
        assert response.status_code == 422

    def test_download_invalid_url(self, media_client):
        """POST /download with invalid URL should return 422."""
        response = media_client.post(f"{BASE}/download", json={"url": "not-a-url"})
        assert response.status_code == 422

    def test_download_sync_success(self, media_client):
        """POST /download with sync=true processes immediately."""
        with patch("app.routes.media.download.download_service") as mock_svc:
            mock_svc.process_enhanced_media_download = AsyncMock(
                return_value={"url": "https://s3/file.mp4"}
            )
            response = media_client.post(
                f"{BASE}/download",
                json={"url": "https://www.youtube.com/watch?v=test123", "sync": True},
            )
            # Sync mode still returns 202 per the route's response_model
            assert response.status_code == 202
            data = response.json()
            assert "job_id" in data

    def test_download_with_optional_params(self, media_client):
        """POST /download with optional parameters should accept them."""
        with patch("app.routes.media.download.job_queue") as mock_jq:
            mock_jq.add_job = AsyncMock()
            response = media_client.post(
                f"{BASE}/download",
                json={
                    "url": "https://www.youtube.com/watch?v=test123",
                    "format": "mp4",
                    "file_name": "my_video",
                    "extract_subtitles": True,
                    "subtitle_languages": ["en", "fr"],
                    "embed_metadata": True,
                },
            )
            assert response.status_code == 202


class TestMediaExtractors:
    """Tests for GET /api/v1/media/extractors."""

    def test_extractors_returns_categories(self, media_client):
        """GET /extractors should return grouped extractor list."""
        with patch("app.routes.media.download.yt_dlp") as mock_ytdlp:
            mock_extractor = MagicMock()
            mock_extractor.IE_NAME = "YouTube"
            mock_extractor.IE_DESC = "YouTube videos"

            mock_ydl_instance = MagicMock()
            mock_ydl_instance._ies = [mock_extractor]
            mock_ydl_instance.__enter__ = MagicMock(return_value=mock_ydl_instance)
            mock_ydl_instance.__exit__ = MagicMock(return_value=False)
            mock_ytdlp.YoutubeDL.return_value = mock_ydl_instance

            response = media_client.get(f"{BASE}/extractors")
            assert response.status_code == 200
            data = response.json()
            assert "total_extractors" in data
            assert "categories" in data
            for key in ("video", "music", "social", "general"):
                assert key in data["categories"]


class TestMediaInfo:
    """Tests for GET /api/v1/media/info."""

    def test_info_missing_url(self, media_client):
        """GET /info without url query param should return 422."""
        response = media_client.get(f"{BASE}/info")
        assert response.status_code == 422

    def test_info_returns_metadata(self, media_client):
        """GET /info?url=... should return media metadata."""
        with patch("app.routes.media.download.yt_dlp") as mock_ytdlp:
            mock_info = {
                "id": "test123",
                "title": "Test Video",
                "description": "A test video",
                "uploader": "TestUser",
                "duration": 120,
                "upload_date": "20240101",
                "view_count": 1000,
                "like_count": 50,
                "thumbnail": "https://example.com/thumb.jpg",
                "formats": [
                    {
                        "format_id": "22",
                        "ext": "mp4",
                        "resolution": "1280x720",
                        "fps": 30,
                        "filesize": 10000000,
                        "format_note": "720p",
                        "vcodec": "h264",
                    }
                ],
                "subtitles": {"en": [{"ext": "vtt"}]},
                "chapters": None,
                "webpage_url": "https://www.youtube.com/watch?v=test123",
            }
            mock_ydl_instance = MagicMock()
            mock_ydl_instance.extract_info = MagicMock(return_value=mock_info)
            mock_ydl_instance.__enter__ = MagicMock(return_value=mock_ydl_instance)
            mock_ydl_instance.__exit__ = MagicMock(return_value=False)
            mock_ytdlp.YoutubeDL.return_value = mock_ydl_instance

            response = media_client.get(
                f"{BASE}/info", params={"url": "https://www.youtube.com/watch?v=test123"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "test123"
            assert data["title"] == "Test Video"
            assert data["duration"] == 120
            assert len(data["formats"]) == 1
            assert "en" in data["subtitles"]


# ── Metadata endpoint ─────────────────────────────────────────────────────────

class TestMetadata:
    """Tests for POST /api/v1/media/metadata."""

    def test_metadata_missing_url(self, media_client):
        """POST /metadata without media_url should return 422."""
        response = media_client.post(f"{BASE}/metadata", json={})
        assert response.status_code == 422

    def test_metadata_invalid_url(self, media_client):
        """POST /metadata with invalid URL should return 422."""
        response = media_client.post(f"{BASE}/metadata", json={"media_url": "not-a-url"})
        assert response.status_code == 422

    def test_metadata_creates_async_job(self, media_client):
        """POST /metadata with valid URL and sync=false should return 202 with job_id."""
        with patch("app.routes.media.metadata.job_queue") as mock_jq:
            mock_jq.add_job = AsyncMock()
            response = media_client.post(
                f"{BASE}/metadata",
                json={"media_url": "https://example.com/video.mp4", "sync": False},
            )
            assert response.status_code == 202
            data = response.json()
            assert "job_id" in data

    def test_metadata_sync_returns_result(self, media_client):
        """POST /metadata with sync=true should return 200 with metadata."""
        mock_metadata = {
            "filesize": 1000000,
            "filesize_mb": 1.0,
            "duration": 120.5,
            "has_video": True,
            "has_audio": True,
        }
        with patch("app.routes.media.metadata.metadata_service") as mock_svc:
            mock_svc.get_metadata = AsyncMock(return_value=mock_metadata)
            response = media_client.post(
                f"{BASE}/metadata",
                json={"media_url": "https://example.com/video.mp4", "sync": True},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["filesize"] == 1000000
            assert data["has_video"] is True


# ── YouTube Transcripts ───────────────────────────────────────────────────────

class TestYouTubeTranscripts:
    """Tests for POST /api/v1/media/youtube-transcripts."""

    def test_transcripts_missing_url(self, media_client):
        """POST /youtube-transcripts without video_url should return 422."""
        response = media_client.post(f"{BASE}/youtube-transcripts", json={})
        assert response.status_code == 422

    def test_transcripts_invalid_url(self, media_client):
        """POST /youtube-transcripts with invalid URL should return 422."""
        response = media_client.post(
            f"{BASE}/youtube-transcripts", json={"video_url": "not-a-url"}
        )
        assert response.status_code == 422

    def test_transcripts_non_youtube_url(self, media_client):
        """POST /youtube-transcripts with non-YouTube URL should return 400."""
        response = media_client.post(
            f"{BASE}/youtube-transcripts",
            json={"video_url": "https://example.com/not-youtube"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "Invalid YouTube URL" in data["detail"]

    def test_transcripts_invalid_format(self, media_client):
        """POST /youtube-transcripts with invalid format should return 400."""
        response = media_client.post(
            f"{BASE}/youtube-transcripts",
            json={
                "video_url": "https://www.youtube.com/watch?v=test",
                "format": "invalid_format",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "Invalid format" in data["detail"]

    def test_transcripts_creates_async_job(self, media_client):
        """POST /youtube-transcripts with valid data creates async job."""
        with patch("app.routes.media.youtube_transcripts.job_queue") as mock_jq:
            mock_jq.add_job = AsyncMock()
            response = media_client.post(
                f"{BASE}/youtube-transcripts",
                json={
                    "video_url": "https://www.youtube.com/watch?v=test123",
                    "format": "text",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data

    def test_transcripts_sync_returns_result(self, media_client):
        """POST /youtube-transcripts with sync=true returns result immediately."""
        mock_result = {
            "transcript": "Hello world",
            "language": "en",
            "video_id": "test123",
        }
        with patch("app.routes.media.youtube_transcripts.youtube_transcript_service") as mock_svc:
            mock_svc.process_transcript_generation = AsyncMock(return_value=mock_result)
            response = media_client.post(
                f"{BASE}/youtube-transcripts",
                json={
                    "video_url": "https://www.youtube.com/watch?v=test123",
                    "format": "text",
                    "sync": True,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["result"]["transcript"] == "Hello world"

    def test_transcripts_valid_formats_accepted(self, media_client):
        """POST /youtube-transcripts with valid format values should not return 400."""
        with patch("app.routes.media.youtube_transcripts.job_queue") as mock_jq:
            mock_jq.add_job = AsyncMock()
            for fmt in ("text", "srt", "vtt", "json"):
                response = media_client.post(
                    f"{BASE}/youtube-transcripts",
                    json={
                        "video_url": "https://www.youtube.com/watch?v=test123",
                        "format": fmt,
                    },
                )
                assert response.status_code == 200, f"Format '{fmt}' should be accepted"


# ── Silence detection ─────────────────────────────────────────────────────────

class TestSilenceDetection:
    """Tests for POST /api/v1/media/silence/ and /silence/analyze."""

    def test_silence_missing_url(self, media_client):
        """POST /silence/ without media_url should return 422."""
        response = media_client.post(f"{BASE}/silence/", json={})
        assert response.status_code == 422

    def test_silence_invalid_url(self, media_client):
        """POST /silence/ with invalid URL should return 422."""
        response = media_client.post(f"{BASE}/silence/", json={"media_url": "not-a-url"})
        assert response.status_code == 422

    def test_silence_creates_job(self, media_client):
        """POST /silence/ with valid URL should return 202 with job_id."""
        with patch("app.routes.media.silence.job_queue") as mock_jq:
            mock_jq.add_job = AsyncMock()
            response = media_client.post(
                f"{BASE}/silence/",
                json={"media_url": "https://example.com/audio.mp3"},
            )
            assert response.status_code == 202
            data = response.json()
            assert "job_id" in data

    def test_silence_with_optional_params(self, media_client):
        """POST /silence/ with optional parameters should accept them."""
        with patch("app.routes.media.silence.job_queue") as mock_jq:
            mock_jq.add_job = AsyncMock()
            response = media_client.post(
                f"{BASE}/silence/",
                json={
                    "media_url": "https://example.com/audio.mp3",
                    "noise": "-30dB",
                    "duration": 0.5,
                    "mono": True,
                    "use_advanced_vad": True,
                    "min_speech_duration": 0.25,
                },
            )
            assert response.status_code == 202

    def test_analyze_missing_url(self, media_client):
        """POST /silence/analyze without media_url should return 422."""
        response = media_client.post(f"{BASE}/silence/analyze", json={})
        assert response.status_code == 422

    def test_analyze_invalid_url(self, media_client):
        """POST /silence/analyze with invalid media_url should return 422."""
        response = media_client.post(f"{BASE}/silence/analyze", json={"media_url": "bad"})
        assert response.status_code == 422

    def test_analyze_creates_job(self, media_client):
        """POST /silence/analyze with valid URL should return 202 with job_id."""
        with patch("app.routes.media.silence.job_queue") as mock_jq:
            mock_jq.add_job = AsyncMock()
            response = media_client.post(
                f"{BASE}/silence/analyze",
                json={"media_url": "https://example.com/audio.mp3"},
            )
            assert response.status_code == 202
            data = response.json()
            assert "job_id" in data


# ── Conversion endpoints ─────────────────────────────────────────────────────

class TestConversionFormats:
    """Tests for GET /api/v1/media/conversions/formats."""

    def test_formats_returns_list(self, client):
        """GET /conversions/formats should return supported formats."""
        response = client.get(f"{BASE}/conversions/formats")
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "formats"
        assert "supported_formats" in data
        assert "quality_presets" in data
        assert "total_formats" in data
        assert isinstance(data["total_formats"], int)
        assert data["total_formats"] > 0
        assert "format_list" in data
        assert "media_types" in data

    def test_formats_has_expected_media_types(self, client):
        """GET /conversions/formats should include standard media types."""
        response = client.get(f"{BASE}/conversions/formats")
        assert response.status_code == 200
        data = response.json()
        media_types = data["media_types"]
        assert isinstance(media_types, list)
        assert len(media_types) > 0


class TestMediaConversion:
    """Tests for POST /api/v1/media/conversions/."""

    def test_conversion_json_missing_both(self, media_client):
        """POST /conversions/ JSON without input_url or file_data should return 400."""
        response = media_client.post(
            f"{BASE}/conversions/",
            json={"output_format": "mp3"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "required" in data["detail"].lower() or "input_url" in data["detail"]

    def test_conversion_json_both_url_and_file(self, media_client):
        """POST /conversions/ JSON with both input_url and file_data should return 400."""
        import base64
        dummy_data = base64.b64encode(b"test data").decode()
        response = media_client.post(
            f"{BASE}/conversions/",
            json={
                "input_url": "https://example.com/video.mp4",
                "file_data": dummy_data,
                "output_format": "mp3",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "not both" in data["detail"].lower() or "either" in data["detail"].lower()

    def test_conversion_json_unsupported_format(self, media_client):
        """POST /conversions/ JSON with unsupported output format should return 400."""
        response = media_client.post(
            f"{BASE}/conversions/",
            json={
                "input_url": "https://example.com/video.mp4",
                "output_format": "xyz_unsupported",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "unsupported" in data["detail"].lower() or "format" in data["detail"].lower()

    def test_conversion_json_invalid_quality(self, media_client):
        """POST /conversions/ JSON with invalid quality preset should return 400."""
        response = media_client.post(
            f"{BASE}/conversions/",
            json={
                "input_url": "https://example.com/video.mp4",
                "output_format": "mp3",
                "quality": "super_ultra_hd",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "quality" in data["detail"].lower() or "preset" in data["detail"].lower()

    def test_conversion_json_creates_async_job(self, media_client):
        """POST /conversions/ JSON with valid data creates async job and returns job_id."""
        with patch("app.routes.media.media_conversions.job_queue") as mock_jq:
            mock_jq.add_job = AsyncMock()
            response = media_client.post(
                f"{BASE}/conversions/",
                json={
                    "input_url": "https://example.com/video.mp4",
                    "output_format": "mp3",
                },
            )
            # Route returns 200 (no explicit status_code on decorator for async path)
            assert response.status_code in (200, 202)
            data = response.json()
            assert "job_id" in data

    def test_conversion_form_missing_both(self, media_client):
        """POST /conversions/ form without file or url should return 400."""
        response = media_client.post(
            f"{BASE}/conversions/",
            data={"output_format": "mp3"},
        )
        assert response.status_code == 400

    def test_conversion_form_missing_output_format(self, media_client):
        """POST /conversions/ form with url but no output_format should return 400."""
        response = media_client.post(
            f"{BASE}/conversions/",
            data={"url": "https://example.com/video.mp4"},
        )
        assert response.status_code == 400


# ── Unauthenticated access ───────────────────────────────────────────────────

class TestMediaAuth:
    """Test that media endpoints require authentication."""

    def test_download_requires_auth(self, unauth_client):
        """POST /download without auth should return 401 or 403."""
        response = unauth_client.post(
            f"{BASE}/download",
            json={"url": "https://www.youtube.com/watch?v=test123"},
        )
        assert response.status_code in (401, 403)

    def test_metadata_requires_auth(self, unauth_client):
        """POST /metadata without auth should return 401 or 403."""
        response = unauth_client.post(
            f"{BASE}/metadata",
            json={"media_url": "https://example.com/video.mp4"},
        )
        assert response.status_code in (401, 403)

    def test_transcripts_requires_auth(self, unauth_client):
        """POST /youtube-transcripts without auth should return 401 or 403."""
        response = unauth_client.post(
            f"{BASE}/youtube-transcripts",
            json={"video_url": "https://www.youtube.com/watch?v=test"},
        )
        assert response.status_code in (401, 403)

    def test_silence_requires_auth(self, unauth_client):
        """POST /silence/ without auth should return 401 or 403."""
        response = unauth_client.post(
            f"{BASE}/silence/",
            json={"media_url": "https://example.com/audio.mp3"},
        )
        assert response.status_code in (401, 403)

    def test_conversions_requires_auth(self, unauth_client):
        """POST /conversions/ without auth should return 401 or 403."""
        response = unauth_client.post(
            f"{BASE}/conversions/",
            json={
                "input_url": "https://example.com/video.mp4",
                "output_format": "mp3",
            },
        )
        assert response.status_code in (401, 403)
