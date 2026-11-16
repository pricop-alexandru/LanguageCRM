from collections.abc import Iterator

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import database
from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def test_new_client_is_created(client: TestClient) -> None:
    response = client.post(
        "/api/clients/resolve",
        json={"name": "Ion Popescu", "phone": "07 22-123-456"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Ion Popescu",
        "email": None,
        "phone": "+40722123456",
        "created": True,
    }


@pytest.mark.parametrize(
    "lookup",
    [
        {"name": "ION POPESCU"},
        {"phone": "+40 (722) 123456"},
    ],
)
def test_existing_client_is_reused(
    client: TestClient, lookup: dict[str, str]
) -> None:
    created = client.post(
        "/api/clients/resolve",
        json={"name": "Ion Popescu", "phone": "0722123456"},
    )
    reused = client.post("/api/clients/resolve", json=lookup)

    assert created.status_code == 200
    assert reused.status_code == 200
    assert reused.json()["id"] == created.json()["id"]
    assert reused.json()["created"] is False
    assert reused.json()["phone"] == "+40722123456"


def test_name_match_fills_missing_phone(client: TestClient) -> None:
    first = client.post(
        "/api/clients/resolve", json={"name": "\u0218tefan Ionescu"}
    )
    resolved = client.post(
        "/api/clients/resolve",
        json={"name": "Stefan Ionescu", "phone": "+40733111222"},
    )

    assert first.status_code == 200
    assert resolved.json()["id"] == first.json()["id"]
    assert resolved.json()["created"] is False
    assert resolved.json()["phone"] == "+40733111222"


def test_conflicting_name_and_phone_are_rejected(client: TestClient) -> None:
    client.post("/api/clients/resolve", json={"name": "Ion Popescu"})
    other = client.post(
        "/api/clients/resolve",
        json={"name": "Maria Ionescu", "phone": "+40722123456"},
    )

    conflict = client.post(
        "/api/clients/resolve",
        json={"name": "Ion Popescu", "phone": "+40722123456"},
    )

    assert other.status_code == 200
    assert conflict.status_code == 409


def test_phone_only_lookup_does_not_create_unknown_client(client: TestClient) -> None:
    response = client.post("/api/clients/resolve", json={"phone": "+40722123456"})

    assert response.status_code == 404


def test_resolution_requires_at_least_one_identifier(client: TestClient) -> None:
    response = client.post("/api/clients/resolve", json={})

    assert response.status_code == 422


def test_invalid_phone_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/clients/resolve",
        json={"name": "Ion Popescu", "phone": "call 0722123456"},
    )

    assert response.status_code == 422


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
