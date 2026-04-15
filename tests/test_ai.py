"""
Tests for AI, text generation, research, and Pollinations routes.

Covers:
- POST /api/v1/text/generate           - general text generation
- POST /api/v1/text/generate/script     - script generation (job)
- POST /api/v1/text/discover/topics     - topic discovery
- POST /api/v1/research/web             - web search
- GET  /api/v1/research/web/engines     - available search engines
- POST /api/v1/research/news            - news research
- GET  /api/v1/research/news/sources    - news sources
- POST /api/v1/pollinations/image/generate - Pollinations image gen
- POST /api/v1/pollinations/text/generate  - Pollinations text gen
- POST /api/v1/pollinations/chat/completions - Pollinations chat
- GET  /api/v1/pollinations/models/text  - list text models
- GET  /api/v1/pollinations/models/image - list image models
- POST /api/v1/ai/script-generation     - AI script generation
- POST /api/v1/ai/scenes-to-video       - scenes to video
- POST /api/v1/ai/news-research         - AI news research
- Input validation and error handling
"""
import pytest
from unittest.mock import AsyncMock, patch

# Auth header used by routes that call get_current_user (text, research, ai).
# The conftest sets API_KEY=test-api-key in env before app import, so this matches.
AUTH = {"X-API-Key": "test-api-key"}


@pytest.fixture(autouse=True)
def _disable_rate_limiting():
    """Disable security middleware rate limiting for all tests in this module."""
    with patch(
        "app.middleware.security.SecurityMiddleware._check_rate_limits",
        return_value=None,
    ):
        yield


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/v1/text/generate  (general text generation)
# ═══════════════════════════════════════════════════════════════════════════

