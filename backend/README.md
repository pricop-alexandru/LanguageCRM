# LanguageCRM Backend

FastAPI + SQLAlchemy + SQLite backend for LanguageCRM.

## Local Run

```bash
cd backend
uv sync --extra dev
uv run uvicorn app.main:app --reload --port 8000 --env-file ../.env
```

## NLP & Intent Parsing (`POST /api/command`)

Incoming English and Romanian messages (with or without diacritics) are parsed in `app/nlp/`:

- **Primary (OpenRouter Decisions API):** When `OPENROUTER_API_KEY` is configured, `app/nlp/parser.py` queries `https://openrouter.ai/api/alpha/decisions` using `perplexity/pplx-decider-flash-v1.3:free` (`choice` for intent classification and `noul` for ambiguity detection) with a `3.0s` timeout.
- **Fallback (Deterministic Multi-Language Parser):** If `OPENROUTER_API_KEY` is unset or an API error/timeout occurs, `app/nlp/fallback.py` classifies the intent and extracts entities locally using `app/nlp/normalizer.py` and the language packs under `app/nlp/lang/` (`ro.py`, `en.py`).
- **Localization (`app/locales/`):** User-facing reply templates are stored in JSON catalogs (`ro.json`, `en.json`). Pass `"locale": "en"` or `"locale": "ro"` in `POST /api/command` (defaults to `"ro"`).
- **Supported Intents:** `order`, `stock_query`, `greeting`, `unknown`.
- **Extracted Entities:** `product` (`str | null`), `quantity` (`int | null`), `client` (`str | null`).

### Example Request & Response

```json
// POST /api/command
{ "prompt": "Creează o comandă de 3 laptopuri pentru Ion Popescu", "locale": "ro" }

// 200 OK
{
  "received_prompt": "Creează o comandă de 3 laptopuri pentru Ion Popescu",
  "intent": "order",
  "confidence": 0.986,
  "entities": {
    "product": "laptopuri",
    "quantity": 3,
    "client": "Ion Popescu"
  },
  "source": "openrouter",
  "reply": "Am înțeles intenția de comandă: 3x laptopuri pentru Ion Popescu."
}
```

## Clarification Dialogue (US-04)

When a request is understood but incomplete, `app/dialogue.py` asks for exactly the missing details instead of guessing:

- **Required slots:** `order` needs `product`, `quantity` and `client`; `stock_query` needs `product`. The client is asked for last (`"Pe ce nume plasez comanda…?"`) and is filled automatically if it was already named in the conversation. When it is the only thing asked for, replies such as `"Sunt Ion Popescu"`, `"ion popescu"` or `"I'm John Doe"` are accepted.
- **Conversation context:** every response carries a `conversation_id`. Send it back on the next request so short answers such as `"5"`, `"cinci"` or `"3 laptopuri"` complete the pending request.
- **State storage:** pending requests live only in memory (`app/conversation.py`, 15-minute TTL). They are never written to the database, so no partial orders are created. State is lost on backend restart.
- **Client memory:** a client named in any message of the conversation (e.g. `"Sunt Ion Popescu"`) is remembered and applied to later requests in the same conversation; a newly named client replaces it. Cancelling a request keeps the client.
- **Cancel / give up:** `"anulează"` / `"cancel"` drops the pending request, and so do 3 consecutive answers that fill nothing.
- **Response fields:** `needs_clarification` (`bool`), `missing_fields` (`["product" | "quantity" | "client"]`), `order_ready` (`true` when an order is complete; order placement itself is US-11).

```json
// POST /api/command
{ "prompt": "Vreau să comand laptopuri pentru Ion Popescu" }
// → { "intent": "order", "needs_clarification": true, "missing_fields": ["quantity"],
//     "conversation_id": "3f9c…", "reply": "Câte bucăți de laptopuri dorești să comanzi?", ... }

// POST /api/command
{ "prompt": "5", "conversation_id": "3f9c…" }
// → { "intent": "order", "order_ready": true,
//     "entities": { "product": "laptopuri", "quantity": 5, "client": "Ion Popescu" }, ... }
```

## Testing

```bash
cd backend
uv run --extra dev pytest --cov=app --cov-report=term-missing
```
