# LanguageCRM

An autonomous natural-language CRM platform centered around a conversational chatbot that handles customer interactions, inventory checks, and order placement.

## Tech Stack

- **Backend:** Python 3.12, FastAPI, Uvicorn, SQLAlchemy, SQLite (`uv` for dependency management)
- **Frontend:** TypeScript, Vite (Node.js 20)
- **Infrastructure:** Docker & Docker Compose

## Project Structure

```text
.
├── backend/              # FastAPI API & SQLAlchemy/SQLite database layer
├── frontend/             # Vite + TypeScript web interface
├── docs/                 # Requirements, agile planning, and setup notes
├── docker-compose.yml    # Multi-service development setup
├── .gitignore
└── README.md
```

## Quick Start (Docker Compose)

Make sure [Docker](https://www.docker.com/) is running, then from the repository root:

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

## Documentation

- [Requirements Document (RO)](docs/requirements_document.md)
- [Agile Planning (RO)](docs/agile_planning.md)
- [Workplace Setup Notes (RO)](docs/workplace_setup.txt)
