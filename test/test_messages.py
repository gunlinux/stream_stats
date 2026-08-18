from fastapi.testclient import TestClient

from src.main import app


def _message_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "body": "Hello world",
        "source": 0,
        "message_id": "ext-msg-1",
        "author_id": "user-123",
        "stream_id": "stream-456",
        "channel_id": "channel-789",
    }
    data.update(overrides)
    return data


def _create_message(client: TestClient, **overrides: object) -> dict[str, object]:
    response = client.post("/api/v1/messages", json=_message_data(**overrides))
    assert response.status_code == 201
    return response.json()


def test_messages_require_bearer_token():
    """Requests without a valid bearer token are rejected with 401"""
    with TestClient(app) as anon:
        missing = anon.get("/api/v1/messages")
        assert missing.status_code == 401
        assert missing.headers["WWW-Authenticate"] == "Bearer"

        assert anon.post("/api/v1/messages", json=_message_data()).status_code == 401
        assert (
            anon.get(
                "/api/v1/messages", headers={"Authorization": "Bearer wrong-token"}
            ).status_code
            == 401
        )


def test_create_message(client: TestClient):
    """Test creating a new message"""
    message_data = _message_data()

    response = client.post("/api/v1/messages", json=message_data)
    assert response.status_code == 201

    data = response.json()
    assert data["body"] == message_data["body"]
    assert data["source"] == message_data["source"]
    assert data["message_id"] == message_data["message_id"]
    assert data["author_id"] == message_data["author_id"]
    assert data["stream_id"] == message_data["stream_id"]
    assert data["channel_id"] == message_data["channel_id"]
    assert "id" in data
    assert "created_at" in data


def test_create_message_idempotent(client: TestClient):
    """Posting the same (source, message_id) twice returns the same row"""
    message_data = _message_data()

    first = client.post("/api/v1/messages", json=message_data)
    second = client.post("/api/v1/messages", json=message_data)

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]


def test_create_message_rejects_invalid_source(client: TestClient):
    """Source outside {0, 1} is rejected by validation"""
    response = client.post("/api/v1/messages", json=_message_data(source=2))
    assert response.status_code == 422


def test_get_messages(client: TestClient):
    """Test listing messages: the created message is returned, newest first"""
    created = _create_message(client)

    response = client.get("/api/v1/messages")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == created["id"]


def test_get_messages_pagination(client: TestClient):
    """Test the limit/offset pagination parameters"""
    _create_message(client, message_id="ext-msg-1")
    _create_message(client, message_id="ext-msg-2")

    response = client.get("/api/v1/messages", params={"limit": 1, "offset": 0})
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.get("/api/v1/messages", params={"limit": 1, "offset": 1})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_message(client: TestClient):
    """Test fetching a message by ID"""
    created = _create_message(client)

    response = client.get(f"/api/v1/messages/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_message_not_found(client: TestClient):
    """Test fetching a missing message returns 404"""
    response = client.get("/api/v1/messages/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_delete_message(client: TestClient):
    """Test deleting a message by ID"""
    created = _create_message(client)

    response = client.delete(f"/api/v1/messages/{created['id']}")
    assert response.status_code == 204

    assert client.get(f"/api/v1/messages/{created['id']}").status_code == 404


def test_delete_message_not_found(client: TestClient):
    """Test deleting a missing message returns 404"""
    response = client.delete("/api/v1/messages/999999")
    assert response.status_code == 404
