from typing import Any
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import httpx
import pytest

from app.database import Client as DBClient, Order as DBOrder, SessionLocal, init_db
from app.main import app
from app.nlp.parser import parse_message

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_openrouter_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests run deterministically by default unless a test sets OPENROUTER_API_KEY."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


@pytest.mark.parametrize(
    ("prompt_with_diacritics", "prompt_without_diacritics", "expected_intent"),
    [
        (
            "Creează o comandă de 3 laptopuri pentru Ion Popescu",
            "Creeaza o comanda de 3 laptopuri pentru Ion Popescu",
            "order",
        ),
        (
            "Câte tastaturi aveți în stoc?",
            "Cate tastaturi aveti in stoc?",
            "stock_query",
        ),
        (
            "Bună ziua!",
            "Buna ziua!",
            "greeting",
        ),
        (
            "Vreau să comand ceva acum",
            "Vreau sa comand ceva acum",
            "unknown",
        ),
    ],
)
def test_romanian_intents_with_and_without_diacritics(
    prompt_with_diacritics: str,
    prompt_without_diacritics: str,
    expected_intent: str,
) -> None:
    res_diacritics = client.post("/api/command", json={"prompt": prompt_with_diacritics})
    res_plain = client.post("/api/command", json={"prompt": prompt_without_diacritics})

    assert res_diacritics.status_code == 200
    assert res_plain.status_code == 200

    data_diacritics = res_diacritics.json()
    data_plain = res_plain.json()

    assert data_diacritics["intent"] == expected_intent
    assert data_plain["intent"] == expected_intent
    assert data_diacritics["entities"] == data_plain["entities"]


@pytest.mark.parametrize(
    ("prompt", "expected_intent", "expected_entities"),
    [
        (
            "Create an order of 3 laptops for John Doe",
            "order",
            {"product": "laptops", "quantity": 3, "client": "John Doe"},
        ),
        (
            "I am Jane Smith and I want to buy two monitors",
            "order",
            {"product": "monitors", "quantity": 2, "client": "Jane Smith"},
        ),
        (
            "How many keyboards do you have in stock?",
            "stock_query",
            {"product": "keyboards", "quantity": None, "client": None},
        ),
        (
            "Good morning!",
            "greeting",
            {"product": None, "quantity": None, "client": None},
        ),
        (
            "I want to order something",
            "unknown",
            {"product": None, "quantity": None, "client": None},
        ),
    ],
)
def test_english_intents_and_entities(
    prompt: str,
    expected_intent: str,
    expected_entities: dict[str, Any],
) -> None:
    response = client.post("/api/command", json={"prompt": prompt, "locale": "en"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == expected_intent
    assert payload["entities"] == expected_entities


def test_order_entity_extraction_digits_and_words() -> None:
    res1 = client.post(
        "/api/command",
        json={"prompt": "Creează o comandă de 3 laptopuri pentru Ion Popescu"},
    )
    payload1 = res1.json()
    assert payload1["intent"] == "order"
    assert payload1["entities"] == {
        "product": "laptopuri",
        "quantity": 3,
        "client": "Ion Popescu",
    }

    res2 = client.post(
        "/api/command",
        json={"prompt": "Sunt Maria Ionescu si vreau sa comand doua monitoare"},
    )
    payload2 = res2.json()
    assert payload2["intent"] == "order"
    assert payload2["entities"] == {
        "product": "monitoare",
        "quantity": 2,
        "client": "Maria Ionescu",
    }


def test_stock_query_entity_extraction() -> None:
    res = client.post("/api/command", json={"prompt": "Câte telefoane mai aveți în stoc?"})
    payload = res.json()
    assert payload["intent"] == "stock_query"
    assert payload["entities"]["product"] == "telefoane"


def test_ambiguous_text_returns_unknown_and_does_not_modify_db() -> None:
    init_db()
    with SessionLocal() as db:
        clients_before = db.query(DBClient).count()
        orders_before = db.query(DBOrder).count()

    ambiguous_prompts = [
        "",
        "   ",
        "Vreau și eu ceva",
        "Mai aveți în stoc?",
        "Cât costă transportul până la Cluj?",
        "Comandă pentru Ion Popescu",
        "Do you have anything in stock?",
    ]
    for prompt in ambiguous_prompts:
        response = client.post("/api/command", json={"prompt": prompt})
        assert response.status_code == 200
        assert response.json()["intent"] == "unknown"

    with SessionLocal() as db:
        clients_after = db.query(DBClient).count()
        orders_after = db.query(DBOrder).count()

    assert clients_after == clients_before
    assert orders_after == orders_before


def test_openrouter_decider_integration_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("OPENROUTER_DECIDER_MODEL", "perplexity/pplx-decider-flash-v1.3:free")

    mock_api_response: dict[str, Any] = {
        "answers": {
            "intent": {
                "type": "choice",
                "choice": "order",
                "confidence": 0.96,
                "probabilities": {
                    "order": 0.96,
                    "stock_query": 0.02,
                    "greeting": 0.01,
                    "unknown": 0.01,
                },
            },
            "is_ambiguous": {
                "type": "noul",
                "noul": 0.04,
            },
        }
    }

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = mock_api_response

    with patch("app.nlp.parser.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__.return_value.post.return_value = mock_response
        parsed = parse_message("Vreau sa comand patru casti wireless pentru Andrei Vasile")

    assert parsed.source == "openrouter"
    assert parsed.intent == "order"
    assert parsed.confidence == 0.96
    assert parsed.entities.product == "casti wireless"
    assert parsed.entities.quantity == 4
    assert parsed.entities.client == "Andrei Vasile"


def test_openrouter_decider_ambiguity_guardrail_and_error_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")

    # Case 1: High ambiguity probability downgrades intent to 'unknown'
    ambiguous_api_response: dict[str, Any] = {
        "answers": {
            "intent": {"type": "choice", "choice": "order", "confidence": 0.80},
            "is_ambiguous": {"type": "noul", "noul": 0.90},
        }
    }
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = ambiguous_api_response

    with patch("app.nlp.parser.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__.return_value.post.return_value = mock_response
        parsed = parse_message("Vreau sa fac ceva")
        assert parsed.intent == "unknown"
        assert parsed.source == "openrouter"

    # Case 2: Network/HTTP timeout falls back cleanly to local parser
    with patch("app.nlp.parser.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__.return_value.post.side_effect = (
            httpx.TimeoutException("Timed out")
        )
        fallback_res = parse_message("Salut!")
        assert fallback_res.intent == "greeting"
        assert fallback_res.source == "fallback"


def test_reply_localization_ro_en_and_fallback() -> None:
    res_ro = client.post(
        "/api/command",
        json={"prompt": "Creeaza o comanda de 2 laptopuri pentru Ion Popescu", "locale": "ro"},
    )
    assert res_ro.status_code == 200
    assert "Am înțeles intenția de comandă: 2x laptopuri pentru Ion Popescu." == res_ro.json()["reply"]

    res_en = client.post(
        "/api/command",
        json={"prompt": "Order 2 laptops for John Doe", "locale": "en"},
    )
    assert res_en.status_code == 200
    assert "Order intent detected: 2x laptops for John Doe." == res_en.json()["reply"]

    # Unknown or traversal-like locale falls back safely to default Romanian catalog
    for bad_locale in ("fr", "../../etc", ""):
        res_fallback = client.post(
            "/api/command",
            json={"prompt": "Salut!", "locale": bad_locale},
        )
        assert res_fallback.status_code == 200
        assert "Salut!" in res_fallback.json()["reply"]
