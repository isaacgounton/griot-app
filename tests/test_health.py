"""
Tests for health check and root endpoints.
These are the simplest tests to verify the test infrastructure works.
"""


def test_health_check(client):
    """Health endpoint should return 200 with status healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "griot"


def test_root_endpoint(client):
    """Root endpoint should return 200."""
    response = client.get("/")
    assert response.status_code == 200
