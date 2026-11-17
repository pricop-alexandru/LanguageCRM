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

- **Primary (OpenRouter Decisions API):** When `OPENROUTER_API_KEY` is configured, `app/nlp/parser.py` queries `https://openrouter.ai/api/alpha/decisions` using `perplexity/pplx-decider-flash-v1.3:free` (`choice` for intent classification and `noul` for ambiguity detection) with a `3.0s` timeout. Phone numbers and email addresses are replaced with `[phone]` / `[email]` before the message is sent, and explicit "add client" requests are never sent at all.
- **Fallback (Deterministic Multi-Language Parser):** If `OPENROUTER_API_KEY` is unset or an API error/timeout occurs, `app/nlp/fallback.py` classifies the intent and extracts entities locally using `app/nlp/normalizer.py` and the language packs under `app/nlp/lang/` (`ro.py`, `en.py`).
- **Localization (`app/locales/`):** User-facing reply templates are stored in JSON catalogs (`ro.json`, `en.json`). Pass `"locale": "en"` or `"locale": "ro"` in `POST /api/command` (defaults to `"ro"`).
- **Supported Intents:** `order`, `stock_query`, `add_client`, `greeting`, `unknown`.
- **Extracted Entities:** `product` (`str | null`), `quantity` (`int | null`), `client` (`str | null`), `phone` (`str | null`, canonical `+40…`), `email` (`str | null`, lowercase).

## Client Resolution (US-06)

`POST /api/clients/resolve` reuses a stored client by normalized name, phone number or email, and creates one when no match exists. Romanian local numbers such as `07xxxxxxxx` are stored in canonical international form (`+407xxxxxxxx`); emails are stored lowercase. A lookup without a name that finds no client returns `404`; identifiers that match different clients return `409`.

```json
{ "name": "Ion Popescu", "phone": "07 22-123-456", "email": "ion@exemplu.ro" }
```

The response contains the client fields and a `created` flag. `name`, `phone` and `email` may be sent individually for lookup, but **creating** a client requires all three (US-05); otherwise the request returns `422`. A matched client gets a missing phone or email filled in.

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
- **State storage:** pending requests live only in memory (`app/conversation.py`, 15-minute TTL). They are never written to the database, so no partial orders or clients are created. State is lost on backend restart.
- **Client memory:** a client named in any message of the conversation (e.g. `"Sunt Ion Popescu"`) is remembered and applied to later requests in the same conversation; a newly named client replaces it. Cancelling a request keeps the client.
- **Cancel / give up:** `"anulează"` / `"cancel"` drops the pending request, and so do 3 consecutive answers that fill nothing.
- **Response fields:** `needs_clarification` (`bool`), `missing_fields` (`["product" | "quantity" | "client" | "phone" | "email"]`), `order_ready` (`true` when an order is complete; order placement itself is US-11).

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

## Client Creation from Chat (US-05)

An explicit "add client" message creates a client in SQLite once its name, phone number and email are known and valid:

- **Trigger:** `"Adaugă clientul …"`, `"Client nou: …"`, `"Add a new client named …"`, `"Register customer …"`. Orders never create clients.
- **Extraction:** `app/nlp/contact.py` finds phone numbers (`0722 123 456`, `+40 733 111 222`, `0040…`, dotted/dashed) and emails, validated with `app/identity.py`. The name comes from the language-pack patterns (lowercase names are accepted right after "clientul"/"client").
- **Clarification:** missing fields are asked for (`missing_fields` may contain `client`, `phone`, `email`) using the US-04 dialogue, so one answer can fill several of them. Invalid values (e.g. `0722 12`, `ion@`) are reported back and asked for again; nothing is written until all three are valid. Cancel and give-up behave as in US-04.
- **Duplicates:** an existing client with the same name/phone/email is reused (`created: false`). A phone or email that belongs to a client with a different name is reported as a conflict and nothing is written.
- **Response:** `client_record` (`id`, `name`, `phone`, `email`, `created`) is set when the client is stored, and the client is remembered for later orders in the same conversation.
- **Listing:** `GET /api/clients` returns all clients, newest first (the dashboard table is US-07).

```json
// POST /api/command
{ "prompt": "Adaugă clientul Ion Popescu, telefon 0722 123 456" }
// → { "intent": "add_client", "needs_clarification": true, "missing_fields": ["email"],
//     "reply": "Care este adresa de email a clientului Ion Popescu?", "conversation_id": "7b1e…", ... }

// POST /api/command
{ "prompt": "ion@exemplu.ro", "conversation_id": "7b1e…" }
// → { "intent": "add_client", "reply": "Am creat clientul Ion Popescu (telefon +40722123456, email ion@exemplu.ro).",
//     "client_record": { "id": 1, "name": "Ion Popescu", "phone": "+40722123456", "email": "ion@exemplu.ro", "created": true }, ... }
```

## Testing

```bash
cd backend
uv run --extra dev pytest --cov=app --cov-report=term-missing
```
