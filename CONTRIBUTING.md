# Contributing to LanguageCRM

Thanks for contributing! Please follow these guidelines so both teammates and AI coding agents stay aligned.

## Branching & Pull Requests

- **Never push directly to `main`.** Always create a branch from an up-to-date `main`:
  ```bash
  git fetch origin
  git checkout -b feat/short-description origin/main
  ```
- Use clear branch prefixes: `feat/`, `fix/`, `refactor/`, `docs/`, `test/`, `ci/`, `chore/`.
- Open a **Pull Request** targeting `main` and wait for GitHub Actions CI (`Backend tests (pytest)` and `Frontend build (tsc & vite)`) to pass before merging.
- Delete the feature branch after it is merged.

## Commit Messages

Write commit messages in **English** using [Conventional Commits](https://www.conventionalcommits.org/):
- `feat: ...` — new feature
- `fix: ...` — bug fix
- `refactor: ...` — code restructuring without behavior change
- `test: ...` — adding or updating tests
- `docs: ...` — documentation updates
- `ci: ...` — GitHub Actions / CI changes
- `chore: ...` — tooling, setup, or maintenance

## Local Setup & Testing

Run the one-time setup after cloning:

```bash
python scripts/setup.py
```

This enables the shared `.githooks/pre-commit` hook, installs backend and frontend dependencies, and runs all checks. Before opening a PR:
- Add or update `pytest` tests in `backend/tests/` for backend changes.
- Verify everything passes with:
  ```bash
  python scripts/setup.py test
  ```

## Language & Documentation Rules

- **Engineering artifacts in English:** All code, comments, docstrings, tests, config descriptions, `README.md`, `CONTRIBUTING.md`, and `AGENTS.md` must be written in **English**.
- **Course deliverables in Romanian:** Files under `docs/` (`requirements_document.md`, `agile_planning.md`, `workplace_setup.txt`) are maintained in **Romanian** for coursework.
- Keep `AGENTS.md` and `README.md` updated whenever project structure, setup steps, or conventions change.

## Security & Git Hygiene

- Never commit `.env` files, API keys, secrets, or local SQLite database files (`*.db`, `*.sqlite`, `*.sqlite3`).
- Do not commit editor folders such as `.vscode/` or `.idea/`.
