"""
Shared test fixtures for Griot API tests.

Strategy:
- Override get_api_key dependency to bypass auth
- Mock database service to avoid needing PostgreSQL
- Mock external services (S3, Redis, Pollinations, etc.)
- Test route logic, input validation, and error handling
"""
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Set test environment variables BEFORE importing anything from the app
os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-for-testing")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_griot")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")
os.environ.setdefault("S3_ACCESS_KEY", "test-access-key")
os.environ.setdefault("S3_SECRET_KEY", "test-secret-key")
os.environ.setdefault("S3_REGION", "us-east-1")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-pass")
os.environ.setdefault("DEBUG", "false")

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ── Mock database service before app import ──────────────────────────────────

def _create_mock_database_service():
    """Create a mock database service that doesn't connect to any database."""
    mock_db = MagicMock()
    mock_db.is_database_available = MagicMock(return_value=True)
    mock_db.engine = None
    mock_db.session_factory = None

    async def mock_initialize():
        pass

    async def mock_create_tables():
        pass

    async def mock_update_enums():
        pass

    async def mock_migrate_schema():
        pass

    async def mock_get_session():
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None), all=MagicMock(return_value=[]))),
            fetchall=MagicMock(return_value=[]),
            fetchone=MagicMock(return_value=None),
        ))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        mock_session.refresh = AsyncMock()
        yield mock_session

    mock_db.initialize = mock_initialize
    mock_db.create_tables = mock_create_tables
    mock_db.update_enums = mock_update_enums
    mock_db.migrate_schema = mock_migrate_schema
    mock_db.get_session = mock_get_session
    return mock_db


# Apply database mock before importing app
_mock_db_service = _create_mock_database_service()

# Patch the database service module-level singleton
with patch.dict("sys.modules", {}):
    pass  # Reset if needed

# We need to patch after import, so we'll do it in the fixture


@pytest.fixture(scope="session")
def mock_database_service():
    """Session-scoped mock database service."""
    return _mock_db_service


@pytest.fixture
def client(mock_database_service):
    """
    Create a FastAPI TestClient with mocked dependencies.

    This patches:
    - get_api_key: returns test key without validation
    - database_service: doesn't connect to real DB
    - startup event: skipped to avoid DB initialization
    """
    from unittest.mock import patch, AsyncMock, MagicMock

    # Mock the database service initialization
    with patch("app.database.DatabaseService.initialize", new_callable=AsyncMock), \
         patch("app.database.DatabaseService.create_tables", new_callable=AsyncMock), \
         patch("app.database.DatabaseService.update_enums", new_callable=AsyncMock), \
         patch("app.database.DatabaseService.migrate_schema", new_callable=AsyncMock):

        from fastapi import Request
        from fastapi.testclient import TestClient
        from app.main import app
        from app.utils.auth import get_api_key, get_current_user

        # Disable rate limiting in tests
        if hasattr(app.state, 'limiter'):
            app.state.limiter.enabled = False

        # Override authentication to always succeed
        _test_user_info = {
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

        async def override_get_api_key(request=None, api_key_header=None):
            if request and hasattr(request, 'state'):
                request.state.api_key_info = _test_user_info
            return "test-api-key"

        async def override_get_current_user(request: Request = None):
            if request and hasattr(request, 'state'):
                request.state.api_key_info = _test_user_info
            return _test_user_info

        app.dependency_overrides[get_api_key] = override_get_api_key
        app.dependency_overrides[get_current_user] = override_get_current_user

        with TestClient(
            app,
            raise_server_exceptions=False,
            base_url="http://localhost",
            headers={"Host": "localhost"},
        ) as test_client:
            yield test_client

        # Cleanup
        app.dependency_overrides.clear()


@pytest.fixture
def unauth_client():
    """
    Create a FastAPI TestClient WITHOUT authentication override.
    Useful for testing auth rejection scenarios.
    """
    from unittest.mock import patch, AsyncMock

    with patch("app.database.DatabaseService.initialize", new_callable=AsyncMock), \
         patch("app.database.DatabaseService.create_tables", new_callable=AsyncMock), \
         patch("app.database.DatabaseService.update_enums", new_callable=AsyncMock), \
         patch("app.database.DatabaseService.migrate_schema", new_callable=AsyncMock):

        from fastapi.testclient import TestClient
        from app.main import app

        # Disable rate limiting in tests
        if hasattr(app.state, 'limiter'):
            app.state.limiter.enabled = False

        with TestClient(
            app,
            raise_server_exceptions=False,
            base_url="http://localhost",
            headers={"Host": "localhost"},
        ) as test_client:
            yield test_client


@pytest.fixture
def api_key():
    """Return the test API key."""
    return "test-api-key"


@pytest.fixture
def auth_headers(api_key):
    """Return headers with API key for authenticated requests."""
    return {"X-API-Key": api_key}


# ── Helper fixtures for common test patterns ─────────────────────────────────

@pytest.fixture
def mock_job_queue():
    """Mock the job queue service."""
    with patch("app.services.job_queue.job_queue.job_queue") as mock_jq:
        mock_jq.add_job = AsyncMock(return_value="test-job-id")
        mock_jq.get_job = AsyncMock(return_value=None)
        mock_jq.get_job_status = AsyncMock(return_value=None)
        yield mock_jq


@pytest.fixture
def mock_s3():
    """Mock the S3 service."""
    with patch("app.services.s3.s3.s3_service") as mock_s3:
        mock_s3.upload_file = AsyncMock(return_value="https://s3.example.com/test-file.mp4")
        mock_s3.download_file = AsyncMock(return_value=b"test-content")
        mock_s3.get_presigned_url = AsyncMock(return_value="https://s3.example.com/presigned")
        mock_s3.delete_file = AsyncMock(return_value=True)
        yield mock_s3


@pytest.fixture
def mock_redis():
    """Mock the Redis service."""
    with patch("app.services.redis.redis_service.redis_service") as mock_redis:
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=True)
        mock_redis.exists = AsyncMock(return_value=False)
        yield mock_redis