class TestTextGenerate:
    ENDPOINT = "/api/v1/text/generate"

    def test_missing_prompt_returns_422(self, client):
        """Omitting the required 'prompt' field should fail validation."""
        resp = client.post(self.ENDPOINT, json={"style": "creative"}, headers=AUTH)
        assert resp.status_code == 422

    def test_successful_generation(self, client):
        """Successful text generation returns content and metadata."""
        mock_response = {
            "content": "Generated text content here.",
            "choices": []
        }
        with patch(
            "app.routes.text.completions.unified_ai_service.create_chat_completion",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            resp = client.post(self.ENDPOINT, json={
                "prompt": "Write a haiku about testing",
                "style": "creative",
                "temperature": 0.8,
            }, headers=AUTH)

        assert resp.status_code == 200
        data = resp.json()
        assert data["content"] == "Generated text content here."
        assert data["style"] == "creative"
        assert data["word_count"] == 4

    def test_service_error_returns_500(self, client):
        """When the AI service raises, the route returns 500."""
        with patch(
            "app.routes.text.completions.unified_ai_service.create_chat_completion",
            new_callable=AsyncMock,
            side_effect=Exception("AI service down"),
        ):
            resp = client.post(self.ENDPOINT, json={"prompt": "Hello"}, headers=AUTH)

        assert resp.status_code == 500
        assert "Failed to generate text" in resp.json()["detail"]

    def test_default_style_is_general(self, client):
        """When no style is specified, 'general' should be used."""
        mock_response = {"content": "Response text", "choices": []}
        with patch(
            "app.routes.text.completions.unified_ai_service.create_chat_completion",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            resp = client.post(self.ENDPOINT, json={"prompt": "Test prompt"}, headers=AUTH)

        assert resp.status_code == 200
        assert resp.json()["style"] == "general"


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/v1/text/generate/script  (script generation job)
# ═══════════════════════════════════════════════════════════════════════════

class TestTextGenerateScript:
    ENDPOINT = "/api/v1/text/generate/script"

    def test_missing_topic_returns_422(self, client):
        """Topic is required for script generation."""
        resp = client.post(self.ENDPOINT, json={"script_type": "facts"}, headers=AUTH)
        assert resp.status_code == 422

    def test_creates_job(self, client):
        """Valid request should create an async job and return job_id."""
        with patch(
            "app.routes.text.completions.job_queue.add_job",
            new_callable=AsyncMock,
        ) as mock_add:
            resp = client.post(self.ENDPOINT, json={
                "topic": "Quantum computing basics",
                "script_type": "educational",
                "language": "en",
                "max_duration": 30,
            }, headers=AUTH)

        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert mock_add.called

    def test_default_values(self, client):
        """Script generation should accept minimal payload with defaults."""
        with patch(
            "app.routes.text.completions.job_queue.add_job",
            new_callable=AsyncMock,
        ):
            resp = client.post(self.ENDPOINT, json={"topic": "AI"}, headers=AUTH)

        assert resp.status_code == 200
        assert "job_id" in resp.json()


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/v1/text/discover/topics  (topic discovery)
# ═══════════════════════════════════════════════════════════════════════════

class TestTopicDiscovery:
    ENDPOINT = "/api/v1/text/discover/topics"

    def test_missing_keywords_returns_422(self, client):
        """Keywords field is required."""
        resp = client.post(self.ENDPOINT, json={"category": "tech"}, headers=AUTH)
        assert resp.status_code == 422

    def test_successful_discovery(self, client):
        """Valid request returns discovered topics."""
        mock_result = {
            "topics": ["AI trends", "Machine learning", "Neural networks"],
            "search_query": "artificial intelligence",
            "total_found": 3,
        }
        with patch(
            "app.routes.text.completions.topic_discovery_service.discover_topics",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(self.ENDPOINT, json={
                "keywords": "artificial intelligence",
                "max_results": 5,
            }, headers=AUTH)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["topics"]) == 3
        assert data["total_found"] == 3

    def test_service_error_returns_500(self, client):
        """Service failure should return 500."""
        with patch(
            "app.routes.text.completions.topic_discovery_service.discover_topics",
            new_callable=AsyncMock,
            side_effect=Exception("Discovery failed"),
        ):
            resp = client.post(self.ENDPOINT, json={"keywords": "test"}, headers=AUTH)

        assert resp.status_code == 500


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/v1/research/web  (web search)
# ═══════════════════════════════════════════════════════════════════════════

class TestWebSearch:
    ENDPOINT = "/api/v1/research/web"

    def test_missing_query_returns_422(self, client):
        """Query is required."""
        resp = client.post(self.ENDPOINT, json={"engine": "perplexity"}, headers=AUTH)
        assert resp.status_code == 422

    def test_invalid_engine_returns_422(self, client):
        """Engine must be 'perplexity' or 'google'."""
        resp = client.post(self.ENDPOINT, json={
            "query": "test query",
            "engine": "bing",
        }, headers=AUTH)
        assert resp.status_code == 422

    def test_successful_perplexity_search(self, client):
        """Valid perplexity search returns results."""
        mock_synth = {
            "synthesis": "AI is transforming everything.",
            "citations": [
                {"title": "AI News", "url": "https://example.com", "snippet": "Latest AI", "source": "Example"}
            ],
        }
        with patch(
            "app.routes.research.web.news_research_service._search_perplexity_synthesis",
            new_callable=AsyncMock,
            return_value=mock_synth,
            create=True,
        ):
            resp = client.post(self.ENDPOINT, json={
                "query": "artificial intelligence",
                "engine": "perplexity",
                "max_results": 5,
            }, headers=AUTH)

        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "artificial intelligence"
        assert data["engine"] == "perplexity"
        assert isinstance(data["results"], list)
        assert data["total_results"] >= 0

    def test_max_results_validation(self, client):
        """max_results must be between 1 and 50."""
        resp = client.post(self.ENDPOINT, json={
            "query": "test",
            "max_results": 0,
        }, headers=AUTH)
        assert resp.status_code == 422

        resp = client.post(self.ENDPOINT, json={
            "query": "test",
            "max_results": 100,
        }, headers=AUTH)
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════
# GET /api/v1/research/web/engines  (search engines list)
# ═══════════════════════════════════════════════════════════════════════════

class TestSearchEngines:
    ENDPOINT = "/api/v1/research/web/engines"

    def test_returns_engines(self, client):
        """Should return available search engines."""
        resp = client.get(self.ENDPOINT, headers=AUTH)
        assert resp.status_code == 200
        data = resp.json()
        assert "available_engines" in data
        assert "default_engine" in data
        engine_names = [e["name"] for e in data["available_engines"]]
        assert "perplexity" in engine_names
        assert "google" in engine_names


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/v1/research/news  (news research)
# ═══════════════════════════════════════════════════════════════════════════

class TestNewsResearch:
    ENDPOINT = "/api/v1/research/news"

    def test_missing_query_returns_422(self, client):
        """Query is required for news research."""
        resp = client.post(self.ENDPOINT, json={"language": "en"}, headers=AUTH)
        assert resp.status_code == 422

    def test_successful_research(self, client):
        """Valid news research request returns articles."""
        mock_result = {
            "articles": [
                {
                    "title": "Breaking News",
                    "description": "Big things happening",
                    "url": "https://example.com/news",
                    "source": "Example News",
                    "published_at": "2025-01-01T00:00:00Z",
                    "image_url": None,
                    "tags": ["tech"],
                }
            ],
            "total_results": 1,
            "search_query": "technology",
            "search_time": 0.5,
        }
        with patch(
            "app.routes.research.news.news_research_service.research_news",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(self.ENDPOINT, json={
                "query": "technology",
                "max_results": 5,
            }, headers=AUTH)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["articles"]) == 1
        assert data["articles"][0]["title"] == "Breaking News"

    def test_max_results_bounds(self, client):
        """max_results must be within [1, 50]."""
        resp = client.post(self.ENDPOINT, json={
            "query": "test",
            "max_results": 0,
        }, headers=AUTH)
        assert resp.status_code == 422

    def test_service_error_returns_500(self, client):
        """Service error returns 500."""
        with patch(
            "app.routes.research.news.news_research_service.research_news",
            new_callable=AsyncMock,
            side_effect=Exception("Service down"),
        ):
            resp = client.post(self.ENDPOINT, json={"query": "test"}, headers=AUTH)

        assert resp.status_code == 500
        assert "News research failed" in resp.json()["detail"]


# ═══════════════════════════════════════════════════════════════════════════
# GET /api/v1/research/news/sources  (news sources)
# ═══════════════════════════════════════════════════════════════════════════

class TestNewsSources:
    ENDPOINT = "/api/v1/research/news/sources"

    def test_returns_sources(self, client):
        """Should return supported languages and features."""
        resp = client.get(self.ENDPOINT, headers=AUTH)
        assert resp.status_code == 200
        data = resp.json()
        assert "supported_languages" in data
        assert "sort_options" in data
        assert "time_ranges" in data
        assert "features" in data


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# NOTE: TestPollinationsImageGenerate, TestPollinationsTextGenerate,
# TestPollinationsChatCompletions, and TestPollinationsTextModels removed.
# Image generation consolidated to /api/v1/image/images/generate?provider=pollinations
# Text generation consolidated to /api/v1/anyllm/completions?provider=pollinations
# Video generation consolidated to /api/v1/videos/generate?provider=pollinations
# ═══════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════
# GET /api/v1/pollinations/models/image  (image models list)
# ═══════════════════════════════════════════════════════════════════════════

class TestPollinationsImageModels:
    ENDPOINT = "/api/v1/pollinations/models/image"

    def test_returns_models(self, client):
        """Should list available image models."""
        mock_models = [{"id": "flux", "name": "Flux"}]
        with patch(
            "app.routes.pollinations.image.pollinations_service.list_image_models",
            new_callable=AsyncMock,
            return_value=mock_models,
        ):
            resp = client.get(self.ENDPOINT)

        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data

    def test_service_error_returns_500(self, client):
        """Service error returns 500."""
        with patch(
            "app.routes.pollinations.image.pollinations_service.list_image_models",
            new_callable=AsyncMock,
            side_effect=Exception("Service unavailable"),
        ):
            resp = client.get(self.ENDPOINT)

        assert resp.status_code == 500


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/v1/ai/script-generation  (AI script generation)
# ═══════════════════════════════════════════════════════════════════════════

class TestAIScriptGeneration:
    ENDPOINT = "/api/v1/ai/script-generation"

    def test_missing_topic_without_auto_returns_400(self, client):
        """When auto_topic=False and topic is empty, should return 400."""
        with patch(
            "app.routes.ai.script_generation.job_queue.add_job",
            new_callable=AsyncMock,
        ):
            resp = client.post(self.ENDPOINT, json={
                "topic": "",
                "auto_topic": False,
            }, headers=AUTH)

        assert resp.status_code == 400
        assert "Topic is required" in resp.json()["detail"]

    def test_creates_async_job(self, client):
        """Valid request creates a job."""
        with patch(
            "app.routes.ai.script_generation.job_queue.add_job",
            new_callable=AsyncMock,
        ):
            resp = client.post(self.ENDPOINT, json={
                "topic": "History of Rome",
                "script_type": "facts",
                "language": "en",
            }, headers=AUTH)

        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data

    def test_sync_mode(self, client):
        """Sync mode returns the script directly."""
        mock_script = {
            "script": "Rome was founded in 753 BC...",
            "title": "History of Rome",
            "scenes": [],
        }
        with patch(
            "app.routes.ai.script_generation.script_generator.generate_script",
            new_callable=AsyncMock,
            return_value=mock_script,
        ):
            resp = client.post(self.ENDPOINT, json={
                "topic": "History of Rome",
                "sync": True,
            }, headers=AUTH)

        assert resp.status_code == 200
        data = resp.json()
        assert data["script"] == "Rome was founded in 753 BC..."

    def test_auto_topic_discovery(self, client):
        """auto_topic=True should discover a topic and proceed."""
        with patch(
            "app.routes.ai.script_generation.topic_discovery_service.discover_topic",
            new_callable=AsyncMock,
            return_value={"topic": "Trending AI topic"},
        ), patch(
            "app.routes.ai.script_generation.job_queue.add_job",
            new_callable=AsyncMock,
        ):
            resp = client.post(self.ENDPOINT, json={
                "topic": "",
                "auto_topic": True,
            }, headers=AUTH)

        assert resp.status_code == 200
        assert "job_id" in resp.json()


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/v1/ai/scenes-to-video  (scenes to video)
# ═══════════════════════════════════════════════════════════════════════════

class TestScenesToVideo:
    ENDPOINT = "/api/v1/ai/scenes-to-video"

    def test_missing_scenes_returns_422(self, client):
        """Scenes list is required."""
        resp = client.post(self.ENDPOINT, json={"config": {}}, headers=AUTH)
        assert resp.status_code == 422

    def test_empty_scenes_returns_422(self, client):
        """Empty scenes list should fail validation."""
        resp = client.post(self.ENDPOINT, json={"scenes": []}, headers=AUTH)
        assert resp.status_code == 422

    def test_scene_without_text_returns_400(self, client):
        """Scenes with only whitespace text should be rejected."""
        with patch(
            "app.routes.ai.scenes_to_video.job_queue.add_job",
            new_callable=AsyncMock,
        ):
            resp = client.post(self.ENDPOINT, json={
                "scenes": [{"text": "   ", "searchTerms": []}],
            }, headers=AUTH)

        assert resp.status_code == 400
        assert "at least one scene with text" in resp.json()["detail"].lower()

    def test_creates_job(self, client):
        """Valid request creates a video generation job."""
        with patch(
            "app.routes.ai.scenes_to_video.job_queue.add_job",
            new_callable=AsyncMock,
        ):
            resp = client.post(self.ENDPOINT, json={
                "scenes": [
                    {"text": "Welcome to our video", "searchTerms": ["welcome"], "duration": 3.0},
                    {"text": "Here is the main content", "searchTerms": ["content"], "duration": 5.0},
                ],
            }, headers=AUTH)

        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data

    def test_scene_duration_bounds(self, client):
        """Scene duration must be between 1.0 and 30.0."""
        resp = client.post(self.ENDPOINT, json={
            "scenes": [{"text": "Too short", "duration": 0.5}],
        }, headers=AUTH)
        assert resp.status_code == 422

        resp = client.post(self.ENDPOINT, json={
            "scenes": [{"text": "Too long", "duration": 60.0}],
        }, headers=AUTH)
        assert resp.status_code == 422

    def test_default_config(self, client):
        """Request with scenes only should use default config."""
        with patch(
            "app.routes.ai.scenes_to_video.job_queue.add_job",
            new_callable=AsyncMock,
        ):
            resp = client.post(self.ENDPOINT, json={
                "scenes": [{"text": "A simple scene"}],
            }, headers=AUTH)

        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/v1/ai/news-research  (AI news research job)
# ═══════════════════════════════════════════════════════════════════════════

class TestAINewsResearch:
    ENDPOINT = "/api/v1/ai/news-research"

    def test_missing_search_term_returns_422(self, client):
        """searchTerm is required."""
        resp = client.post(self.ENDPOINT, json={"targetLanguage": "en"}, headers=AUTH)
        assert resp.status_code == 422

    def test_creates_job(self, client):
        """Valid request creates a news research job."""
        with patch(
            "app.routes.ai.script_generation.job_queue.add_job",
            new_callable=AsyncMock,
        ):
            resp = client.post(self.ENDPOINT, json={
                "searchTerm": "artificial intelligence",
                "maxResults": 5,
            }, headers=AUTH)

        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data


# ═══════════════════════════════════════════════════════════════════════════
# Auth enforcement - unauthenticated requests
# ═══════════════════════════════════════════════════════════════════════════

class TestAIAuthEnforcement:
    """Endpoints should reject unauthenticated requests."""

    def test_text_generate_requires_auth(self, unauth_client):
        resp = unauth_client.post("/api/v1/text/generate", json={"prompt": "test"})
        assert resp.status_code in (401, 403)

    def test_ai_script_generation_requires_auth(self, unauth_client):
        resp = unauth_client.post(
            "/api/v1/ai/script-generation",
            json={"topic": "test"},
        )
        assert resp.status_code in (401, 403)

    def test_scenes_to_video_requires_auth(self, unauth_client):
        resp = unauth_client.post(
            "/api/v1/ai/scenes-to-video",
            json={"scenes": [{"text": "test"}]},
        )
        assert resp.status_code in (401, 403)
