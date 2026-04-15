"""
Tests for image-related API endpoints.

Covers:
- POST /api/v1/images/generate - Image generation
- GET /api/v1/images/models/together - Together AI models
- GET /api/v1/images/models/modal - Modal image models
- POST /api/v1/web_screenshot/capture - Web screenshot capture
- GET /api/v1/web_screenshot/devices - Available screenshot devices
- POST /api/v1/images/enhance - Image enhancement
- POST /api/v1/images/ai-edit - AI image editing
"""
import io
from unittest.mock import patch, MagicMock, AsyncMock

import pytest


@pytest.fixture(autouse=True)
def _disable_rate_limit():
    """Disable SecurityMiddleware rate limiting for all image tests."""
    with patch(
        "app.middleware.security.SecurityMiddleware._check_rate_limits",
        return_value=None,
    ):
        yield


# ---------------------------------------------------------------------------
# Image Generation: POST /api/v1/images/generate
# ---------------------------------------------------------------------------

class TestImageGeneration:
    """Tests for the image generation endpoint."""

    def test_generate_image_async_together(self, client, auth_headers):
        """Async image generation with Together provider returns a job_id."""
        with patch(
            "app.routes.image.generate.together_ai_service"
        ) as mock_svc, patch(
            "app.routes.image.generate.job_queue"
        ) as mock_jq:
            mock_svc.is_available.return_value = True
            mock_jq.add_job = AsyncMock()

            resp = client.post(
                "/api/v1/images/generate",
                json={
                    "prompt": "A sunset over the ocean",
                    "provider": "together",
                },
                headers=auth_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "job_id" in data
            assert data["job_id"] is not None

    def test_generate_image_async_modal(self, client, auth_headers):
        """Async image generation with modal_image provider returns a job_id."""
        with patch(
            "app.routes.image.generate.modal_image_service"
        ) as mock_svc, patch(
            "app.routes.image.generate.job_queue"
        ) as mock_jq:
            mock_svc.is_available.return_value = True
            mock_jq.add_job = AsyncMock()

            resp = client.post(
                "/api/v1/images/generate",
                json={
                    "prompt": "A mountain landscape",
                    "provider": "modal_image",
                },
                headers=auth_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "job_id" in data

    def test_generate_image_unsupported_provider(self, client, auth_headers):
        """Unsupported provider returns 400."""
        resp = client.post(
            "/api/v1/images/generate",
            json={
                "prompt": "A test prompt",
                "provider": "nonexistent_provider",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "Unsupported provider" in resp.json()["detail"]

    def test_generate_image_together_unavailable(self, client, auth_headers):
        """Together provider unavailable returns 503."""
        with patch(
            "app.routes.image.generate.together_ai_service"
        ) as mock_svc:
            mock_svc.is_available.return_value = False

            resp = client.post(
                "/api/v1/images/generate",
                json={
                    "prompt": "A test prompt",
                    "provider": "together",
                },
                headers=auth_headers,
            )
            assert resp.status_code == 503

    def test_generate_image_modal_unavailable(self, client, auth_headers):
        """Modal provider unavailable returns 503."""
        with patch(
            "app.routes.image.generate.modal_image_service"
        ) as mock_svc:
            mock_svc.is_available.return_value = False

            resp = client.post(
                "/api/v1/images/generate",
                json={
                    "prompt": "A test prompt",
                    "provider": "modal_image",
                },
                headers=auth_headers,
            )
            assert resp.status_code == 503

    def test_generate_image_missing_prompt(self, client, auth_headers):
        """Missing required prompt field returns 422."""
        resp = client.post(
            "/api/v1/images/generate",
            json={"provider": "together"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_generate_image_invalid_width(self, client, auth_headers):
        """Width out of range returns 422."""
        resp = client.post(
            "/api/v1/images/generate",
            json={
                "prompt": "test",
                "width": 50,  # below minimum 256
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_generate_image_invalid_height(self, client, auth_headers):
        """Height out of range returns 422."""
        resp = client.post(
            "/api/v1/images/generate",
            json={
                "prompt": "test",
                "height": 5000,  # above maximum 2048
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_generate_image_invalid_steps(self, client, auth_headers):
        """Steps out of range returns 422."""
        resp = client.post(
            "/api/v1/images/generate",
            json={
                "prompt": "test",
                "steps": 100,  # above max 50
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_generate_image_prompt_truncation(self, client, auth_headers):
        """Very long prompt is accepted (truncated by validator)."""
        with patch(
            "app.routes.image.generate.together_ai_service"
        ) as mock_svc, patch(
            "app.routes.image.generate.job_queue"
        ) as mock_jq:
            mock_svc.is_available.return_value = True
            mock_jq.add_job = AsyncMock()

            long_prompt = "x" * 3000
            resp = client.post(
                "/api/v1/images/generate",
                json={
                    "prompt": long_prompt,
                    "provider": "together",
                },
                headers=auth_headers,
            )
            assert resp.status_code == 200

    def test_generate_image_default_values(self, client, auth_headers):
        """Default values are applied correctly."""
        with patch(
            "app.routes.image.generate.together_ai_service"
        ) as mock_svc, patch(
            "app.routes.image.generate.job_queue"
        ) as mock_jq:
            mock_svc.is_available.return_value = True
            mock_jq.add_job = AsyncMock()

            resp = client.post(
                "/api/v1/images/generate",
                json={"prompt": "test"},
                headers=auth_headers,
            )
            assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Together AI Models: GET /api/v1/images/models/together
# ---------------------------------------------------------------------------

class TestTogetherModels:
    """Tests for the Together AI models list endpoint."""

    def test_list_together_models(self, client, auth_headers):
        """Returns a list of model names."""
        with patch(
            "app.routes.image.generate.together_ai_service"
        ) as mock_svc:
            mock_svc.get_available_models.return_value = [
                "black-forest-labs/FLUX.1-schnell",
                "stabilityai/stable-diffusion-xl",
            ]

            resp = client.get(
                "/api/v1/images/models/together",
                headers=auth_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "models" in data
            assert isinstance(data["models"], list)
            assert len(data["models"]) == 2

    def test_list_together_models_empty(self, client, auth_headers):
        """Empty model list is valid."""
        with patch(
            "app.routes.image.generate.together_ai_service"
        ) as mock_svc:
            mock_svc.get_available_models.return_value = []

            resp = client.get(
                "/api/v1/images/models/together",
                headers=auth_headers,
            )
            assert resp.status_code == 200
            assert resp.json()["models"] == []


# ---------------------------------------------------------------------------
# Modal Models: GET /api/v1/images/models/modal
# ---------------------------------------------------------------------------

class TestModalModels:
    """Tests for the Modal image models list endpoint."""

    def test_list_modal_models(self, client, auth_headers):
        """Returns a list of modal model names."""
        with patch(
            "app.routes.image.generate.modal_image_service"
        ) as mock_svc:
            mock_svc.get_available_models.return_value = ["modal-image"]

            resp = client.get(
                "/api/v1/images/models/modal",
                headers=auth_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "models" in data
            assert isinstance(data["models"], list)


# ---------------------------------------------------------------------------
# Web Screenshot Capture: POST /api/v1/web_screenshot/capture
# ---------------------------------------------------------------------------

class TestWebScreenshotCapture:
    """Tests for the web screenshot capture endpoint."""

    def test_capture_async_returns_job_id(self, client, auth_headers):
        """Async capture returns a job_id and status endpoint."""
        with patch(
            "app.routes.image.web_screenshot.job_queue"
        ) as mock_jq:
            mock_jq.add_job = AsyncMock()

            resp = client.post(
                "/api/v1/web_screenshot/capture",
                json={"url": "https://example.com"},
                headers=auth_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "job_id" in data

    def test_capture_missing_url(self, client, auth_headers):
        """Missing required URL returns 422."""
        resp = client.post(
            "/api/v1/web_screenshot/capture",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_capture_invalid_width(self, client, auth_headers):
        """Width below minimum returns 422."""
        resp = client.post(
            "/api/v1/web_screenshot/capture",
            json={"url": "https://example.com", "width": 50},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_capture_invalid_height(self, client, auth_headers):
        """Height above maximum returns 422."""
        resp = client.post(
            "/api/v1/web_screenshot/capture",
            json={"url": "https://example.com", "height": 5000},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_capture_invalid_timeout(self, client, auth_headers):
        """Timeout below minimum returns 422."""
        resp = client.post(
            "/api/v1/web_screenshot/capture",
            json={"url": "https://example.com", "timeout": 100},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_capture_invalid_wait_time(self, client, auth_headers):
        """Wait time above maximum returns 422."""
        resp = client.post(
            "/api/v1/web_screenshot/capture",
            json={"url": "https://example.com", "wait_time": 50000},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_capture_with_all_options(self, client, auth_headers):
        """Request with various options is accepted."""
        with patch(
            "app.routes.image.web_screenshot.job_queue"
        ) as mock_jq:
            mock_jq.add_job = AsyncMock()

            resp = client.post(
                "/api/v1/web_screenshot/capture",
                json={
                    "url": "https://example.com",
                    "width": 1920,
                    "height": 1080,
                    "device_type": "desktop",
                    "format": "png",
                    "full_page": True,
                    "wait_time": 5000,
                    "timeout": 60000,
                    "ignore_https_errors": True,
                    "color_scheme": "dark",
                },
                headers=auth_headers,
            )
            assert resp.status_code == 200

    def test_capture_invalid_color_scheme(self, client, auth_headers):
        """Invalid color_scheme pattern returns 422."""
        resp = client.post(
            "/api/v1/web_screenshot/capture",
            json={
                "url": "https://example.com",
                "color_scheme": "invalid",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_capture_invalid_media_type(self, client, auth_headers):
        """Invalid media_type pattern returns 422."""
        resp = client.post(
            "/api/v1/web_screenshot/capture",
            json={
                "url": "https://example.com",
                "media_type": "invalid",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Screenshot Devices: GET /api/v1/web_screenshot/devices
# ---------------------------------------------------------------------------

class TestWebScreenshotDevices:
    """Tests for the screenshot devices endpoint."""

    def test_list_devices(self, client):
        """Returns a list of device configurations."""
        with patch(
            "app.routes.image.web_screenshot.web_screenshot_service"
        ) as mock_svc:
            mock_svc.get_device_info.return_value = [
                {
                    "type": "desktop",
                    "name": "Desktop Chrome",
                    "viewport": {"width": 1920, "height": 1080},
                    "user_agent": "Mozilla/5.0",
                    "device_scale_factor": 1.0,
                    "is_mobile": False,
                    "has_touch": False,
                },
                {
                    "type": "mobile",
                    "name": "iPhone 14",
                    "viewport": {"width": 390, "height": 844},
                    "user_agent": "Mozilla/5.0 (iPhone)",
                    "device_scale_factor": 3.0,
                    "is_mobile": True,
                    "has_touch": True,
                },
            ]

            resp = client.get("/api/v1/web_screenshot/devices")
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) == 2
            # Verify device structure
            device = data[0]
            assert "type" in device
            assert "name" in device
            assert "viewport" in device
            assert "user_agent" in device
            assert "device_scale_factor" in device
            assert "is_mobile" in device
            assert "has_touch" in device

    def test_list_devices_structure(self, client):
        """Each device has the expected fields and types."""
        with patch(
            "app.routes.image.web_screenshot.web_screenshot_service"
        ) as mock_svc:
            mock_svc.get_device_info.return_value = [
                {
                    "type": "tablet",
                    "name": "iPad",
                    "viewport": {"width": 820, "height": 1180},
                    "user_agent": "Mozilla/5.0 (iPad)",
                    "device_scale_factor": 2.0,
                    "is_mobile": False,
                    "has_touch": True,
                },
            ]

            resp = client.get("/api/v1/web_screenshot/devices")
            assert resp.status_code == 200
            device = resp.json()[0]
            assert device["type"] == "tablet"
            assert device["viewport"]["width"] == 820
            assert device["is_mobile"] is False
            assert device["has_touch"] is True


# ---------------------------------------------------------------------------
# Image Enhancement: POST /api/v1/images/enhance
# ---------------------------------------------------------------------------

class TestImageEnhancement:
    """Tests for the image enhancement endpoint."""

    def test_enhance_image_valid(self, client):
        """Valid enhancement request returns a job_id."""
        with patch(
            "app.routes.image.enhancement.job_queue"
        ) as mock_jq:
            mock_jq.add_job = AsyncMock()

            resp = client.post(
                "/api/v1/images/enhance",
                json={
                    "image_url": "https://example.com/image.png",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "job_id" in data

    def test_enhance_image_with_all_options(self, client):
        """Enhancement with all options returns a job_id."""
        with patch(
            "app.routes.image.enhancement.job_queue"
        ) as mock_jq:
            mock_jq.add_job = AsyncMock()

            resp = client.post(
                "/api/v1/images/enhance",
                json={
                    "image_url": "https://example.com/image.png",
                    "enhance_color": 1.5,
                    "enhance_contrast": 1.2,
                    "noise_strength": 20,
                    "remove_artifacts": True,
                    "add_film_grain": True,
                    "vintage_effect": 0.5,
                    "output_format": "jpg",
                    "output_quality": 85,
                },
            )
            assert resp.status_code == 200
            assert "job_id" in resp.json()

    def test_enhance_image_missing_url(self, client):
        """Missing image_url returns 422."""
        resp = client.post(
            "/api/v1/images/enhance",
            json={},
        )
        assert resp.status_code == 422

    def test_enhance_image_invalid_url(self, client):
        """Invalid image_url format returns 422."""
        resp = client.post(
            "/api/v1/images/enhance",
            json={"image_url": "not-a-valid-url"},
        )
        assert resp.status_code == 422

    def test_enhance_image_color_out_of_range(self, client):
        """enhance_color above max returns 422."""
        resp = client.post(
            "/api/v1/images/enhance",
            json={
                "image_url": "https://example.com/image.png",
                "enhance_color": 3.0,  # max is 2.0
            },
        )
        assert resp.status_code == 422

    def test_enhance_image_contrast_out_of_range(self, client):
        """enhance_contrast below min returns 422."""
        resp = client.post(
            "/api/v1/images/enhance",
            json={
                "image_url": "https://example.com/image.png",
                "enhance_contrast": -1.0,  # min is 0.0
            },
        )
        assert resp.status_code == 422

    def test_enhance_image_noise_out_of_range(self, client):
        """noise_strength above max returns 422."""
        resp = client.post(
            "/api/v1/images/enhance",
            json={
                "image_url": "https://example.com/image.png",
                "noise_strength": 200,  # max is 100
            },
        )
        assert resp.status_code == 422

    def test_enhance_image_vintage_out_of_range(self, client):
        """vintage_effect above max returns 422."""
        resp = client.post(
            "/api/v1/images/enhance",
            json={
                "image_url": "https://example.com/image.png",
                "vintage_effect": 2.0,  # max is 1.0
            },
        )
        assert resp.status_code == 422

    def test_enhance_image_quality_out_of_range(self, client):
        """output_quality above max returns 422."""
        resp = client.post(
            "/api/v1/images/enhance",
            json={
                "image_url": "https://example.com/image.png",
                "output_quality": 200,  # max is 100
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# AI Image Edit: POST /api/v1/images/ai-edit
# ---------------------------------------------------------------------------

class TestAIImageEdit:
    """Tests for the AI image editing endpoint."""

    def _make_fake_image(self, size: int = 100) -> io.BytesIO:
        """Create a minimal fake PNG-like binary blob."""
        return io.BytesIO(b"\x89PNG" + b"\x00" * size)

    def test_ai_edit_valid(self, client, auth_headers):
        """Valid AI edit request with an image file returns a job_id."""
        with patch(
            "app.routes.image.generate.modal_image_service"
        ) as mock_svc, patch(
            "app.routes.image.generate.job_queue"
        ) as mock_jq:
            mock_svc.is_available.return_value = True
            mock_jq.add_job = AsyncMock()

            fake_image = self._make_fake_image()
            resp = client.post(
                "/api/v1/images/ai-edit",
                data={"prompt": "Make it brighter"},
                files={"image": ("test.png", fake_image, "image/png")},
                headers=auth_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "job_id" in data

    def test_ai_edit_missing_prompt(self, client, auth_headers):
        """Missing prompt field returns 422."""
        fake_image = self._make_fake_image()
        resp = client.post(
            "/api/v1/images/ai-edit",
            files={"image": ("test.png", fake_image, "image/png")},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_ai_edit_missing_image(self, client, auth_headers):
        """Missing image file returns 422."""
        resp = client.post(
            "/api/v1/images/ai-edit",
            data={"prompt": "Make it brighter"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_ai_edit_prompt_too_long(self, client, auth_headers):
        """Prompt exceeding 1000 chars returns 400."""
        with patch(
            "app.routes.image.generate.modal_image_service"
        ) as mock_svc:
            mock_svc.is_available.return_value = True

            fake_image = self._make_fake_image()
            long_prompt = "x" * 1001
            resp = client.post(
                "/api/v1/images/ai-edit",
                data={"prompt": long_prompt},
                files={"image": ("test.png", fake_image, "image/png")},
                headers=auth_headers,
            )
            assert resp.status_code == 400
            assert "Prompt too long" in resp.json()["detail"]

    def test_ai_edit_invalid_file_type(self, client, auth_headers):
        """Non-image file type returns 400."""
        fake_file = io.BytesIO(b"not an image")
        resp = client.post(
            "/api/v1/images/ai-edit",
            data={"prompt": "edit this"},
            files={"image": ("test.txt", fake_file, "text/plain")},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "Invalid file type" in resp.json()["detail"]

    def test_ai_edit_service_unavailable(self, client, auth_headers):
        """Modal service unavailable returns 503."""
        with patch(
            "app.routes.image.generate.modal_image_service"
        ) as mock_svc:
            mock_svc.is_available.return_value = False

            fake_image = self._make_fake_image()
            resp = client.post(
                "/api/v1/images/ai-edit",
                data={"prompt": "edit this"},
                files={"image": ("test.png", fake_image, "image/png")},
                headers=auth_headers,
            )
            assert resp.status_code == 503

    def test_ai_edit_file_too_large(self, client, auth_headers):
        """Image file exceeding 10MB returns 400."""
        with patch(
            "app.routes.image.generate.modal_image_service"
        ) as mock_svc:
            mock_svc.is_available.return_value = True

            # Create a file slightly over 10MB
            large_image = io.BytesIO(b"\x89PNG" + b"\x00" * (10 * 1024 * 1024 + 1))
            resp = client.post(
                "/api/v1/images/ai-edit",
                data={"prompt": "edit this"},
                files={"image": ("large.png", large_image, "image/png")},
                headers=auth_headers,
            )
            assert resp.status_code == 400
            assert "too large" in resp.json()["detail"]

    def test_ai_edit_with_optional_params(self, client, auth_headers):
        """AI edit with guidance_scale, steps, and seed is accepted."""
        with patch(
            "app.routes.image.generate.modal_image_service"
        ) as mock_svc, patch(
            "app.routes.image.generate.job_queue"
        ) as mock_jq:
            mock_svc.is_available.return_value = True
            mock_jq.add_job = AsyncMock()

            fake_image = self._make_fake_image()
            resp = client.post(
                "/api/v1/images/ai-edit",
                data={
                    "prompt": "Add a sunset",
                    "guidance_scale": "7.5",
                    "num_inference_steps": "30",
                    "seed": "42",
                },
                files={"image": ("test.png", fake_image, "image/png")},
                headers=auth_headers,
            )
            assert resp.status_code == 200
            assert "job_id" in resp.json()
