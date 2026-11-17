"""Tests for creating clients from chat messages (US-05)."""

from typing import Any
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.conversation import ConversationStore, get_conversation_store
from app.database import Client as DBClient
from app.dialogue import MAX_CLARIFICATION_ATTEMPTS
from app.main import app
from app.nlp.contact import extract_email, extract_phone, mask_contact_details
from app.nlp.fallback import fallback_parse_message
from app.nlp.parser import build_decider_payload, parse_message

client = TestClient(app)

ION_RECORD = {
    "id": 1,
    "name": "Ion Popescu",
    "phone": "+40722123456",
    "email": "ion@exemplu.ro",
}


@pytest.fixture(autouse=True)
def isolated_store(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Give each test a fresh conversation store and keep the parser deterministic."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    store = ConversationStore(ttl_seconds=900)
    app.dependency_overrides[get_conversation_store] = lambda: store
    yield store
    app.dependency_overrides.pop(get_conversation_store, None)


def send(prompt: str, conversation_id: str | None = None, locale: str = "ro") -> dict[str, Any]:
    body: dict[str, Any] = {"prompt": prompt, "locale": locale}
    if conversation_id is not None:
        body["conversation_id"] = conversation_id
    response = client.post("/api/command", json=body)
    assert response.status_code == 200
    return response.json()


def stored_clients(session_factory: sessionmaker[Session]) -> list[tuple[str, str, str]]:
    with session_factory() as db:
        return [(c.name, c.phone, c.email) for c in db.query(DBClient).order_by(DBClient.id)]


# --- Contact extraction -------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("telefon 0722 123 456", "+40722123456"),
        ("tel: 0722-123-456.", "+40722123456"),
        ("+40 733 111 222", "+40733111222"),
        ("0040.722.123.456", "+40722123456"),
        ("(0722) 123 456", "+40722123456"),
        ("0722123456, ion@exemplu.ro", "+40722123456"),
    ],
)
def test_extract_phone_accepts_common_formats(text: str, expected: str) -> None:
    assert extract_phone(text) == (expected, None)


@pytest.mark.parametrize(
    ("text", "invalid"),
    [("telefon 0722 12", "0722 12"), ("nr +40 7", None)],
)
def test_extract_phone_reports_invalid_numbers(text: str, invalid: str | None) -> None:
    phone, raw = extract_phone(text)
    assert phone is None
    if invalid is not None:
        assert raw == invalid


@pytest.mark.parametrize("text", ["vreau 5 laptopuri", "100 de suruburi", "comanda 2024"])
def test_quantities_are_not_phone_numbers(text: str) -> None:
    assert extract_phone(text) == (None, None)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("email Ion@Exemplu.ro.", ("ion@exemplu.ro", None)),
        ("<ana.maria+crm@firma-mea.co.uk>", ("ana.maria+crm@firma-mea.co.uk", None)),
        ("emailul este ion@", (None, "ion@")),
        ("ion@exemplu", (None, "ion@exemplu")),
        ("fara email", (None, None)),
    ],
)
def test_extract_email(text: str, expected: tuple[str | None, str | None]) -> None:
    assert extract_email(text) == expected


def test_mask_contact_details_hides_phone_and_email() -> None:
    masked = mask_contact_details("Adaugă clientul Ion Popescu, 0722 123 456, ion@exemplu.ro")
    assert masked == "Adaugă clientul Ion Popescu, [phone], [email]"


# --- Parsing ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("prompt", "entities"),
    [
        (
            "Adaugă clientul Ion Popescu, telefon 0722 123 456, email Ion@Exemplu.ro.",
            ("Ion Popescu", "+40722123456", "ion@exemplu.ro"),
        ),
        (
            "adauga clientul ion popescu cu telefonul 0722123456 si emailul ion@exemplu.ro",
            ("Ion Popescu", "+40722123456", "ion@exemplu.ro"),
        ),
        ("Client nou: Maria Ionescu, 0733 111 222", ("Maria Ionescu", "+40733111222", None)),
        (
            "Add a new client named John Doe, phone +40 744 111 222, john@example.com",
            ("John Doe", "+40744111222", "john@example.com"),
        ),
        ("register customer jane smith", ("Jane Smith", None, None)),
        ("Adaugă un client nou", (None, None, None)),
    ],
)
def test_add_client_intent_and_entities(
    prompt: str, entities: tuple[str | None, str | None, str | None]
) -> None:
    parsed = fallback_parse_message(prompt)
    assert parsed.intent == "add_client"
    assert (parsed.entities.client, parsed.entities.phone, parsed.entities.email) == entities


def test_phone_digits_are_not_order_quantities() -> None:
    parsed = fallback_parse_message("Vreau să comand laptopuri, tel 0722123456")
    assert parsed.intent == "order"
    assert parsed.entities.quantity is None
    assert parsed.entities.product == "laptopuri"


