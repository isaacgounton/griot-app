"""
Tests for video API endpoints.

Covers:
- Video listing and management (GET /api/v1/videos/)
- Caption operations (POST /api/v1/videos/add-captions)
- Caption styles listing (GET /api/v1/videos/add-captions/styles/list)
- Text overlay presets (GET /api/v1/videos/text-overlay/all-presets)
- Video generation (POST /api/v1/videos/generate)
- Caption style presets & best practices
- Video stats overview
- Input validation (422 on missing fields)
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


# ── Helpers ──────────────────────────────────────────────────────────────────

def _override_auth(app):
    """Override auth dependencies so video routes don't need real JWT/API keys."""
    from app.utils.auth import get_current_user, get_api_key
    from app.utils.subscription import require_active_subscription

    async def fake_current_user(request=None):
        return {"user_id": "1", "user_role": "admin", "user_email": "test@example.com"}

    async def fake_api_key(request=None, api_key_header=None):
        return "test-api-key"

    async def fake_subscription(request=None, api_key=None):
        return True

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_api_key] = fake_api_key
    app.dependency_overrides[require_active_subscription] = fake_subscription


def _disable_rate_limiting():
    """Disable the security middleware rate limiter for tests."""
    from app.middleware.security import SecurityMiddleware
    instance = SecurityMiddleware.get_instance()
    if instance:
        instance._check_rate_limits = lambda *args, **kwargs: None


@pytest.fixture
def vclient(mock_database_service):
    """TestClient with all auth overrides needed for video routes."""
    from unittest.mock import patch, AsyncMock
    with patch("app.database.DatabaseService.initialize", new_callable=AsyncMock), \
         patch("app.database.DatabaseService.create_tables", new_callable=AsyncMock), \
         patch("app.database.DatabaseService.update_enums", new_callable=AsyncMock), \
         patch("app.database.DatabaseService.migrate_schema", new_callable=AsyncMock):

        from fastapi.testclient import TestClient
        from app.main import app

        _override_auth(app)

        with TestClient(
            app,
            raise_server_exceptions=False,
            base_url="http://localhost",
            headers={"Host": "localhost"},
        ) as tc:
            _disable_rate_limiting()
            yield tc

        app.dependency_overrides.clear()


# ── Caption styles list ──────────────────────────────────────────────────────

class TestCaptionStylesList:
    """GET /api/v1/videos/add-captions/styles/list"""

    def test_list_caption_styles(self, vclient):
        response = vclient.get("/api/v1/videos/add-captions/styles/list")
        assert response.status_code == 200
        data = response.json()
        assert "styles" in data
        assert isinstance(data["styles"], list)
        assert len(data["styles"]) > 0
        # Verify expected style names
        style_names = [s["name"] for s in data["styles"]]
        assert "classic" in style_names
        assert "karaoke" in style_names
        assert data["default"] == "classic"

    def test_caption_styles_have_descriptions(self, vclient):
        response = vclient.get("/api/v1/videos/add-captions/styles/list")
        data = response.json()
        for style in data["styles"]:
            assert "name" in style
            assert "description" in style
            assert "use_case" in style


# ── Text overlay presets ─────────────────────────────────────────────────────

class TestTextOverlayPresets:
    """GET /api/v1/videos/text-overlay/all-presets"""

    def test_get_all_presets(self, vclient):
        response = vclient.get("/api/v1/videos/text-overlay/all-presets")
        assert response.status_code == 200
        data = response.json()
        assert "presets" in data
        assert "categories" in data
        assert "total_count" in data
        assert isinstance(data["presets"], dict)
        assert data["total_count"] == len(data["presets"])

    def test_presets_have_expected_categories(self, vclient):
        response = vclient.get("/api/v1/videos/text-overlay/all-presets")
        data = response.json()
        # The service returns title, subtitle, watermark, alert, caption
        assert "title" in data["presets"]
        assert "subtitle" in data["presets"]


# ── Caption create (POST add-captions) ───────────────────────────────────────

