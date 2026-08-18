from fastapi.testclient import TestClient

from src.main import app


def test_health_check(client: TestClient):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "timestamp" in data


def test_health_check_unauthenticated():
    """The health endpoint is intentionally left open for liveness probes"""
    with TestClient(app) as anon:
        response = anon.get("/health")
        assert response.status_code == 200
