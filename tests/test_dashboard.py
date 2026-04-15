"""
Tests for dashboard, jobs, library, diagnostics, and admin endpoints.

Covers:
- GET /api/v1/dashboard/stats
- GET /api/v1/dashboard/recent-activity
- GET /api/v1/dashboard/system-info
- GET /api/v1/dashboard/settings
- GET /api/v1/dashboard/api-keys
- POST /api/v1/dashboard/api-keys (create API key)
- DELETE /api/v1/dashboard/api-keys/{key_id}
- GET /api/v1/jobs
- GET /api/v1/library/content
- GET /api/v1/library/stats
- GET /api/v1/diagnostics/api-keys
- GET /api/v1/diagnostics/service-health
- Admin endpoints (/admin, /admin/login, /admin/verify, /admin/stats, etc.)
- Auth enforcement (unauth_client)
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.fixture(autouse=True)
def disable_rate_limiting():
    """Disable security middleware rate limiting for all tests in this module."""
    with patch(
        "app.middleware.security.SecurityMiddleware._check_rate_limits",
        return_value=None,
    ):
        yield


# ── Dashboard Stats ─────────────────────────────────────────────────────────


class TestDashboardStats:
    """Tests for GET /api/v1/dashboard/stats."""

    def test_dashboard_stats_returns_200(self, client, auth_headers):
        """Dashboard stats should return 200 with valid structure."""
        with patch(
            "app.routes.dashboard.dashboard.db_job_service"
        ) as mock_db_jobs, patch(
            "app.routes.dashboard.dashboard.user_service"
        ) as mock_user_svc, patch(
            "app.routes.dashboard.dashboard.api_key_service"
        ) as mock_api_svc, patch(
            "app.routes.dashboard.dashboard.calculate_average_processing_time",
            new_callable=AsyncMock,
            return_value=12.5,
        ), patch(
            "app.routes.dashboard.dashboard.calculate_storage_usage",
            new_callable=AsyncMock,
            return_value=(1.5, 100.0),
        ):
            mock_db_jobs.get_job_count_by_status = AsyncMock(return_value={})
            mock_db_jobs.get_video_creation_jobs_count = AsyncMock(return_value=5)
            mock_user_svc.get_user_stats = AsyncMock(
                return_value={"total_users": 3}
            )
            mock_api_svc.get_api_key_stats = AsyncMock(
                return_value={"active_keys": 2}
            )

            response = client.get(
                "/api/v1/dashboard/stats", headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "total_videos" in data
            assert "active_jobs" in data
            assert "completed_jobs" in data
            assert "failed_jobs" in data
            assert "total_users" in data
            assert "active_api_keys" in data
            assert data["total_videos"] == 5
            assert data["total_users"] == 3
            assert data["active_api_keys"] == 2

    def test_dashboard_stats_handles_db_errors(self, client, auth_headers):
        """Dashboard stats should handle database errors gracefully."""
        with patch(
            "app.routes.dashboard.dashboard.db_job_service"
        ) as mock_db_jobs, patch(
            "app.routes.dashboard.dashboard.user_service"
        ) as mock_user_svc, patch(
            "app.routes.dashboard.dashboard.api_key_service"
        ) as mock_api_svc, patch(
            "app.routes.dashboard.dashboard.calculate_average_processing_time",
            new_callable=AsyncMock,
            return_value=0.0,
        ), patch(
            "app.routes.dashboard.dashboard.calculate_storage_usage",
            new_callable=AsyncMock,
            return_value=(None, None),
        ):
            mock_db_jobs.get_job_count_by_status = AsyncMock(
                side_effect=Exception("DB error")
            )
            mock_db_jobs.get_video_creation_jobs_count = AsyncMock(
                side_effect=Exception("DB error")
            )
            mock_user_svc.get_user_stats = AsyncMock(
                side_effect=Exception("DB error")
            )
            mock_api_svc.get_api_key_stats = AsyncMock(
                side_effect=Exception("DB error")
            )

            response = client.get(
                "/api/v1/dashboard/stats", headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["total_videos"] == 0
            assert data["total_users"] == 0
            assert data["active_api_keys"] == 0


# ── Dashboard Recent Activity ────────────────────────────────────────────────


class TestDashboardRecentActivity:
    """Tests for GET /api/v1/dashboard/recent-activity."""

    def test_recent_activity_returns_list(self, client, auth_headers):
        """Recent activity endpoint should return a list."""
        with patch(
            "app.routes.dashboard.dashboard.db_job_service"
        ) as mock_db_jobs:
            mock_db_jobs.get_all_jobs = AsyncMock(return_value=[])

            response = client.get(
                "/api/v1/dashboard/recent-activity", headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_recent_activity_with_limit(self, client, auth_headers):
        """Recent activity should accept limit parameter."""
        with patch(
            "app.routes.dashboard.dashboard.db_job_service"
        ) as mock_db_jobs:
            mock_db_jobs.get_all_jobs = AsyncMock(return_value=[])

            response = client.get(
                "/api/v1/dashboard/recent-activity?limit=5",
                headers=auth_headers,
            )
            assert response.status_code == 200

    def test_recent_activity_handles_errors(self, client, auth_headers):
        """Recent activity should return empty list on error."""
        with patch(
            "app.routes.dashboard.dashboard.db_job_service"
        ) as mock_db_jobs:
            mock_db_jobs.get_all_jobs = AsyncMock(
                side_effect=Exception("DB error")
            )

            response = client.get(
                "/api/v1/dashboard/recent-activity", headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data == []


# ── Dashboard System Info ────────────────────────────────────────────────────


class TestDashboardSystemInfo:
    """Tests for GET /api/v1/dashboard/system-info."""

    def test_system_info_returns_200(self, client, auth_headers):
        """System info should return 200."""
        with patch(
            "app.routes.dashboard.dashboard.settings_service"
        ) as mock_settings:
            mock_settings.get_system_info = AsyncMock(
                return_value={
                    "version": "1.0.0",
                    "python_version": "3.12",
                    "uptime": 3600,
                }
            )

            response = client.get(
                "/api/v1/dashboard/system-info", headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "version" in data

    def test_system_info_error_returns_500(self, client, auth_headers):
        """System info should return 500 on service failure."""
        with patch(
            "app.routes.dashboard.dashboard.settings_service"
        ) as mock_settings:
            mock_settings.get_system_info = AsyncMock(
                side_effect=Exception("Service error")
            )

            response = client.get(
                "/api/v1/dashboard/system-info", headers=auth_headers
            )
            assert response.status_code == 500


# ── Dashboard Settings ───────────────────────────────────────────────────────


class TestDashboardSettings:
    """Tests for GET /api/v1/dashboard/settings."""

    def test_settings_returns_defaults_on_error(self, client, auth_headers):
        """Settings should return defaults when DB is unavailable."""
        with patch(
            "app.routes.dashboard.dashboard.settings_service"
        ) as mock_settings:
            mock_settings.get_all_settings = AsyncMock(
                side_effect=Exception("DB unavailable")
            )

            response = client.get(
                "/api/v1/dashboard/settings", headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["auto_refresh"] is True
            assert data["max_concurrent_jobs"] == 5
            assert data["default_video_resolution"] == "1080x1920"
            assert data["storage_retention_days"] == 90

    def test_settings_returns_db_values(self, client, auth_headers):
        """Settings should return values from database when available."""
        with patch(
            "app.routes.dashboard.dashboard.settings_service"
        ) as mock_settings:
            mock_settings.get_all_settings = AsyncMock(
                return_value={
                    "auto_refresh": False,
                    "email_notifications": False,
                    "api_logging": False,
                    "max_concurrent_jobs": 10,
                    "default_video_resolution": "720x1280",
                    "storage_retention_days": 30,
                }
            )

            response = client.get(
                "/api/v1/dashboard/settings", headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["auto_refresh"] is False
            assert data["max_concurrent_jobs"] == 10
            assert data["default_video_resolution"] == "720x1280"


# ── Dashboard API Keys ──────────────────────────────────────────────────────


class TestDashboardApiKeys:
    """Tests for /api/v1/dashboard/api-keys CRUD endpoints."""

    def test_list_api_keys(self, client, auth_headers):
        """GET /api/v1/dashboard/api-keys should return paginated list."""
        with patch(
            "app.routes.dashboard.dashboard.api_key_service"
        ) as mock_svc:
            mock_svc.list_api_keys = AsyncMock(
                return_value={
                    "api_keys": [],
                    "pagination": {
                        "total_count": 0,
                        "total_pages": 0,
                    },
                }
            )

            response = client.get(
                "/api/v1/dashboard/api-keys", headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "api_keys" in data
            assert "total" in data
            assert "pages" in data

    def test_create_api_key_validates_name(self, client, auth_headers):
        """POST /api/v1/dashboard/api-keys should require name field."""
        response = client.post(
            "/api/v1/dashboard/api-keys",
            headers=auth_headers,
            json={},  # Missing required "name"
        )
        assert response.status_code == 422  # Validation error

    def test_create_api_key_success(self, client, auth_headers):
        """POST /api/v1/dashboard/api-keys should create key and return it."""
        with patch(
            "app.routes.dashboard.dashboard.api_key_service"
        ) as mock_svc:
            mock_svc.create_api_key = AsyncMock(
                return_value={
                    "key_id": "new-key-id",
                    "name": "Test Key",
                    "key": "oui_sk_abc123",
                    "user_id": "1",
                    "user_email": "test@example.com",
                    "is_active": True,
                    "created_at": "2024-01-01T00:00:00",
                    "last_used": None,
                    "expires_at": None,
                    "usage_count": 0,
                    "rate_limit": 100,
                    "permissions": [],
                }
            )

            response = client.post(
                "/api/v1/dashboard/api-keys",
                headers=auth_headers,
                json={"name": "Test Key"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Key"
            assert data["key"] == "oui_sk_abc123"

    def test_delete_api_key_success(self, client, auth_headers):
        """DELETE /api/v1/dashboard/api-keys/{key_id} should delete the key."""
        with patch(
            "app.routes.dashboard.dashboard.api_key_service"
        ) as mock_svc:
            mock_svc.get_api_key = AsyncMock(
                return_value={"user_id": "1"}
            )
            mock_svc.delete_api_key = AsyncMock(return_value=True)

            response = client.delete(
                "/api/v1/dashboard/api-keys/test-key-id",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert "deleted" in data["message"].lower()

    def test_delete_api_key_not_found(self, client, auth_headers):
        """DELETE returns 404 when key doesn't exist."""
        with patch(
            "app.routes.dashboard.dashboard.api_key_service"
        ) as mock_svc:
            mock_svc.get_api_key = AsyncMock(return_value={"user_id": "1"})
            mock_svc.delete_api_key = AsyncMock(return_value=False)

            response = client.delete(
                "/api/v1/dashboard/api-keys/nonexistent",
                headers=auth_headers,
            )
            assert response.status_code == 404