def test_adding_an_order_is_not_adding_a_client() -> None:
    assert fallback_parse_message("Adaugă o comandă de 3 laptopuri").intent == "order"


def test_decider_payload_masks_contact_details() -> None:
    payload = build_decider_payload("Comandă pentru Ion, 0722 123 456, ion@exemplu.ro", "m")
    assert "0722" not in payload["state"]
    assert "ion@exemplu.ro" not in payload["state"]
    assert "[phone]" in payload["state"] and "[email]" in payload["state"]
    assert "add_client" in payload["questions"]["intent"]["criteria"]


def test_add_client_message_is_never_sent_to_openrouter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    with patch("app.nlp.parser.httpx.Client") as mock_client_cls:
        parsed = parse_message("Adaugă clientul Ion Popescu, 0722 123 456, ion@exemplu.ro")
    mock_client_cls.assert_not_called()
    assert parsed.intent == "add_client"
    assert parsed.entities.phone == "+40722123456"


def test_openrouter_add_client_intent_uses_masked_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "answers": {
            "intent": {"choice": "add_client", "confidence": 0.95},
            "is_ambiguous": {"noul": 0.01},
        }
    }
    prompt = "Te rog să-l înregistrezi pe Ion Popescu, 0722 123 456, ion@exemplu.ro"
    with patch("app.nlp.parser.httpx.Client") as mock_client_cls:
        post = mock_client_cls.return_value.__enter__.return_value.post
        post.return_value = response
        parsed = parse_message(prompt)

    sent_state = post.call_args.kwargs["json"]["state"]
    assert "0722" not in sent_state and "ion@exemplu.ro" not in sent_state
    assert parsed.intent == "add_client"
    assert (parsed.entities.phone, parsed.entities.email) == ("+40722123456", "ion@exemplu.ro")


# --- Dialogue & persistence ---------------------------------------------------


def test_complete_message_creates_client(test_sessionmaker: sessionmaker[Session]) -> None:
    res = send("Adaugă clientul Ion Popescu, telefon 0722 123 456, email Ion@Exemplu.ro")

    assert res["intent"] == "add_client"
    assert res["needs_clarification"] is False
    assert res["client_record"] == {**ION_RECORD, "created": True}
    assert res["entities"]["phone"] == "+40722123456"
    assert res["reply"] == (
        "Am creat clientul Ion Popescu (telefon +40722123456, email ion@exemplu.ro)."
    )
    assert stored_clients(test_sessionmaker) == [("Ion Popescu", "+40722123456", "ion@exemplu.ro")]


def test_english_message_creates_client() -> None:
    res = send(
        "Add a new client named John Doe, phone +40 733 111 222, john@example.com", locale="en"
    )

    assert res["client_record"]["created"] is True
    assert res["reply"] == (
        "I created the client John Doe (phone +40733111222, email john@example.com)."
    )


def test_missing_email_is_requested(test_sessionmaker: sessionmaker[Session]) -> None:
    first = send("Adaugă clientul Ion Popescu, telefon 0722123456")

    assert first["needs_clarification"] is True
    assert first["missing_fields"] == ["email"]
    assert first["reply"] == "Care este adresa de email a clientului Ion Popescu?"
    assert stored_clients(test_sessionmaker) == []

    done = send("ion@exemplu.ro", first["conversation_id"])
    assert done["client_record"] == {**ION_RECORD, "created": True}


def test_all_details_can_be_collected_over_several_turns(
    test_sessionmaker: sessionmaker[Session],
) -> None:
    first = send("Adaugă un client nou")
    assert first["missing_fields"] == ["client", "phone", "email"]
    assert first["reply"] == (
        "Pentru a crea clientul am nevoie de: numele complet, numărul de telefon și adresa de email."
    )
    cid = first["conversation_id"]

    named = send("ion popescu", cid)
    assert named["missing_fields"] == ["phone", "email"]

    done = send("0722 123 456, ion@exemplu.ro", cid)
    assert done["client_record"] == {**ION_RECORD, "created": True}
    assert stored_clients(test_sessionmaker) == [("Ion Popescu", "+40722123456", "ion@exemplu.ro")]


def test_name_is_asked_for_alone_when_only_it_is_missing() -> None:
    res = send("Adaugă un client nou, 0722 123 456, ion@exemplu.ro")
    assert res["missing_fields"] == ["client"]
    assert res["reply"] == "Care este numele complet al clientului?"

    done = send("Ion Popescu", res["conversation_id"])
    assert done["client_record"]["created"] is True


def test_invalid_phone_is_reported_and_nothing_is_stored(
    test_sessionmaker: sessionmaker[Session],
) -> None:
    res = send("Adaugă clientul Ion Popescu, telefon 0722 12, email ion@exemplu.ro")

    assert res["needs_clarification"] is True
    assert res["missing_fields"] == ["phone"]
    assert res["reply"].startswith("Numărul de telefon „0722 12” nu pare valid.")
    assert stored_clients(test_sessionmaker) == []

    done = send("0722 123 456", res["conversation_id"])
    assert done["client_record"] == {**ION_RECORD, "created": True}


