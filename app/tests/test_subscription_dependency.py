import asyncio
from fastapi import FastAPI, Depends, Request
from fastapi.testclient import TestClient
import pytest

from app.utils.subscription import require_active_subscription
from app.utils.auth import get_api_key


def create_test_app():
    app = FastAPI()

    @app.get("/test-require")
    async def test_endpoint(_: bool = Depends(require_active_subscription)):
        return {"ok": True}

    return app


@pytest.fixture
def client(monkeypatch):
    app = create_test_app()

    # Helper to override get_api_key to set request.state.api_key_info
    async def override_get_api_key_admin(request: Request, api_key_header=None):
        request.state.api_key_info = {
            "user_id": "1",
            "user_email": "admin@example.com",
            "user_role": "admin",
        }
        return "env-admin-key"

    async def override_get_api_key_active(request: Request, api_key_header=None):
        request.state.api_key_info = {
            "user_id": "2",
            "user_email": "user-active@example.com",
            "user_role": "user",
        }
        return "env-user-active-key"

    async def override_get_api_key_inactive(request: Request, api_key_header=None):
        request.state.api_key_info = {
            "user_id": "3",
            "user_email": "user-inactive@example.com",
            "user_role": "user",
        }
        return "env-user-inactive-key"

    # We'll swap these overrides inside each test
    app.dependency_overrides.clear()

    client = TestClient(app)
    client._override_get_api_key_admin = override_get_api_key_admin
    client._override_get_api_key_active = override_get_api_key_active
    client._override_get_api_key_inactive = override_get_api_key_inactive

    return client


# Async helper to simulate user_service.get_user
async def _mock_get_user_admin(user_id):
    return {"id": 1, "role": "admin", "subscription_status": None}


async def _mock_get_user_active(user_id):
    return {"id": 2, "role": "user", "subscription_status": "active"}


async def _mock_get_user_inactive(user_id):
    return {"id": 3, "role": "user", "subscription_status": "inactive"}


def test_admin_bypass(monkeypatch, client):
    # Override get_api_key to set api_key_info for an admin
    client.app.dependency_overrides[get_api_key] = client._override_get_api_key_admin

    # Monkeypatch the user_service.get_user used by require_active_subscription
    from app.utils.subscription import user_service

    monkeypatch.setattr(user_service, "get_user", _mock_get_user_admin)

    response = client.get("/test-require")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_env_admin_key_bypass(monkeypatch, client):
    # Simulate environment API key validation returning user_role='admin' and no user_id
    async def override_get_api_key_env_admin(request: Request, api_key_header=None):
        request.state.api_key_info = {
            "user_id": None,
            "user_email": None,
            "user_role": "admin",
        }
        return "env-admin-key"

    client.app.dependency_overrides[get_api_key] = override_get_api_key_env_admin

    response = client.get("/test-require")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_active_subscription(monkeypatch, client):
    client.app.dependency_overrides[get_api_key] = client._override_get_api_key_active

    from app.utils.subscription import user_service
    monkeypatch.setattr(user_service, "get_user", _mock_get_user_active)

    response = client.get("/test-require")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_inactive_subscription(monkeypatch, client):
    client.app.dependency_overrides[get_api_key] = client._override_get_api_key_inactive

    from app.utils.subscription import user_service
    monkeypatch.setattr(user_service, "get_user", _mock_get_user_inactive)

    response = client.get("/test-require")
    assert response.status_code == 402
    assert "Active subscription required" in response.json().get("detail", "")
