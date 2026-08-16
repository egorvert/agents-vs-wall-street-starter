from uuid import UUID

from fastapi.testclient import TestClient

from app.repositories.sqlite import SQLiteRepository


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_demo_persists_record(client: TestClient, repository: SQLiteRepository) -> None:
    response = client.post("/api/demo", json={"input": "hello"})

    assert response.status_code == 201
    body = response.json()
    assert body["input"] == "hello"
    assert body["status"] == "created"
    assert body["timestamp"].endswith("Z") or body["timestamp"].endswith("+00:00")

    saved = repository.get_demo(UUID(body["id"]))
    assert saved is not None
    assert saved.input == "hello"


def test_demo_rejects_empty_input(client: TestClient) -> None:
    response = client.post("/api/demo", json={"input": ""})

    assert response.status_code == 422
