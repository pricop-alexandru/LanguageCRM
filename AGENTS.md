# AGENTS.md

Guidance for coding agents working in the **LanguageCRM** repository.

## Repository Structure

- `backend/` — Python 3.12 FastAPI + SQLAlchemy + SQLite backend (`uv` / `pyproject.toml`)
- `frontend/` — TypeScript + Vite frontend (`package.json`, Node 20)
- `docs/` — Course & planning documentation (requirements, agile planning, Planning Poker screenshots)
- `docker-compose.yml` — Multi-service local development setup

## Language Conventions

- **Engineering artifacts in English:** Write all code, comments, docstrings, config descriptions, commit messages, and `README.md` updates in **English**.
- **Course deliverables in Romanian:** Files under `docs/` (`requirements_document.md`, `agile_planning.md`, `workplace_setup.txt`) are maintained in **Romanian** for coursework. Do not translate them to English unless explicitly requested.

## Running & Verifying Changes

- **Full stack (Docker):** `docker compose up --build`
  - Frontend: `http://localhost:5173`
  - Backend API: `http://localhost:8000` (`/health`, `/docs`)
- **Frontend build/typecheck:** `cd frontend && npm run build` (`tsc && vite build`)
- **Backend local run:** `cd backend && uvicorn app.main:app --reload --port 8000` (Python `>=3.12`, dependencies in `backend/pyproject.toml`)

## Security & Git Hygiene

- Never commit secrets, `.env` files, API keys, or local SQLite database files (`*.db`, `*.sqlite`, `*.sqlite3`)—these are ignored in `.gitignore`.
- Do not commit editor-specific folders like `.vscode/` or `.idea/`.
- Use feature branches and Pull Requests rather than committing directly to `main`.
