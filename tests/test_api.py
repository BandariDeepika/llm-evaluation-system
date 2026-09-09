from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_returns_success() -> None:
    response = client.get("/health")

    assert response.status_code == 200


def test_health_returns_expected_status() -> None:
    response = client.get("/health")

    assert response.json() == {
        "status": "healthy",
        "service": "LLM Evaluation API",
    }


def test_root_returns_success() -> None:
    response = client.get("/")

    assert response.status_code == 200