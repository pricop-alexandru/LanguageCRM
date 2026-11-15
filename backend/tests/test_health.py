from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "LanguageCRM Backend"}


def test_process_command() -> None:
    response = client.post("/api/command", json={"prompt": "Add client John"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["received_prompt"] == "Add client John"
    assert "reply" in payload
