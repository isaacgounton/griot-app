"""
Tests for agent-related API endpoints.

Covers:
- GET  /api/v1/agents/           - list agents
- GET  /api/v1/agents/{type}     - get agent details
- POST /api/v1/agents/sessions   - create session
- GET  /api/v1/agents/sessions   - list sessions
- GET  /api/v1/agents/knowledge-bases - list knowledge bases
- GET  /api/v1/agents/users/preferences - get user preferences
- PUT  /api/v1/agents/users/preferences - update preferences
"""
from unittest.mock import AsyncMock, MagicMock, patch

PREFIX = "/api/v1/agents"


# ── List agents ────────────────────────────────────────────────────────────

class TestListAgents:
    """Tests for GET /api/v1/agents/."""

    @patch("app.routes.agents.agents.agent_service")
    def test_list_agents_success(self, mock_svc, client, auth_headers):
        """Should return list of available agents."""
        mock_svc.get_available_agents = AsyncMock(return_value=[
            {"type": "research", "name": "Research Agent", "description": "Research topics"},
            {"type": "writer", "name": "Writer Agent", "description": "Write content"},
        ])
        response = client.get(f"{PREFIX}/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["type"] == "research"

    @patch("app.routes.agents.agents.agent_service")
    def test_list_agents_empty(self, mock_svc, client, auth_headers):
        """Should return empty list when no agents configured."""
        mock_svc.get_available_agents = AsyncMock(return_value=[])
        response = client.get(f"{PREFIX}/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    @patch("app.routes.agents.agents.agent_service")
    def test_list_agents_service_error(self, mock_svc, client, auth_headers):
        """Should return 500 when agent service fails."""
        mock_svc.get_available_agents = AsyncMock(side_effect=Exception("Service down"))
        response = client.get(f"{PREFIX}/", headers=auth_headers)
        assert response.status_code == 500


# ── Get agent details ──────────────────────────────────────────────────────

class TestGetAgentDetails:
    """Tests for GET /api/v1/agents/{agent_type}."""

    @patch("app.routes.agents.agents.agent_service")
    def test_get_agent_details_success(self, mock_svc, client, auth_headers):
        """Should return agent details for valid type."""
        mock_svc.get_agent_details = AsyncMock(return_value={
            "type": "research",
            "name": "Research Agent",
            "models": ["gpt-5-mini"],
        })
        response = client.get(f"{PREFIX}/research", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "research"

    @patch("app.routes.agents.agents.agent_service")
    def test_get_agent_details_not_found(self, mock_svc, client, auth_headers):
        """Should return 404 for unknown agent type."""
        mock_svc.get_agent_details = AsyncMock(return_value=None)
        response = client.get(f"{PREFIX}/nonexistent", headers=auth_headers)
        assert response.status_code == 404


# ── Sessions ───────────────────────────────────────────────────────────────

class TestCreateSession:
    """Tests for POST /api/v1/agents/sessions."""

    @patch("app.routes.agents.sessions.agent_service")
    def test_create_session_success(self, mock_svc, client, auth_headers):
        """Should create a new session and return session info."""
        mock_svc.create_session = AsyncMock(return_value={
            "session_id": "sess-123",
            "agent_type": "research",
            "user_id": "1",
            "model_id": "gpt-5-mini",
            "provider": "openai",
            "created_at": "2026-01-01T00:00:00Z",
            "status": "active",
            "title": None,
            "description": None,
            "updated_at": None,
            "metadata": None,
            "settings": None,
        })
        response = client.post(
            f"{PREFIX}/sessions",
            json={"agent_type": "research", "model_id": "gpt-5-mini"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "sess-123"
        assert data["agent_type"] == "research"

    def test_create_session_missing_agent_type(self, client, auth_headers):
        """Should reject request without agent_type."""
        response = client.post(
            f"{PREFIX}/sessions",
            json={"model_id": "gpt-5-mini"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @patch("app.routes.agents.sessions.agent_service")
    def test_create_session_invalid_agent(self, mock_svc, client, auth_headers):
        """Should return 400 when agent type is invalid."""
        mock_svc.create_session = AsyncMock(side_effect=ValueError("Unknown agent type"))
        response = client.post(
            f"{PREFIX}/sessions",
            json={"agent_type": "invalid_agent"},
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestListSessions:
    """Tests for GET /api/v1/agents/sessions."""

    @patch("app.routes.agents.sessions.agent_service")
    def test_list_sessions_success(self, mock_svc, client, auth_headers):
        """Should return list of user sessions."""
        mock_svc.get_user_sessions = AsyncMock(return_value=[
            {"session_id": "sess-1", "agent_type": "research", "status": "active"},
            {"session_id": "sess-2", "agent_type": "writer", "status": "active"},
        ])
        response = client.get(f"{PREFIX}/sessions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) == 2

    @patch("app.routes.agents.sessions.agent_service")
    def test_list_sessions_empty(self, mock_svc, client, auth_headers):
        """Should return empty list when no sessions."""
        mock_svc.get_user_sessions = AsyncMock(return_value=[])
        response = client.get(f"{PREFIX}/sessions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["sessions"] == []


class TestDeleteSession:
    """Tests for DELETE /api/v1/agents/sessions/{session_id}."""

    @patch("app.routes.agents.sessions.agent_service")
    def test_delete_session_success(self, mock_svc, client, auth_headers):
        """Should delete session and return success message."""
        mock_svc.delete_session = AsyncMock(return_value=True)
        response = client.delete(f"{PREFIX}/sessions/sess-123", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"].lower() or "sess-123" in data["message"]

    @patch("app.routes.agents.sessions.agent_service")
    def test_delete_session_not_found(self, mock_svc, client, auth_headers):
        """Should return 404 when session does not exist."""
        mock_svc.delete_session = AsyncMock(return_value=False)
        response = client.delete(f"{PREFIX}/sessions/nonexistent", headers=auth_headers)
        assert response.status_code == 404


class TestSessionHistory:
    """Tests for GET /api/v1/agents/sessions/{session_id}/history."""

    @patch("app.routes.agents.sessions.agent_service")
    def test_get_history_success(self, mock_svc, client, auth_headers):
        """Should return session message history."""
        mock_svc.get_session_history = AsyncMock(return_value=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ])
        response = client.get(f"{PREFIX}/sessions/sess-123/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "sess-123"
        assert len(data["messages"]) == 2

    @patch("app.routes.agents.sessions.agent_service")
    def test_get_history_not_found(self, mock_svc, client, auth_headers):
        """Should return 404 when session not found."""
        mock_svc.get_session_history = AsyncMock(side_effect=ValueError("Session not found"))
        response = client.get(f"{PREFIX}/sessions/nonexistent/history", headers=auth_headers)
        assert response.status_code == 404


# ── Knowledge Bases ────────────────────────────────────────────────────────

class TestKnowledgeBases:
    """Tests for /api/v1/agents/knowledge-bases endpoints."""

    @patch("app.routes.agents.knowledge.knowledge_base_service")
    def test_list_knowledge_bases(self, mock_svc, client, auth_headers):
        """Should return list of knowledge bases."""
        mock_svc.list_knowledge_bases = AsyncMock(return_value=[
            {"id": "kb-1", "name": "My KB", "description": "Test"},
        ])
        response = client.get(f"{PREFIX}/knowledge-bases", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "knowledge_bases" in data
        assert len(data["knowledge_bases"]) == 1

    @patch("app.routes.agents.knowledge.knowledge_base_service")
    def test_list_knowledge_bases_empty(self, mock_svc, client, auth_headers):
        """Should return empty list when no knowledge bases."""
        mock_svc.list_knowledge_bases = AsyncMock(return_value=[])
        response = client.get(f"{PREFIX}/knowledge-bases", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["knowledge_bases"] == []

    @patch("app.routes.agents.knowledge.knowledge_base_service")
    def test_create_knowledge_base(self, mock_svc, client, auth_headers):
        """Should create a knowledge base and return 201."""
        mock_svc.create_knowledge_base = AsyncMock(return_value={
            "id": "kb-new",
            "name": "New KB",
            "description": "Created via test",
        })
        response = client.post(
            f"{PREFIX}/knowledge-bases",
            json={"name": "New KB", "description": "Created via test"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New KB"

    def test_create_knowledge_base_missing_name(self, client, auth_headers):
        """Should reject knowledge base creation without name."""
        response = client.post(
            f"{PREFIX}/knowledge-bases",
            json={"description": "No name provided"},
            headers=auth_headers,
        )
        assert response.status_code == 422


# ── Preferences ────────────────────────────────────────────────────────────

class TestPreferences:
    """Tests for /api/v1/agents/users/preferences endpoints."""

    @patch("app.routes.agents.preferences.agent_preferences_service")
    def test_get_preferences(self, mock_svc, client, auth_headers):
        """Should return user preferences."""
        mock_svc.get_preferences = AsyncMock(return_value={
            "theme": "dark",
            "language": "en",
            "default_model": "gpt-5-mini",
        })
        response = client.get(f"{PREFIX}/users/preferences", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "theme" in data

    @patch("app.routes.agents.preferences.agent_preferences_service")
    def test_update_preferences(self, mock_svc, client, auth_headers):
        """Should update and return new preferences."""
        mock_svc.update_preferences = AsyncMock(return_value={
            "theme": "light",
            "language": "fr",
        })
        response = client.put(
            f"{PREFIX}/users/preferences",
            json={"preferences": {"theme": "light", "language": "fr"}},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_update_preferences_missing_body(self, client, auth_headers):
        """Should reject update without preferences field."""
        response = client.put(
            f"{PREFIX}/users/preferences",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @patch("app.routes.agents.preferences.agent_preferences_service")
    def test_update_preferences_invalid_values(self, mock_svc, client, auth_headers):
        """Should return 400 for invalid preference values."""
        mock_svc.update_preferences = AsyncMock(side_effect=ValueError("Invalid preference"))
        response = client.put(
            f"{PREFIX}/users/preferences",
            json={"preferences": {"invalid_key": "bad_value"}},
            headers=auth_headers,
        )
        assert response.status_code == 400


# ── Authentication ─────────────────────────────────────────────────────────

class TestAgentsAuth:
    """Test that agent endpoints require authentication."""

    def test_list_agents_no_auth(self, unauth_client):
        """Should reject unauthenticated request to list agents."""
        response = unauth_client.get(f"{PREFIX}/")
        # Should fail with 401 or 403
        assert response.status_code in (401, 403)

    def test_list_sessions_no_auth(self, unauth_client):
        """Should reject unauthenticated request to list sessions."""
        response = unauth_client.get(f"{PREFIX}/sessions")
        assert response.status_code in (401, 403)
