from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app import database
from app.database import Client
from app.main import app

ION = {"name": "Ion Popescu", "phone": "07 22-123-456", "email": "Ion@Exemplu.ro"}


@pytest.fixture
def client() -> TestClient:
    """Test client; the in-memory database comes from the autouse fixture in conftest.py."""
    return TestClient(app)


def test_new_client_is_created(client: TestClient) -> None:
    response = client.post("/api/clients/resolve", json=ION)

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Ion Popescu",
        "email": "ion@exemplu.ro",
        "phone": "+40722123456",
        "created": True,
    }


@pytest.mark.parametrize(
    "missing",
    [
        {"name": "Ion Popescu"},
        {"name": "Ion Popescu", "phone": "0722123456"},
        {"name": "Ion Popescu", "email": "ion@exemplu.ro"},
    ],
)
def test_new_client_requires_name_phone_and_email(
    client: TestClient, missing: dict[str, str]
) -> None:
    response = client.post("/api/clients/resolve", json=missing)

    assert response.status_code == 422
    assert client.get("/api/clients").json() == []


@pytest.mark.parametrize(
    "lookup",
    [
        {"name": "ION POPESCU"},
        {"phone": "+40 (722) 123456"},
        {"email": "ion@EXEMPLU.ro"},
    ],
)
def test_existing_client_is_reused(
    client: TestClient, lookup: dict[str, str]
) -> None:
    created = client.post("/api/clients/resolve", json=ION)
    reused = client.post("/api/clients/resolve", json=lookup)

    assert created.status_code == 200
    assert reused.status_code == 200
    assert reused.json()["id"] == created.json()["id"]
    assert reused.json()["created"] is False
    assert reused.json()["phone"] == "+40722123456"


def test_name_match_fills_missing_phone_and_email(
    client: TestClient, test_sessionmaker: sessionmaker[Session]
) -> None:
    # A client stored before phone/email were mandatory.
    with test_sessionmaker() as db:
        db.add(Client(name="\u0218tefan Ionescu", normalized_name="stefan ionescu"))
        db.commit()

    resolved = client.post(
        "/api/clients/resolve",
        json={"name": "Stefan Ionescu", "phone": "+40733111222", "email": "stefan@exemplu.ro"},
    )

    assert resolved.status_code == 200
    assert resolved.json() == {
        "id": 1,
        "name": "\u0218tefan Ionescu",
        "email": "stefan@exemplu.ro",
        "phone": "+40733111222",
        "created": False,
    }


@pytest.mark.parametrize(
    "conflict",
    [
        {"name": "Ion Popescu", "phone": "+40733111222"},
        {"name": "Ion Popescu", "email": "maria@exemplu.ro"},
        {"phone": "0722123456", "email": "maria@exemplu.ro"},
    ],
)
def test_identifiers_of_different_clients_are_rejected(
    client: TestClient, conflict: dict[str, str]
) -> None:
    client.post("/api/clients/resolve", json=ION)
    other = client.post(
        "/api/clients/resolve",
        json={"name": "Maria Ionescu", "phone": "+40733111222", "email": "maria@exemplu.ro"},
    )

    response = client.post("/api/clients/resolve", json=conflict)

    assert other.status_code == 200
    assert response.status_code == 409


@pytest.mark.parametrize(
    "lookup", [{"phone": "+40722123456"}, {"email": "nobody@exemplu.ro"}]
)
def test_lookup_without_name_does_not_create_unknown_client(
    client: TestClient, lookup: dict[str, str]
) -> None:
    response = client.post("/api/clients/resolve", json=lookup)

    assert response.status_code == 404


def test_resolution_requires_at_least_one_identifier(client: TestClient) -> None:
    response = client.post("/api/clients/resolve", json={})

    assert response.status_code == 422


@pytest.mark.parametrize(
    "invalid",
    [
        {**ION, "phone": "call 0722123456"},
        {**ION, "email": "ion@"},
        {**ION, "email": "ion popescu@exemplu.ro"},
    ],
)
def test_invalid_contact_details_are_rejected(
    client: TestClient, invalid: dict[str, str]
) -> None:
    response = client.post("/api/clients/resolve", json=invalid)

    assert response.status_code == 422


def test_clients_are_listed_newest_first(client: TestClient) -> None:
    client.post("/api/clients/resolve", json=ION)
    client.post(
        "/api/clients/resolve",
        json={"name": "Maria Ionescu", "phone": "0733111222", "email": "maria@exemplu.ro"},
    )

    response = client.get("/api/clients")

    assert response.status_code == 200
    assert [c["name"] for c in response.json()] == ["Maria Ionescu", "Ion Popescu"]
    assert response.json()[1] == {
        "id": 1,
        "name": "Ion Popescu",
        "email": "ion@exemplu.ro",
        "phone": "+40722123456",
    }


def test_init_db_adds_client_identity_columns_to_existing_database(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE clients "
                "(id INTEGER PRIMARY KEY, name VARCHAR, email VARCHAR)"
            )
        )
        connection.execute(
            text("INSERT INTO clients (id, name) VALUES (1, :name)"),
            {"name": "\u0218tefan Ionescu"},
        )
    monkeypatch.setattr(database, "engine", engine)

    database.init_db()

    with engine.connect() as connection:
        client = connection.execute(
            text("SELECT phone, normalized_name FROM clients WHERE id = 1")
        ).one()
    assert client == (None, "stefan ionescu")
    engine.dispose()
