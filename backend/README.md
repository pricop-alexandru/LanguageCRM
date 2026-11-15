# LanguageCRM Backend

FastAPI + SQLAlchemy + SQLite backend for LanguageCRM.

## Local Run

```bash
cd backend
uv sync --extra dev
uv run uvicorn app.main:app --reload --port 8000 --env-file ../.env
```

## NLP & Intent Parsing (`POST /api/command`)

Incoming Romanian messages (with or without diacritics) are parsed in `app/nlp/`:

- **Primary (OpenRouter Decisions API):** When `OPENROUTER_API_KEY` is configured, `app/nlp/parser.py` queries `https://openrouter.ai/api/alpha/decisions` using `perplexity/pplx-decider-flash-v1.3:free` (`choice` for intent classification and `noul` for ambiguity detection) with a `3.0s` timeout.
- **Fallback (Deterministic Romanian Parser):** If `OPENROUTER_API_KEY` is unset or an API error/timeout occurs, `app/nlp/fallback.py` classifies the intent and extracts entities locally using `app/nlp/normalizer.py` and `app/nlp/ro_locale.py`.
- **Supported Intents:** `comanda`, `interogare_stoc`, `salut`, `necunoscut`.
- **Extracted Entities:** `product` (`str | null`), `quantity` (`int | null`), `client` (`str | null`).

### Example Request & Response

```json
// POST /api/command
{ "prompt": "Creează o comandă de 3 laptopuri pentru Ion Popescu" }

// 200 OK
{
  "received_prompt": "Creează o comandă de 3 laptopuri pentru Ion Popescu",
  "intent": "comanda",
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

## Testing

```bash
cd backend
uv run --extra dev pytest --cov=app --cov-report=term-missing
```
