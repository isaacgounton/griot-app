import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient
import os

import pytest

from app.routes.auth import router as auth_router
from app.database import database_service, UserRole


class FakeUser:
    def __init__(self):
        self.id = 42
        self.username = "testuser"
        self.email = "testuser@example.com"
        self.hashed_password = "hashed"
        self.is_verified = True
        self.is_active = True
        self.role = UserRole.USER


class FakeResult:
    def __init__(self, user):
        self._user = user

    def scalars(self):
        return self

    def first(self):
        return self._user


class FakeSession:
    def __init__(self, user):
        self._user = user

    async def execute(self, *args, **kwargs):
        return FakeResult(self._user)

    async def commit(self):
        return None

    async def refresh(self, *args, **kwargs):
        return None


async def _fake_get_session(user=None):
    session = FakeSession(user or FakeUser())
    yield session


def create_test_app():
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")

    return app


@pytest.fixture
def client(monkeypatch):
    app = create_test_app()

    # Mock database availability and session generator
    monkeypatch.setattr(database_service, "is_database_available", lambda: True)
    monkeypatch.setattr(database_service, "get_session", lambda: _fake_get_session(FakeUser()))

    # Patch verify_password to always return True inside the auth module (auth imported earlier)
    import importlib
    auth_mod = importlib.import_module("app.routes.auth.auth")
    monkeypatch.setattr(auth_mod, "verify_password", lambda pw, h: True)

    # Capture create_api_key calls
    from app.services.api_key import api_key_service as api_key_svc

    created_data = {}

    async def fake_create_api_key(key_data, requester_info=None):
        created_data["api_key_data"] = key_data
        # Return a fake API key
        return {"key": "oui_sk_test_key"}

    monkeypatch.setattr(api_key_svc, "create_api_key", fake_create_api_key)

    client = TestClient(app)
    client._created_data = created_data
    return client


def test_login_returns_unmasked_api_key_with_expiry(monkeypatch, client):
    # Ensure expiry days env var is set
    monkeypatch.setenv("WEB_LOGIN_KEY_EXPIRY_DAYS", "7")

    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "test-password"}
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data.get("api_key") == "oui_sk_test_key"

    # Check that create_api_key received an expires_at set approx 7 days forward
    api_key_data = client._created_data.get("api_key_data")
    assert api_key_data is not None
    expires_at = api_key_data.get("expires_at")
    assert expires_at is not None

    # expires_at should be a datetime - when passed across, ensure it's within ~2 seconds of now + 7 days
    expected = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    delta = abs((expires_at - expected).total_seconds())
    assert delta < 5
