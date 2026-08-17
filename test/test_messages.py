from fastapi.testclient import TestClient


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


def test_get_messages(client: TestClient):
    """Test getting all messages"""
    response = client.get("/api/v1/messages")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
