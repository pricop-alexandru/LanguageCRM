# AGENTS.md

Guidance for coding agents working in the **LanguageCRM** repository.

## Repository Structure

- `backend/` — Python 3.12 FastAPI + SQLAlchemy + SQLite backend (`uv` / `pyproject.toml`)
  - `backend/app/` — Application package (`main.py`, `database.py`, `schemas.py`)
  - `backend/app/nlp/` — Message parsing & intent detection (OpenRouter `perplexity/pplx-decider-flash-v1.3:free` client, Romanian fallback parser, and `ro_locale.py` language constants)
  - `backend/tests/` — `pytest` test suite (`test_health.py`, `test_parser.py`)
- `frontend/` — TypeScript + Vite frontend (`package.json`, Node 20)
  - Uses `import.meta.env.VITE_API_URL` (defaults to `http://localhost:8000`)
- `scripts/` — Cross-platform developer helpers (`setup.py`)
- `.githooks/` — Shared Git hooks (`pre-commit` runs backend `pytest` + frontend `npm run build`)
- `.github/workflows/` — GitHub Actions CI (`ci.yml` runs backend `pytest` and frontend `npm run build` on PRs and pushes to `main`)
- `docs/` — Course & planning documentation (requirements, agile planning, Planning Poker screenshots)
- `docker-compose.yml` — Multi-service local development setup

## Language Conventions

- **Engineering artifacts in English:** Write all code, comments, docstrings, config descriptions, commit messages, and `README.md` updates in **English**.
- **User-facing Romanian NLP/copy centralized:** Keep all Romanian user-facing reply templates, numerals, and regex/stopword patterns in `backend/app/nlp/ro_locale.py` rather than hardcoding Romanian strings inline across Python modules.
- **Course deliverables in Romanian:** Files under `docs/` (`requirements_document.md`, `agile_planning.md`, `workplace_setup.txt`) are maintained in **Romanian** for coursework. Do not translate them to English unless explicitly requested.

## Running & Verifying Changes

- **One-time local setup (Windows/macOS/Linux):** `python scripts/setup.py` (enables `.githooks`, installs backend/frontend deps, and runs checks)
- **Run all checks:** `python scripts/setup.py test`
- **Full stack (Docker):** `docker compose up --build` (or `python scripts/setup.py up`)
  - Frontend: `http://localhost:5173`
  - Backend API: `http://localhost:8000` (`/health`, `/docs`)
- **Backend tests:** `cd backend && uv run --extra dev pytest`
- **Frontend build/typecheck:** `cd frontend && npm run build` (`tsc && vite build`)
- **Backend local run:** `cd backend && uv run uvicorn app.main:app --reload --port 8000` (Python `>=3.12`, dependencies in `backend/pyproject.toml`)

## Security & Git Hygiene

- Never commit secrets, `.env` files, API keys, or local SQLite database files (`*.db`, `*.sqlite`, `*.sqlite3`)—these are ignored in `.gitignore`.
- Do not commit editor-specific folders like `.vscode/` or `.idea/`.
- Use feature branches and Pull Requests rather than committing directly to `main` (see `CONTRIBUTING.md`).
- Keep `AGENTS.md`, `CONTRIBUTING.md`, and `README.md` up to date whenever project structure, setup commands, or conventions change.