def test_invalid_email_is_reported_and_nothing_is_stored(
    test_sessionmaker: sessionmaker[Session],
) -> None:
    res = send("Add client John Doe, phone 0733 111 222, email john@", locale="en")

    assert res["missing_fields"] == ["email"]
    assert res["reply"].startswith('The email address "john@" doesn\'t look valid.')
    assert stored_clients(test_sessionmaker) == []

    done = send("john@example.com", res["conversation_id"], locale="en")
    assert done["client_record"]["email"] == "john@example.com"


def test_invalid_phone_with_other_missing_fields_asks_for_them_too() -> None:
    res = send("Adaugă clientul Ion Popescu, telefon 0722 12")
    assert res["missing_fields"] == ["phone", "email"]
    assert res["reply"].endswith("Care este adresa de email a clientului Ion Popescu?")


def test_repeated_invalid_answers_drop_the_request(
    test_sessionmaker: sessionmaker[Session], isolated_store: ConversationStore
) -> None:
    cid = send("Adaugă clientul Ion Popescu, telefon 0722123456")["conversation_id"]
    for _ in range(MAX_CLARIFICATION_ATTEMPTS - 1):
        assert send("ion@", cid)["needs_clarification"] is True

    dropped = send("ion@", cid)
    assert dropped["needs_clarification"] is False
    assert dropped["reply"].startswith("Nu am reușit să înțeleg detaliile lipsă")
    state = isolated_store.get(cid)
    assert state is None or state.pending is None
    assert stored_clients(test_sessionmaker) == []


def test_cancel_writes_nothing(test_sessionmaker: sessionmaker[Session]) -> None:
    cid = send("Adaugă clientul Ion Popescu, telefon 0722123456")["conversation_id"]
    cancelled = send("anulează", cid)

    assert cancelled["reply"] == "Am anulat cererea. Cu ce te mai pot ajuta?"
    assert stored_clients(test_sessionmaker) == []


def test_existing_client_is_reused_not_duplicated(test_sessionmaker: sessionmaker[Session]) -> None:
    send("Adaugă clientul Ion Popescu, telefon 0722 123 456, email ion@exemplu.ro")
    again = send("Adaugă clientul ion popescu, tel +40 722 123 456, email ION@exemplu.ro")

    assert again["client_record"] == {**ION_RECORD, "created": False}
    assert again["reply"].startswith("Clientul Ion Popescu există deja")
    assert len(stored_clients(test_sessionmaker)) == 1


def test_phone_of_another_client_is_a_conflict(test_sessionmaker: sessionmaker[Session]) -> None:
    send("Adaugă clientul Ion Popescu, telefon 0722 123 456, email ion@exemplu.ro")
    conflict = send("Adaugă clientul Vasile Pop, telefon 0722123456, email vasile@exemplu.ro")

    assert conflict["client_record"] is None
    assert conflict["needs_clarification"] is False
    assert conflict["reply"].startswith("Telefonul sau emailul aparțin deja altui client")
    assert stored_clients(test_sessionmaker) == [("Ion Popescu", "+40722123456", "ion@exemplu.ro")]


def test_created_client_is_listed_and_remembered_for_orders() -> None:
    cid = send("Adaugă clientul Ion Popescu, telefon 0722 123 456, email ion@exemplu.ro")[
        "conversation_id"
    ]

    assert client.get("/api/clients").json() == [ION_RECORD]

    order = send("Vreau să comand 5 laptopuri", cid)
    assert order["order_ready"] is True
    assert order["entities"]["client"] == "Ion Popescu"


def test_add_client_replaces_a_pending_order() -> None:
    cid = send("Vreau să comand laptopuri")["conversation_id"]
    res = send("Adaugă clientul Ana Maria, 0755 000 111, ana@exemplu.ro", cid)

    assert res["intent"] == "add_client"
    assert res["client_record"]["created"] is True


def test_new_order_replaces_a_pending_client(test_sessionmaker: sessionmaker[Session]) -> None:
    cid = send("Adaugă clientul Ion Popescu")["conversation_id"]
    res = send("Vreau să comand 3 laptopuri pentru Ion Popescu", cid)

    assert res["intent"] == "order"
    assert res["order_ready"] is True
    assert stored_clients(test_sessionmaker) == []


def test_remembered_client_is_not_used_as_new_client_name() -> None:
    cid = send("Sunt Maria Ionescu")["conversation_id"]
    res = send("Adaugă un client nou", cid)

    assert res["missing_fields"] == ["client", "phone", "email"]


def test_phone_in_order_answer_is_not_a_quantity() -> None:
    cid = send("Vreau să comand laptopuri")["conversation_id"]
    res = send("Ion Popescu, 0722 123 456", cid)

    assert res["entities"]["quantity"] is None
    assert "quantity" in res["missing_fields"]
