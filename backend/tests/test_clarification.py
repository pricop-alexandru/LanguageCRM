"""Tests for multi-turn clarification of incomplete messages (US-04)."""

from collections.abc import Iterator
from typing import Any

from fastapi.testclient import TestClient
import pytest

from app.conversation import ConversationStore, get_conversation_store
from sqlalchemy.orm import Session, sessionmaker

from app.database import Client as DBClient, Order as DBOrder
from app.dialogue import MAX_CLARIFICATION_ATTEMPTS
from app.main import app

client = TestClient(app)


class FakeClock:
    def __init__(self) -> None:
        self.now = 1_000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def store(clock: FakeClock) -> ConversationStore:
    return ConversationStore(ttl_seconds=900, clock=clock)


@pytest.fixture(autouse=True)
def isolated_store(
    store: ConversationStore, monkeypatch: pytest.MonkeyPatch
) -> Iterator[None]:
    """Give each test a fresh store and keep the parser deterministic."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    app.dependency_overrides[get_conversation_store] = lambda: store
    yield
    app.dependency_overrides.pop(get_conversation_store, None)


def send(prompt: str, conversation_id: str | None = None, locale: str = "ro") -> dict[str, Any]:
    body: dict[str, Any] = {"prompt": prompt, "locale": locale}
    if conversation_id is not None:
        body["conversation_id"] = conversation_id
    response = client.post("/api/command", json=body)
    assert response.status_code == 200
    return response.json()


def test_missing_quantity_is_requested_and_context_is_kept(store: ConversationStore) -> None:
    first = send("Vreau să comand laptopuri pentru Ion Popescu")
    assert first["intent"] == "order"
    assert first["needs_clarification"] is True
    assert first["missing_fields"] == ["quantity"]
    assert first["order_ready"] is False
    assert first["reply"] == "Câte bucăți de laptopuri dorești să comanzi?"
    cid = first["conversation_id"]
    assert cid
    assert len(store) == 1

    second = send("5", cid)
    assert second["conversation_id"] == cid
    assert second["intent"] == "order"
    assert second["needs_clarification"] is False
    assert second["missing_fields"] == []
    assert second["order_ready"] is True
    assert second["entities"] == {"product": "laptopuri", "quantity": 5, "client": "Ion Popescu", "phone": None, "email": None}
    assert second["reply"] == "Am înțeles intenția de comandă: 5x laptopuri pentru Ion Popescu."
    state = store.get(cid)
    assert state is not None and state.pending is None
    assert state.client == "Ion Popescu"


@pytest.mark.parametrize("answer", ["cinci", "5 bucăți", "vreau 5", "5, te rog"])
def test_quantity_answer_variants(answer: str) -> None:
    cid = send("Vreau să comand laptopuri")["conversation_id"]
    answered = send(answer, cid)
    # Product and quantity are known; only the client is still asked for.
    assert answered["missing_fields"] == ["client"]
    assert answered["entities"]["quantity"] == 5


def test_missing_product_and_quantity_filled_by_one_answer() -> None:
    first = send("Vreau să comand ceva")
    assert first["missing_fields"] == ["product", "quantity", "client"]

    answered = send("3 laptopuri", first["conversation_id"])
    assert answered["missing_fields"] == ["client"]
    assert answered["entities"] == {"product": "laptopuri", "quantity": 3, "client": None, "phone": None, "email": None}


def test_missing_product_with_known_quantity() -> None:
    first = send("vreau să comand 3")
    assert first["missing_fields"] == ["product", "client"]
    assert first["entities"]["quantity"] == 3

    answered = send("monitoare", first["conversation_id"])
    assert answered["missing_fields"] == ["client"]
    assert answered["entities"] == {"product": "monitoare", "quantity": 3, "client": None, "phone": None, "email": None}


def test_slots_can_be_filled_over_several_turns() -> None:
    cid = send("Comandă pentru Ion Popescu")["conversation_id"]

    partial = send("tastaturi", cid)
    assert partial["needs_clarification"] is True
    assert partial["missing_fields"] == ["quantity"]
    assert partial["entities"]["product"] == "tastaturi"

    done = send("2", cid)
    assert done["entities"] == {"product": "tastaturi", "quantity": 2, "client": "Ion Popescu", "phone": None, "email": None}


def test_unhelpful_answers_keep_context_then_give_up(store: ConversationStore) -> None:
    cid = send("Vreau să comand laptopuri")["conversation_id"]

    for answer in ["hmm", "Cât costă transportul?"][: MAX_CLARIFICATION_ATTEMPTS - 1]:
        retry = send(answer, cid)
        assert retry["needs_clarification"] is True
        assert retry["missing_fields"] == ["quantity", "client"]
        assert retry["entities"]["product"] == "laptopuri"

    abandoned = send("multe", cid)
    assert abandoned["intent"] == "unknown"
    assert abandoned["needs_clarification"] is False
    assert "renunțat" in abandoned["reply"]
    assert len(store) == 0


@pytest.mark.parametrize(("cancel", "locale"), [("anulează", "ro"), ("cancel", "en")])
def test_cancel_clears_pending_request(cancel: str, locale: str, store: ConversationStore) -> None:
    cid = send("Vreau să comand laptopuri", locale=locale)["conversation_id"]

    cancelled = send(cancel, cid, locale=locale)
    assert cancelled["intent"] == "unknown"
    assert cancelled["needs_clarification"] is False
    assert len(store) == 0

    after = send("5", cid, locale=locale)
    assert after["intent"] == "unknown"
    assert after["needs_clarification"] is False
    assert after["order_ready"] is False


def test_new_complete_order_replaces_pending_request(store: ConversationStore) -> None:
    cid = send("Vreau să comand laptopuri pentru Ion Popescu")["conversation_id"]

    replaced = send("Creează o comandă de 2 monitoare", cid)
    assert replaced["order_ready"] is True
    # The client given earlier in the conversation is carried over.
    assert replaced["entities"] == {"product": "monitoare", "quantity": 2, "client": "Ion Popescu", "phone": None, "email": None}
    state = store.get(cid)
    assert state is not None and state.pending is None


def test_expired_or_unknown_conversation_starts_fresh(clock: FakeClock) -> None:
    cid = send("Vreau să comand laptopuri")["conversation_id"]
    clock.advance(901)
    expired = send("5", cid)
    assert expired["intent"] == "unknown"
    assert expired["order_ready"] is False

    unknown = send("5", "does-not-exist")
    assert unknown["intent"] == "unknown"
    assert unknown["conversation_id"] == "does-not-exist"


def test_english_flow_uses_english_replies() -> None:
    first = send("I want to buy keyboards for John Doe", locale="en")
    assert first["missing_fields"] == ["quantity"]
    assert first["reply"] == "How many keyboards would you like to order?"

    done = send("three", first["conversation_id"], locale="en")
    assert done["entities"] == {"product": "keyboards", "quantity": 3, "client": "John Doe", "phone": None, "email": None}
    assert done["reply"] == "Order intent detected: 3x keyboards for John Doe."


def test_stock_query_product_clarification() -> None:
    first = send("Mai aveți în stoc?")
    assert first["intent"] == "stock_query"
    assert first["missing_fields"] == ["product"]
    assert first["reply"] == "Pentru ce produs dorești să verific stocul?"

    done = send("tastaturi", first["conversation_id"])
    assert done["intent"] == "stock_query"
    assert done["needs_clarification"] is False
    assert done["order_ready"] is False
    assert done["reply"] == "Verific stocul pentru produsul: tastaturi."


def test_complete_message_needs_no_clarification(store: ConversationStore) -> None:
    res = send("Creează o comandă de 3 laptopuri pentru Ion Popescu")
    assert res["order_ready"] is True
    assert res["needs_clarification"] is False
    assert res["conversation_id"]
    state = store.get(res["conversation_id"])
    assert state is not None and state.pending is None
    assert state.client == "Ion Popescu"


def test_clarification_never_creates_partial_db_records(
    test_sessionmaker: sessionmaker[Session],
) -> None:
    with test_sessionmaker() as db:
        clients_before = db.query(DBClient).count()
        orders_before = db.query(DBOrder).count()

    cid = send("Comandă pentru Ion Popescu")["conversation_id"]
    send("laptopuri", cid)
    send("4", cid)

    cid = send("Vreau să comand monitoare")["conversation_id"]
    send("anulează", cid)

    with test_sessionmaker() as db:
        assert db.query(DBClient).count() == clients_before
        assert db.query(DBOrder).count() == orders_before


def test_conversation_id_length_is_validated() -> None:
    response = client.post("/api/command", json={"prompt": "Salut", "conversation_id": "x" * 65})
    assert response.status_code == 422


def test_switching_to_another_incomplete_intent_replaces_pending() -> None:
    cid = send("Vreau să comand laptopuri")["conversation_id"]
    switched = send("Mai aveți în stoc?", cid)
    assert switched["intent"] == "stock_query"
    assert switched["missing_fields"] == ["product"]

    done = send("tastaturi", cid)
    assert done["intent"] == "stock_query"
    assert done["reply"] == "Verific stocul pentru produsul: tastaturi."


def test_decider_misclassified_bare_answer_still_fills_slot(monkeypatch: pytest.MonkeyPatch) -> None:
    """A bare answer labelled with a different intent by the decider must not reset the order."""
    from app import dialogue
    from app.schemas import ParsedMessage

    cid = send("Comandă pentru Ion Popescu")["conversation_id"]
    monkeypatch.setattr(
        dialogue,
        "parse_message",
        lambda prompt: ParsedMessage(intent="stock_query", confidence=0.7, source="openrouter"),
    )
    partial = send("3 tastaturi", cid)
    assert partial["intent"] == "order"
    assert partial["order_ready"] is True
    assert partial["entities"] == {"product": "tastaturi", "quantity": 3, "client": "Ion Popescu", "phone": None, "email": None}


@pytest.mark.parametrize(
    ("intro", "locale"),
    [
        ("Sunt Ion Popescu", "ro"),
        ("Bună, mă numesc Ion Popescu", "ro"),
        ("Hi, my name is Ion Popescu", "en"),
    ],
)
def test_client_from_earlier_message_is_applied_to_later_order(intro: str, locale: str) -> None:
    first = send(intro, locale=locale)
    assert first["intent"] == "unknown"
    assert first["entities"]["client"] == "Ion Popescu"
    assert "Ion Popescu" in first["reply"]

    order = "Vreau să comand 5 laptopuri" if locale == "ro" else "I want to buy 5 laptops"
    done = send(order, first["conversation_id"], locale=locale)
    assert done["order_ready"] is True
    assert done["entities"]["client"] == "Ion Popescu"


def test_client_is_kept_through_clarification_and_after_cancel() -> None:
    cid = send("Sunt Ion Popescu")["conversation_id"]

    asked = send("Vreau să comand laptopuri", cid)
    assert asked["missing_fields"] == ["quantity"]
    assert asked["entities"]["client"] == "Ion Popescu"
    assert send("5", cid)["entities"]["client"] == "Ion Popescu"

    send("Vreau să comand monitoare", cid)
    cancelled = send("anulează", cid)
    assert cancelled["entities"]["client"] == "Ion Popescu"

    again = send("Creează o comandă de 2 monitoare", cid)
    assert again["entities"]["client"] == "Ion Popescu"


def test_newly_named_client_replaces_remembered_one() -> None:
    cid = send("Sunt Ion Popescu")["conversation_id"]
    done = send("Creează o comandă de 2 monitoare pentru Maria Ionescu", cid)
    assert done["entities"]["client"] == "Maria Ionescu"
    assert send("Vreau să comand 3 laptopuri", cid)["entities"]["client"] == "Maria Ionescu"


def test_client_is_not_shared_between_conversations() -> None:
    send("Sunt Ion Popescu")
    other = send("Vreau să comand 5 laptopuri")
    assert other["entities"]["client"] is None


def test_greeting_with_name_is_acknowledged(monkeypatch: pytest.MonkeyPatch) -> None:
    """The decider may label an introduction as a greeting; the name must still be kept."""
    from app import dialogue
    from app.nlp.fallback import extract_client_name
    from app.schemas import ExtractedEntities, ParsedMessage

    monkeypatch.setattr(
        dialogue,
        "parse_message",
        lambda prompt: ParsedMessage(
            intent="greeting",
            confidence=0.9,
            entities=ExtractedEntities(client=extract_client_name(prompt)),
            source="openrouter",
        ),
    )
    res = send("Bună, sunt Ion Popescu")
    assert res["intent"] == "greeting"
    assert res["reply"].startswith("Mulțumesc, Ion Popescu!")


def test_bare_name_reply_during_clarification_sets_client() -> None:
    cid = send("Vreau sa comand laptopuri")["conversation_id"]

    named = send("Ion Popescu", cid)
    assert named["needs_clarification"] is True
    assert named["missing_fields"] == ["quantity"]
    assert named["entities"]["client"] == "Ion Popescu"

    done = send("5", cid)
    assert done["entities"] == {"product": "laptopuri", "quantity": 5, "client": "Ion Popescu", "phone": None, "email": None}


def test_naming_client_counts_as_progress() -> None:
    """Naming the client counts as progress, so it must not trigger abandonment."""
    cid = send("Vreau sa comand laptopuri")["conversation_id"]
    send("hmm", cid)
    send("nu stiu", cid)
    named = send("Ion Popescu", cid)
    assert named["needs_clarification"] is True
    assert named["entities"]["client"] == "Ion Popescu"


def test_bare_capitalized_reply_is_product_when_product_is_missing() -> None:
    cid = send("vreau sa comand 2")["conversation_id"]
    done = send("Dell Latitude", cid)
    assert done["entities"] == {"product": "dell latitude", "quantity": 2, "client": None, "phone": None, "email": None}


def test_bare_name_as_first_message_is_remembered() -> None:
    first = send("Ion Popescu")
    assert first["entities"]["client"] == "Ion Popescu"
    done = send("Vreau sa comand 5 laptopuri", first["conversation_id"])
    assert done["entities"]["client"] == "Ion Popescu"


@pytest.mark.parametrize(
    ("answer", "locale", "expected"),
    [
        ("Sunt Ion Popescu", "ro", "Ion Popescu"),
        ("Ion Popescu", "ro", "Ion Popescu"),
        ("ion popescu", "ro", "Ion Popescu"),
        ("sunt ion popescu", "ro", "Ion Popescu"),
        ("pentru maria ionescu", "ro", "Maria Ionescu"),
        ("I'm John Doe", "en", "John Doe"),
        ("john doe", "en", "John Doe"),
    ],
)
def test_order_without_client_asks_for_client(answer: str, locale: str, expected: str) -> None:
    prompt = "vreau sa comand 5 laptopuri" if locale == "ro" else "I want to order 5 laptops"
    asked = send(prompt, locale=locale)
    assert asked["intent"] == "order"
    assert asked["order_ready"] is False
    assert asked["missing_fields"] == ["client"]

    done = send(answer, asked["conversation_id"], locale=locale)
    assert done["order_ready"] is True
    assert done["entities"]["client"] == expected
    assert done["entities"]["quantity"] == 5


@pytest.mark.parametrize("answer", ["multumesc frumos", "nu stiu", "hmm", "cine esti tu?"])
def test_non_name_replies_are_not_taken_as_client(answer: str) -> None:
    cid = send("vreau sa comand 5 laptopuri")["conversation_id"]
    retry = send(answer, cid)
    assert retry["needs_clarification"] is True
    assert retry["missing_fields"] == ["client"]
    assert retry["entities"]["client"] is None
