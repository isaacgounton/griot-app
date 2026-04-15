"""
Tests for authentication routes: /api/v1/auth/*

Covers:
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- GET  /api/v1/auth/status
- POST /api/v1/auth/validate
- GET  /api/v1/auth/profile
- PUT  /api/v1/auth/profile
- POST /api/v1/auth/change-password
- POST /api/v1/auth/verify-email
- Auth enforcement on protected endpoints
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_user(**overrides):
    """Return a MagicMock that behaves like a database User row."""
    defaults = dict(
        id=1,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password="$2b$12$validbcrypthashvaluehere1234567890abcdef",
        role=MagicMock(value="user"),
        is_active=True,
        is_verified=True,
        verification_token=None,
        verification_token_expires_at=None,
        created_at=datetime(2025, 1, 1, tzinfo=None),
        last_login=None,
    )
    defaults.update(overrides)
    user = MagicMock(**defaults)
    return user


def _scalars_returning(value):
    """Create a mock Result whose .scalars().first() returns *value*."""
    scalars = MagicMock()
    scalars.first = MagicMock(return_value=value)
    scalars.all = MagicMock(return_value=[value] if value else [])
    result = MagicMock(scalars=MagicMock(return_value=scalars))
    return result


def _reset_rate_limiter():
    """Clear the rate limiter state to avoid 429s between test fixtures."""
    try:
        from app.middleware.security import SecurityMiddleware
        instance = SecurityMiddleware.get_instance()
        if instance:
            instance.request_count.clear()
            instance.suspicious_count.clear()
            instance.blocked_ips.clear()
            instance.temp_blocked_ips.clear()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_client(mock_database_service):
    """
    TestClient with BOTH get_api_key AND get_current_user overridden.
    Required for endpoints that use Depends(get_current_user).
    """
    from unittest.mock import patch, AsyncMock

    with patch("app.database.DatabaseService.initialize", new_callable=AsyncMock), \
         patch("app.database.DatabaseService.create_tables", new_callable=AsyncMock), \
         patch("app.database.DatabaseService.update_enums", new_callable=AsyncMock), \
         patch("app.database.DatabaseService.migrate_schema", new_callable=AsyncMock):

        from fastapi.testclient import TestClient
        from app.main import app
        from app.utils.auth import get_api_key, get_current_user

        async def override_get_api_key(request=None, api_key_header=None):
            if request and hasattr(request, 'state'):
                request.state.api_key_info = {
                    "id": "test",
                    "key_id": "test-key-id",
                    "name": "Test API Key",
                    "user_id": "1",
                    "user_email": "test@example.com",
                    "user_role": "admin",
                    "rate_limit": None,
                    "monthly_quota": None,
                    "usage_count": 0,
                }
            return "test-api-key"

        async def override_get_current_user(request=None):
            return {
                "user_id": "1",
                "user_role": "admin",
                "user_email": "test@example.com",
            }

        app.dependency_overrides[get_api_key] = override_get_api_key
        app.dependency_overrides[get_current_user] = override_get_current_user

        with TestClient(
            app,
            raise_server_exceptions=False,
            base_url="http://localhost",
            headers={"Host": "localhost"},
        ) as test_client:
            _reset_rate_limiter()
            yield test_client

        app.dependency_overrides.clear()


# ═══════════════════════════════════════════════════════════════════════════
# GET /api/v1/auth/status  (no auth required, no DB)
# ═══════════════════════════════════════════════════════════════════════════

class TestAuthStatus:
    def test_returns_unauthenticated(self, client):
        resp = client.get("/api/v1/auth/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["isAuthenticated"] is False
        assert "message" in data


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/v1/auth/register
# ═══════════════════════════════════════════════════════════════════════════

class TestRegister:
    ENDPOINT = "/api/v1/auth/register"

    VALID_PAYLOAD = {
        "full_name": "New User",
        "email": "new@example.com",
        "username": "newuser",
        "password": "securepassword123",
    }

    # ---- validation failures ----

    def test_missing_full_name(self, client):
        payload = {**self.VALID_PAYLOAD, "full_name": ""}
        resp = client.post(self.ENDPOINT, json=payload)
        assert resp.status_code == 400
        assert "Full name" in resp.json()["detail"]

    def test_invalid_email(self, client):
        payload = {**self.VALID_PAYLOAD, "email": "not-an-email"}
        resp = client.post(self.ENDPOINT, json=payload)
        assert resp.status_code == 400
        assert "email" in resp.json()["detail"].lower()

    def test_short_username(self, client):
        payload = {**self.VALID_PAYLOAD, "username": "ab"}
        resp = client.post(self.ENDPOINT, json=payload)
        assert resp.status_code == 400
        assert "3 characters" in resp.json()["detail"]

    def test_short_password(self, client):
        payload = {**self.VALID_PAYLOAD, "password": "short"}
        resp = client.post(self.ENDPOINT, json=payload)
        assert resp.status_code == 400
        assert "8 characters" in resp.json()["detail"]

    def test_missing_fields_returns_422(self, client):
        """Pydantic rejects the request before reaching route logic."""
        resp = client.post(self.ENDPOINT, json={"full_name": "Only Name"})
        assert resp.status_code == 422

    # ---- successful registration (mock DB) ----

    def test_successful_registration(self, client):
        """Successful register returns 200 with success=True."""
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            return _scalars_returning(None)

        mock_session = AsyncMock()
        mock_session.execute = mock_execute
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock(side_effect=lambda u: setattr(u, "id", 42))

        async def mock_get_session():
            yield mock_session

        with patch("app.routes.auth.auth.database_service") as mock_db, \
             patch("app.routes.auth.auth.hash_password", return_value="$2b$12$validhash"), \
             patch("app.routes.auth.auth.generate_verification_token", return_value="tok123"), \
             patch("app.routes.auth.auth.get_verification_token_expiry", return_value=datetime(2099, 1, 1)), \
             patch("app.routes.auth.auth.send_verification_email", new_callable=AsyncMock, return_value=False):
            mock_db.is_database_available.return_value = True
            mock_db.get_session = mock_get_session

            resp = client.post(self.ENDPOINT, json=self.VALID_PAYLOAD)

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    # ---- duplicate username / email ----

    def test_duplicate_username(self, client):
        existing_user = _make_mock_user()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _scalars_returning(existing_user)
            return _scalars_returning(None)

        mock_session = AsyncMock()
        mock_session.execute = mock_execute

        async def mock_get_session():
            yield mock_session

        with patch("app.routes.auth.auth.database_service") as mock_db:
            mock_db.is_database_available.return_value = True
            mock_db.get_session = mock_get_session

            resp = client.post(self.ENDPOINT, json=self.VALID_PAYLOAD)

        assert resp.status_code == 400
        assert "Username already taken" in resp.json()["detail"]

    def test_duplicate_email(self, client):
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _scalars_returning(None)
            if call_count == 2:
                return _scalars_returning(_make_mock_user())
            return _scalars_returning(None)

        mock_session = AsyncMock()
        mock_session.execute = mock_execute

        async def mock_get_session():
            yield mock_session

        with patch("app.routes.auth.auth.database_service") as mock_db:
            mock_db.is_database_available.return_value = True
            mock_db.get_session = mock_get_session

            resp = client.post(self.ENDPOINT, json=self.VALID_PAYLOAD)

        assert resp.status_code == 400
        assert "Email already registered" in resp.json()["detail"]

    # ---- DB unavailable ----

    def test_db_unavailable(self, client):
        with patch("app.routes.auth.auth.database_service") as mock_db:
            mock_db.is_database_available.return_value = False
            resp = client.post(self.ENDPOINT, json=self.VALID_PAYLOAD)

        assert resp.status_code == 503


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/v1/auth/login
# ═══════════════════════════════════════════════════════════════════════════

class TestLogin:
    ENDPOINT = "/api/v1/auth/login"

    def test_missing_credentials(self, client):
        resp = client.post(self.ENDPOINT, json={"username": "", "password": ""})
        assert resp.status_code == 400

    def test_user_not_found(self, client):
        async def mock_execute(stmt):
            return _scalars_returning(None)

        mock_session = AsyncMock()
        mock_session.execute = mock_execute

        async def mock_get_session():
            yield mock_session

        with patch("app.routes.auth.auth.database_service") as mock_db:
            mock_db.is_database_available.return_value = True
            mock_db.get_session = mock_get_session

            resp = client.post(self.ENDPOINT, json={
                "username": "nonexistent",
                "password": "password123",
            })

        assert resp.status_code == 401
        assert "Invalid username or password" in resp.json()["detail"]

    def test_wrong_password(self, client):
        user = _make_mock_user()

        async def mock_execute(stmt):
            return _scalars_returning(user)

        mock_session = AsyncMock()
        mock_session.execute = mock_execute

        async def mock_get_session():
            yield mock_session

        with patch("app.routes.auth.auth.database_service") as mock_db, \
             patch("app.routes.auth.auth.verify_password", return_value=False):
            mock_db.is_database_available.return_value = True
            mock_db.get_session = mock_get_session

            resp = client.post(self.ENDPOINT, json={
                "username": "testuser",
                "password": "wrongpassword",
            })

        assert resp.status_code == 401

    def test_unverified_user(self, client):
        user = _make_mock_user(is_verified=False)

        async def mock_execute(stmt):
            return _scalars_returning(user)

        mock_session = AsyncMock()
        mock_session.execute = mock_execute

        async def mock_get_session():
            yield mock_session

        with patch("app.routes.auth.auth.database_service") as mock_db, \
             patch("app.routes.auth.auth.verify_password", return_value=True):
            mock_db.is_database_available.return_value = True
            mock_db.get_session = mock_get_session

            resp = client.post(self.ENDPOINT, json={
                "username": "testuser",
                "password": "password123",
            })

        assert resp.status_code == 403
        assert "verify your email" in resp.json()["detail"].lower()

    def test_inactive_user(self, client):
        user = _make_mock_user(is_active=False)

        async def mock_execute(stmt):
            return _scalars_returning(user)

        mock_session = AsyncMock()
        mock_session.execute = mock_execute

        async def mock_get_session():
            yield mock_session

        with patch("app.routes.auth.auth.database_service") as mock_db, \
             patch("app.routes.auth.auth.verify_password", return_value=True):
            mock_db.is_database_available.return_value = True
            mock_db.get_session = mock_get_session

            resp = client.post(self.ENDPOINT, json={
                "username": "testuser",
                "password": "password123",
            })

        assert resp.status_code == 403
        assert "deactivated" in resp.json()["detail"].lower()

    def test_successful_login(self, client):
        user = _make_mock_user()

        async def mock_execute(stmt):
            return _scalars_returning(user)

        mock_session = AsyncMock()
        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        async def mock_get_session():
            yield mock_session

        with patch("app.routes.auth.auth.database_service") as mock_db, \
             patch("app.routes.auth.auth.verify_password", return_value=True), \
             patch("app.routes.auth.auth.create_access_token", return_value="fake.jwt.token"), \
             patch("app.routes.auth.auth.set_auth_cookie"):
            mock_db.is_database_available.return_value = True
            mock_db.get_session = mock_get_session

            resp = client.post(self.ENDPOINT, json={
                "username": "testuser",
                "password": "password123",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["username"] == "testuser"
        assert data["api_key"] == "fake.jwt.token"

    def test_db_unavailable(self, client):
        with patch("app.routes.auth.auth.database_service") as mock_db:
            mock_db.is_database_available.return_value = False

            resp = client.post(self.ENDPOINT, json={
                "username": "testuser",
                "password": "password123",
            })

        assert resp.status_code == 503

    def test_invalid_hash_format(self, client):
        user = _make_mock_user(hashed_password="invalidhash")

        async def mock_execute(stmt):
            return _scalars_returning(user)

        mock_session = AsyncMock()
        mock_session.execute = mock_execute

        async def mock_get_session():
            yield mock_session

        with patch("app.routes.auth.auth.database_service") as mock_db:
            mock_db.is_database_available.return_value = True
            mock_db.get_session = mock_get_session

            resp = client.post(self.ENDPOINT, json={
                "username": "testuser",
                "password": "password123",
            })

        assert resp.status_code == 401
        assert "password reset" in resp.json()["detail"].lower()


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/v1/auth/validate
# ═══════════════════════════════════════════════════════════════════════════

class TestValidateApiKey:
    ENDPOINT = "/api/v1/auth/validate"

    def test_missing_api_key(self, client):
        resp = client.post(self.ENDPOINT)
        assert resp.status_code == 400

    def test_valid_env_api_key(self, client):
        with patch.dict("os.environ", {"API_KEY": "env-test-key"}):
            resp = client.post(self.ENDPOINT, params={"api_key": "env-test-key"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True

    def test_invalid_api_key(self, client):
        with patch("app.routes.auth.auth.api_key_service") as mock_svc:
            mock_svc.validate_api_key = AsyncMock(return_value=None)
            resp = client.post(self.ENDPOINT, params={"api_key": "bad-key"})
        assert resp.status_code == 401

    def test_valid_db_api_key(self, client):
        with patch("app.routes.auth.auth.api_key_service") as mock_svc:
            mock_svc.validate_api_key = AsyncMock(return_value={"user_id": 1})
            resp = client.post(self.ENDPOINT, params={"api_key": "db-key"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["user_id"] == 1


# ═══════════════════════════════════════════════════════════════════════════
# GET /api/v1/auth/profile  (requires get_current_user)
# ═══════════════════════════════════════════════════════════════════════════

class TestGetProfile:
    ENDPOINT = "/api/v1/auth/profile"

    def test_returns_profile(self, auth_client):
        admin_user = _make_mock_user(role=MagicMock(value="admin"))

        async def mock_execute(stmt):
            return _scalars_returning(admin_user)

        mock_session = AsyncMock()
        mock_session.execute = mock_execute

        async def mock_get_session():
            yield mock_session

        with patch("app.routes.auth.auth.database_service") as mock_db:
            mock_db.is_database_available.return_value = True
            mock_db.get_session = mock_get_session

            resp = auth_client.get(self.ENDPOINT)

        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testuser"
        assert data["role"] == "admin"

    def test_fallback_when_db_unavailable(self, auth_client):
        with patch("app.routes.auth.auth.database_service") as mock_db:
            mock_db.is_database_available.return_value = False

            resp = auth_client.get(self.ENDPOINT)

        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"  # fallback default

    def test_unauthenticated_rejected(self, unauth_client):
        _reset_rate_limiter()
        resp = unauth_client.get(self.ENDPOINT)
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# PUT /api/v1/auth/profile  (requires get_current_user)
# ═══════════════════════════════════════════════════════════════════════════

class TestUpdateProfile:
    ENDPOINT = "/api/v1/auth/profile"

    def test_update_full_name(self, auth_client):
        user = _make_mock_user(role=MagicMock(value="admin"))
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _scalars_returning(user)
            return _scalars_returning(None)

        mock_session = AsyncMock()
        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        async def mock_get_session():
            yield mock_session

        with patch("app.routes.auth.auth.database_service") as mock_db:
            mock_db.is_database_available.return_value = True
            mock_db.get_session = mock_get_session

            resp = auth_client.put(self.ENDPOINT, json={"full_name": "Updated Name"})

        assert resp.status_code == 200

    def test_db_unavailable(self, auth_client):
        with patch("app.routes.auth.auth.database_service") as mock_db:
            mock_db.is_database_available.return_value = False

            resp = auth_client.put(self.ENDPOINT, json={"full_name": "X"})

        assert resp.status_code == 503

    def test_unauthenticated_rejected(self, unauth_client):
        _reset_rate_limiter()
        resp = unauth_client.put(self.ENDPOINT, json={"full_name": "Hacker"})
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/v1/auth/change-password  (requires get_current_user)
# ═══════════════════════════════════════════════════════════════════════════

class TestChangePassword:
    ENDPOINT = "/api/v1/auth/change-password"

    def test_short_new_password(self, auth_client):
        resp = auth_client.post(self.ENDPOINT, json={
            "current_password": "oldpassword123",
            "new_password": "short",
        })
        assert resp.status_code == 400
        assert "8 characters" in resp.json()["detail"]

    def test_wrong_current_password(self, auth_client):
        user = _make_mock_user(role=MagicMock(value="admin"))

        async def mock_execute(stmt):
            return _scalars_returning(user)

        mock_session = AsyncMock()
        mock_session.execute = mock_execute

        async def mock_get_session():
            yield mock_session

        with patch("app.routes.auth.auth.database_service") as mock_db, \
             patch("app.routes.auth.auth.verify_password", return_value=False):
            mock_db.is_database_available.return_value = True
            mock_db.get_session = mock_get_session

            resp = auth_client.post(self.ENDPOINT, json={
                "current_password": "wrongold",
                "new_password": "newpassword123",
            })

        assert resp.status_code == 401
        assert "incorrect" in resp.json()["detail"].lower()

    def test_successful_password_change(self, auth_client):
        user = _make_mock_user(role=MagicMock(value="admin"))

        async def mock_execute(stmt):
            return _scalars_returning(user)

        mock_session = AsyncMock()
        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        async def mock_get_session():
            yield mock_session

        with patch("app.routes.auth.auth.database_service") as mock_db, \
             patch("app.routes.auth.auth.verify_password", return_value=True), \
             patch("app.routes.auth.auth.hash_password", return_value="$2b$12$newhash"):
            mock_db.is_database_available.return_value = True
            mock_db.get_session = mock_get_session

            resp = auth_client.post(self.ENDPOINT, json={
                "current_password": "oldpassword123",
                "new_password": "newpassword123",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_db_unavailable(self, auth_client):
        with patch("app.routes.auth.auth.database_service") as mock_db:
            mock_db.is_database_available.return_value = False

            resp = auth_client.post(self.ENDPOINT, json={
                "current_password": "old",
                "new_password": "newpassword123",
            })

        assert resp.status_code == 503

    def test_unauthenticated_rejected(self, unauth_client):
        _reset_rate_limiter()
        resp = unauth_client.post(self.ENDPOINT, json={
            "current_password": "old",
            "new_password": "newpassword123",
        })
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/v1/auth/verify-email
# ═══════════════════════════════════════════════════════════════════════════

class TestVerifyEmail:
    ENDPOINT = "/api/v1/auth/verify-email"

    def test_missing_token(self, client):
        _reset_rate_limiter()
        resp = client.post(self.ENDPOINT, json={"token": ""})
        assert resp.status_code == 400

    def test_invalid_token(self, client):
        _reset_rate_limiter()

        async def mock_execute(stmt):
            return _scalars_returning(None)

        mock_session = AsyncMock()
        mock_session.execute = mock_execute

        async def mock_get_session():
            yield mock_session

        with patch("app.routes.auth.auth.database_service") as mock_db:
            mock_db.is_database_available.return_value = True
            mock_db.get_session = mock_get_session

            resp = client.post(self.ENDPOINT, json={"token": "badtoken"})

        assert resp.status_code == 400
        assert "Invalid verification token" in resp.json()["detail"]

    def test_already_verified(self, client):
        _reset_rate_limiter()
        user = _make_mock_user(is_verified=True, verification_token="tok", verification_token_expires_at=None)

        async def mock_execute(stmt):
            return _scalars_returning(user)

        mock_session = AsyncMock()
        mock_session.execute = mock_execute

        async def mock_get_session():
            yield mock_session

        with patch("app.routes.auth.auth.database_service") as mock_db:
            mock_db.is_database_available.return_value = True
            mock_db.get_session = mock_get_session

            resp = client.post(self.ENDPOINT, json={"token": "tok"})

        assert resp.status_code == 400
        assert "already verified" in resp.json()["detail"].lower()

    def test_successful_verification(self, client):
        _reset_rate_limiter()
        user = _make_mock_user(is_verified=False, verification_token="tok", verification_token_expires_at=None)

        async def mock_execute(stmt):
            return _scalars_returning(user)

        mock_session = AsyncMock()
        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        async def mock_get_session():
            yield mock_session

        with patch("app.routes.auth.auth.database_service") as mock_db:
            mock_db.is_database_available.return_value = True
            mock_db.get_session = mock_get_session

            resp = client.post(self.ENDPOINT, json={"token": "tok"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_db_unavailable(self, client):
        _reset_rate_limiter()

        with patch("app.routes.auth.auth.database_service") as mock_db:
            mock_db.is_database_available.return_value = False

            resp = client.post(self.ENDPOINT, json={"token": "sometoken"})

        assert resp.status_code == 503


# ═══════════════════════════════════════════════════════════════════════════
# Auth enforcement - protected endpoints reject unauthenticated requests
# ═══════════════════════════════════════════════════════════════════════════

class TestAuthEnforcement:
    """Verify that endpoints requiring auth reject unauthenticated requests."""

    def test_profile_get_requires_auth(self, unauth_client):
        _reset_rate_limiter()
        resp = unauth_client.get("/api/v1/auth/profile")
        assert resp.status_code == 401

    def test_profile_put_requires_auth(self, unauth_client):
        _reset_rate_limiter()
        resp = unauth_client.put("/api/v1/auth/profile", json={"full_name": "X"})
        assert resp.status_code == 401

    def test_change_password_requires_auth(self, unauth_client):
        _reset_rate_limiter()
        resp = unauth_client.post("/api/v1/auth/change-password", json={
            "current_password": "old",
            "new_password": "newpassword123",
        })
        assert resp.status_code == 401