# ── Jobs Endpoints ──────────────────────────────────────────────────────────


class TestJobs:
    """Tests for /api/v1/jobs endpoints."""

    def test_list_jobs_returns_200(self, client, auth_headers):
        """GET /api/v1/jobs should return job list."""
        with patch(
            "app.routes.jobs.jobs.job_queue"
        ) as mock_jq:
            mock_jq.get_all_jobs = AsyncMock(return_value=[])

            response = client.get(
                "/api/v1/jobs", headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "jobs" in data["data"]
            assert isinstance(data["data"]["jobs"], list)

    def test_list_jobs_with_pagination(self, client, auth_headers):
        """GET /api/v1/jobs should support pagination parameters."""
        with patch(
            "app.routes.jobs.jobs.job_queue"
        ) as mock_jq:
            mock_jq.get_all_jobs = AsyncMock(return_value=[])

            response = client.get(
                "/api/v1/jobs?page=1&limit=10&all=false",
                headers=auth_headers,
            )
            assert response.status_code == 200

    def test_get_job_status_not_found(self, client, auth_headers):
        """GET /api/v1/jobs/{job_id}/status should return 404 for missing job."""
        with patch(
            "app.routes.jobs.jobs.job_queue"
        ) as mock_jq:
            mock_jq.get_job_info = AsyncMock(return_value=None)

            response = client.get(
                "/api/v1/jobs/nonexistent-id/status",
                headers=auth_headers,
            )
            assert response.status_code == 404

    def test_delete_job_not_found(self, client, auth_headers):
        """DELETE /api/v1/jobs/{job_id} should return 404 for missing job."""
        with patch(
            "app.routes.jobs.jobs.job_queue"
        ) as mock_jq:
            mock_jq.get_job_info = AsyncMock(return_value=None)

            response = client.delete(
                "/api/v1/jobs/nonexistent-id",
                headers=auth_headers,
            )
            assert response.status_code == 404


# ── Library Endpoints ────────────────────────────────────────────────────────


class TestLibrary:
    """Tests for /api/v1/library endpoints."""

    def test_library_content_returns_200(self, client, auth_headers):
        """GET /api/v1/library/content should return library response."""
        response = client.get(
            "/api/v1/library/content", headers=auth_headers
        )
        # Library gracefully returns empty on DB errors
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "total_count" in data
        assert "pagination" in data

    def test_library_content_with_filters(self, client, auth_headers):
        """GET /api/v1/library/content should accept filter parameters."""
        response = client.get(
            "/api/v1/library/content?content_type=video&limit=10&offset=0",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_library_stats_returns_200(self, client, auth_headers):
        """GET /api/v1/library/stats should return stats."""
        response = client.get(
            "/api/v1/library/stats", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        assert "total_items" in data
        stats = data["stats"]
        assert "video" in stats
        assert "audio" in stats
        assert "image" in stats


# ── Diagnostics Endpoints ────────────────────────────────────────────────────


class TestDiagnostics:
    """Tests for /api/v1/diagnostics endpoints."""

    def test_api_keys_diagnostics(self, client, auth_headers):
        """GET /api/v1/diagnostics/api-keys should return key status."""
        response = client.get(
            "/api/v1/diagnostics/api-keys", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "ai_services" in data
        assert "storage" in data
        assert "recommendations" in data

    def test_service_health(self, client, auth_headers):
        """GET /api/v1/diagnostics/service-health should return health info."""
        with patch(
            "app.routes.diagnostics.diagnostics._check_database_health",
            new_callable=AsyncMock,
            return_value={"status": "down", "message": "Not connected"},
        ):
            response = client.get(
                "/api/v1/diagnostics/service-health", headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "overall_status" in data


# ── Admin Endpoints ──────────────────────────────────────────────────────────


class TestAdmin:
    """Tests for /admin endpoints."""

    def test_admin_page_returns_html(self, client):
        """GET /admin should return HTML redirect page."""
        response = client.get("/admin")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_admin_login_valid_credentials(self, client):
        """POST /admin/login should succeed with correct credentials."""
        import os
        response = client.post(
            "/admin/login",
            json={
                "username": os.environ.get("ADMIN_USERNAME", "admin"),
                "password": os.environ.get("ADMIN_PASSWORD", "admin"),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_admin_login_invalid_credentials(self, client):
        """POST /admin/login should fail with wrong credentials."""
        response = client.post(
            "/admin/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert response.status_code == 401

    def test_admin_verify_no_cookie(self, client):
        """GET /admin/verify should fail without session cookie."""
        response = client.get("/admin/verify")
        assert response.status_code == 401

    def test_admin_stats(self, client, auth_headers):
        """GET /admin/stats should return stats dict."""
        with patch(
            "app.routes.admin.admin.redis_service"
        ) as mock_redis:
            mock_redis.ping = AsyncMock(side_effect=Exception("no redis"))

            response = client.get(
                "/admin/stats", headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "active_jobs" in data
            assert "redis_connected" in data

    def test_admin_system_info(self, client, auth_headers):
        """GET /admin/system should return system config."""
        response = client.get(
            "/admin/system", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "debug" in data
        assert "s3_bucket" in data

    def test_admin_jobs(self, client, auth_headers):
        """GET /admin/jobs should return jobs list."""
        with patch(
            "app.routes.admin.admin.redis_service"
        ) as mock_redis:
            mock_redis.ping = AsyncMock(side_effect=Exception("no redis"))

            response = client.get(
                "/admin/jobs", headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "jobs" in data


# ── Auth Enforcement ─────────────────────────────────────────────────────────


class TestAuthEnforcement:
    """Test that endpoints reject unauthenticated requests."""

    def test_dashboard_stats_requires_auth(self, unauth_client):
        """Dashboard stats should reject requests without auth."""
        response = unauth_client.get("/api/v1/dashboard/stats")
        assert response.status_code in (401, 403)

    def test_dashboard_settings_requires_auth(self, unauth_client):
        """Dashboard settings should reject requests without auth."""
        response = unauth_client.get("/api/v1/dashboard/settings")
        assert response.status_code in (401, 403)

    def test_jobs_requires_auth(self, unauth_client):
        """Jobs list should reject requests without auth."""
        response = unauth_client.get("/api/v1/jobs")
        assert response.status_code in (401, 403)

    def test_library_content_requires_auth(self, unauth_client):
        """Library content should reject requests without auth."""
        response = unauth_client.get("/api/v1/library/content")
        assert response.status_code in (401, 403)

    def test_diagnostics_requires_auth(self, unauth_client):
        """Diagnostics should reject requests without auth."""
        response = unauth_client.get("/api/v1/diagnostics/api-keys")
        assert response.status_code in (401, 403)

    def test_admin_stats_requires_auth(self, unauth_client):
        """Admin stats should reject requests without auth."""
        response = unauth_client.get("/admin/stats")
        assert response.status_code in (401, 403)
