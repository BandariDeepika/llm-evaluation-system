from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_evaluate_endpoint_returns_structured_result() -> None:
    response = client.post(
        "/evaluate",
        json={
            "question": "What is the capital of France?",
            "response": "Paris is the capital of France.",
            "source_document": "Paris is the capital of France.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "What is the capital of France?"
    assert body["factuality"]["score"] == 10
    assert "overall_score" in body


def test_evaluate_endpoint_rejects_missing_required_fields() -> None:
    response = client.post("/evaluate", json={"question": "A question"})

    assert response.status_code == 422


def test_evaluate_endpoint_preserves_existing_system_routes() -> None:
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200