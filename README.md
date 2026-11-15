# LanguageCRM

[![CI](https://github.com/pricop-alexandru/LanguageCRM/actions/workflows/ci.yml/badge.svg)](https://github.com/pricop-alexandru/LanguageCRM/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/taralesca/8a654ac9b3c3ab58c670413b2eba6d1f/raw/languagecrm-coverage.json)](https://gist.github.com/taralesca/8a654ac9b3c3ab58c670413b2eba6d1f)

An autonomous natural-language CRM platform centered around a conversational chatbot that handles customer interactions, inventory checks, and order placement.

## Tech Stack

- **Backend:** Python 3.12, FastAPI, Uvicorn, SQLAlchemy, SQLite (`uv` for dependency management)
- **Frontend:** TypeScript, Vite (Node.js 20)
- **Infrastructure:** Docker & Docker Compose

## Project Structure

```text
.
├── backend/
│   ├── app/              # FastAPI API & SQLAlchemy/SQLite database layer
│   └── tests/            # pytest test suite
├── frontend/             # Vite + TypeScript web interface
├── scripts/              # Cross-platform setup & test runner (setup.py)
├── .githooks/            # Shared Git hooks (pre-commit)
├── docs/                 # Requirements, agile planning, and setup notes
├── docker-compose.yml    # Multi-service development setup
├── AGENTS.md             # Guidance for AI coding agents
├── CONTRIBUTING.md       # Branching, PR, commit, and testing guidelines
├── .gitignore
└── README.md
```

## Quick Start (Docker Compose)

Make sure [Docker](https://www.docker.com/) is running. Optionally, copy `.env.example` to `.env` and set `OPENROUTER_API_KEY` (and `OPENROUTER_DECIDER_MODEL`, defaulting to `perplexity/pplx-decider-flash-v1.3:free`) to enable OpenRouter-based intent parsing (otherwise a local Romanian fallback parser is used). Then from the repository root:

```bash
docker compose up --build
```

Once running:
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

To stop the containers:

```bash
docker compose down
```

## Local Development (Without Docker)

### One-Time Setup (Windows / macOS / Linux)

Requires Python `>=3.12`, [`uv`](https://docs.astral.sh/uv/), and Node.js `>=20`:

```bash
python scripts/setup.py
```

This enables the shared `.githooks` pre-commit hook, installs backend and frontend dependencies, and runs all checks. You can re-run checks anytime with:

```bash
python scripts/setup.py test
```

### Backend

Requires Python `>=3.12` and [`uv`](https://docs.astral.sh/uv/) (or `pip`):

```bash
cd backend
uv pip install -r pyproject.toml
uvicorn app.main:app --reload --port 8000
```

### Frontend

Requires Node.js `>=20`:

```bash
cd frontend
npm install
npm run dev
```

### Pre-commit Hook

Enable the shared Git pre-commit hook (runs backend `pytest` and frontend `npm run build` before each commit):

```bash
git config core.hooksPath .githooks
```

## Documentation

- [Requirements Document (RO)](docs/requirements_document.md)
- [Agile Planning (RO)](docs/agile_planning.md)
- [Workplace Setup Notes (RO)](docs/workplace_setup.txt)