class TestCaptionCreate:
    """POST /api/v1/videos/add-captions"""

    def test_create_caption_job_returns_job_id(self, vclient):
        with patch("app.routes.video.caption.job_queue") as mock_jq:
            mock_jq.add_job = AsyncMock()
            response = vclient.post(
                "/api/v1/videos/add-captions",
                json={"video_url": "https://example.com/video.mp4"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data

    def test_create_caption_missing_video_url(self, vclient):
        """Missing required field video_url should return 422."""
        response = vclient.post("/api/v1/videos/add-captions", json={})
        assert response.status_code == 422

    def test_create_caption_with_settings(self, vclient):
        with patch("app.routes.video.caption.job_queue") as mock_jq:
            mock_jq.add_job = AsyncMock()
            response = vclient.post(
                "/api/v1/videos/add-captions",
                json={
                    "video_url": "https://example.com/video.mp4",
                    "settings": {
                        "style": "karaoke",
                        "font_size": 32,
                        "all_caps": True,
                    },
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data

    def test_create_caption_with_replacements(self, vclient):
        with patch("app.routes.video.caption.job_queue") as mock_jq:
            mock_jq.add_job = AsyncMock()
            response = vclient.post(
                "/api/v1/videos/add-captions",
                json={
                    "video_url": "https://example.com/video.mp4",
                    "replace": [{"find": "foo", "replace": "bar"}],
                },
            )
            assert response.status_code == 200


# ── Caption job status ───────────────────────────────────────────────────────

class TestCaptionJobStatus:
    """GET /api/v1/videos/add-captions/{job_id}"""

    def test_get_caption_job_not_found(self, vclient):
        with patch("app.routes.video.caption.job_queue") as mock_jq:
            mock_jq.get_job = AsyncMock(return_value=None)
            response = vclient.get("/api/v1/videos/add-captions/nonexistent-id")
            assert response.status_code == 404

    def test_get_caption_job_found(self, vclient):
        mock_job = MagicMock()
        mock_job.status = "completed"
        mock_job.result = {"url": "https://s3.example.com/result.mp4"}
        mock_job.error = None
        with patch("app.routes.video.caption.job_queue") as mock_jq:
            mock_jq.get_job = AsyncMock(return_value=mock_job)
            response = vclient.get("/api/v1/videos/add-captions/test-job-id")
            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "test-job-id"
            assert data["status"] == "completed"


# ── Video generation ─────────────────────────────────────────────────────────

class TestVideoGeneration:
    """POST /api/v1/videos/generate"""

    def test_generate_video_missing_prompt(self, vclient):
        """Missing required field prompt should return 422."""
        response = vclient.post("/api/v1/videos/generate", json={})
        assert response.status_code == 422

    def test_generate_video_invalid_provider(self, vclient):
        response = vclient.post(
            "/api/v1/videos/generate",
            json={"prompt": "A cat playing piano", "provider": "nonexistent"},
        )
        assert response.status_code == 400
        assert "Unsupported provider" in response.json()["detail"]

    def test_generate_video_creates_job(self, vclient):
        with patch("app.routes.video.generate.ltx_video_service") as mock_ltx, \
             patch("app.routes.video.generate.job_queue") as mock_jq:
            mock_ltx.is_available.return_value = True
            mock_jq.add_job = AsyncMock()
            response = vclient.post(
                "/api/v1/videos/generate",
                json={"prompt": "A beautiful sunset over the ocean"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data

    def test_generate_video_width_out_of_range(self, vclient):
        """Width below minimum should return 422."""
        response = vclient.post(
            "/api/v1/videos/generate",
            json={"prompt": "test", "width": 100},
        )
        assert response.status_code == 422

    def test_generate_video_height_out_of_range(self, vclient):
        """Height above maximum should return 422."""
        response = vclient.post(
            "/api/v1/videos/generate",
            json={"prompt": "test", "height": 2000},
        )
        assert response.status_code == 422

    def test_generate_video_num_frames_out_of_range(self, vclient):
        """num_frames above 257 should return 422."""
        response = vclient.post(
            "/api/v1/videos/generate",
            json={"prompt": "test", "num_frames": 500},
        )
        assert response.status_code == 422

    def test_generate_video_service_unavailable(self, vclient):
        """When the provider service is unavailable, return 503."""
        with patch("app.routes.video.generate.ltx_video_service") as mock_ltx:
            mock_ltx.is_available.return_value = False
            response = vclient.post(
                "/api/v1/videos/generate",
                json={"prompt": "A cat playing piano", "provider": "ltx_video"},
            )
            assert response.status_code == 503

    def test_generate_video_pollinations_provider(self, vclient):
        """Pollinations provider should create a job (no availability check for it)."""
        with patch("app.routes.video.generate.job_queue") as mock_jq:
            mock_jq.add_job = AsyncMock()
            response = vclient.post(
                "/api/v1/videos/generate",
                json={"prompt": "A sunset", "provider": "pollinations"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data


# ── Text overlay create ──────────────────────────────────────────────────────

class TestTextOverlayCreate:
    """POST /api/v1/videos/text-overlay"""

    def test_create_text_overlay_job(self, vclient):
        with patch("app.routes.video.text_overlay.job_queue") as mock_jq:
            mock_jq.add_job = AsyncMock()
            response = vclient.post(
                "/api/v1/videos/text-overlay",
                json={
                    "video_url": "https://example.com/video.mp4",
                    "text": "Hello World",
                    "options": {},
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data

    def test_create_text_overlay_missing_video_url(self, vclient):
        """Missing video_url should return 422."""
        response = vclient.post(
            "/api/v1/videos/text-overlay",
            json={"text": "Hello"},
        )
        assert response.status_code == 422

    def test_create_text_overlay_missing_text(self, vclient):
        """Missing text should return 422."""
        response = vclient.post(
            "/api/v1/videos/text-overlay",
            json={"video_url": "https://example.com/video.mp4"},
        )
        assert response.status_code == 422


# ── Video list ───────────────────────────────────────────────────────────────

class TestVideoList:
    """GET /api/v1/videos/"""

    def test_list_videos_empty(self, vclient):
        with patch("app.routes.video.videos.video_service") as mock_vs:
            mock_vs.get_all_videos = AsyncMock(return_value=[])
            response = vclient.get("/api/v1/videos/")
            assert response.status_code == 200
            data = response.json()
            assert data["videos"] == []
            assert data["page"] == 1
            assert data["limit"] == 20

    def test_list_videos_pagination_params(self, vclient):
        with patch("app.routes.video.videos.video_service") as mock_vs:
            mock_vs.get_all_videos = AsyncMock(return_value=[])
            response = vclient.get("/api/v1/videos/?page=2&limit=10")
            assert response.status_code == 200
            data = response.json()
            assert data["page"] == 2
            assert data["limit"] == 10

    def test_list_videos_invalid_page(self, vclient):
        """page < 1 should return 422."""
        response = vclient.get("/api/v1/videos/?page=0")
        assert response.status_code == 422

    def test_list_videos_invalid_limit(self, vclient):
        """limit > 100 should return 422."""
        response = vclient.get("/api/v1/videos/?limit=200")
        assert response.status_code == 422


# ── Video stats overview ─────────────────────────────────────────────────────

class TestVideoStats:
    """GET /api/v1/videos/stats/overview"""

    def test_get_video_stats(self, vclient):
        mock_stats = {
            "total_videos": 10,
            "total_duration_seconds": 120.5,
            "total_file_size_mb": 500.0,
        }
        with patch("app.routes.video.videos.video_service") as mock_vs:
            mock_vs.get_video_stats = AsyncMock(return_value=mock_stats)
            response = vclient.get("/api/v1/videos/stats/overview")
            assert response.status_code == 200
            data = response.json()
            assert data["total_videos"] == 10


# ── Caption style presets ────────────────────────────────────────────────────

class TestCaptionStylePresets:
    """GET /api/v1/videos/caption-styles/presets"""

    def test_get_caption_presets(self, vclient):
        response = vclient.get("/api/v1/videos/caption-styles/presets")
        assert response.status_code == 200
        data = response.json()
        assert "presets" in data
        assert "available_styles" in data
        assert "total_styles" in data
        assert isinstance(data["available_styles"], list)
        assert data["total_styles"] == len(data["available_styles"])


# ── Caption best practices ───────────────────────────────────────────────────

class TestCaptionBestPractices:
    """GET /api/v1/videos/caption-styles/best-practices"""

    def test_get_best_practices(self, vclient):
        response = vclient.get("/api/v1/videos/caption-styles/best-practices")
        assert response.status_code == 200
        data = response.json()
        assert "best_practices" in data


# ── Caption preview ──────────────────────────────────────────────────────────

class TestCaptionPreview:
    """POST /api/v1/videos/add-captions/preview"""

    def test_preview_valid_style(self, vclient):
        response = vclient.post(
            "/api/v1/videos/add-captions/preview",
            json={
                "video_url": "https://example.com/video.mp4",
                "text": "Hello world",
                "style": "karaoke",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["style"] == "karaoke"
        assert "rendering" in data

    def test_preview_unknown_style(self, vclient):
        response = vclient.post(
            "/api/v1/videos/add-captions/preview",
            json={
                "video_url": "https://example.com/video.mp4",
                "text": "Hello",
                "style": "nonexistent_style",
            },
        )
        assert response.status_code == 400


# ── Unauthenticated access ──────────────────────────────────────────────────

class TestUnauthenticatedAccess:
    """Verify that endpoints reject requests without auth."""

    def test_list_videos_no_auth(self, unauth_client):
        _disable_rate_limiting()
        response = unauth_client.get("/api/v1/videos/")
        # Should fail with 401 or 403 due to missing API key (or 429 from rate limiting)
        assert response.status_code in (401, 403, 429)

    def test_generate_video_no_auth(self, unauth_client):
        _disable_rate_limiting()
        response = unauth_client.post(
            "/api/v1/videos/generate",
            json={"prompt": "test"},
        )
        assert response.status_code in (401, 403, 429)
