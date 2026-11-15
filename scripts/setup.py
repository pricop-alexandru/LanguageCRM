"""Cross-platform local setup, test, and Docker helper for LanguageCRM."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"


def resolve_tool(name: str) -> str:
    """Return the executable path for *name* or exit with a clear error."""
    path = shutil.which(name)
    if path is None:
        print(f"Error: '{name}' was not found on PATH. Please install it first.", file=sys.stderr)
        raise SystemExit(1)
    return path


def run_step(args: list[str], cwd: Path, label: str) -> None:
    """Run a command in *cwd*, streaming output and exiting on failure."""
    print(f"==> {label}")
    result = subprocess.run(args, cwd=cwd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def cmd_test() -> None:
    """Run backend unit tests and frontend TypeScript/Vite build."""
    uv = resolve_tool("uv")
    npm = resolve_tool("npm")

    run_step([uv, "run", "--extra", "dev", "pytest"], BACKEND_DIR, "Running backend tests (pytest)")
    run_step([npm, "run", "build"], FRONTEND_DIR, "Building frontend (tsc && vite build)")


def cmd_setup() -> None:
    """Configure git hooks, install backend/frontend dependencies, and verify."""
    git = resolve_tool("git")
    uv = resolve_tool("uv")
    npm = resolve_tool("npm")

    run_step([git, "config", "core.hooksPath", ".githooks"], REPO_ROOT, "Enabling shared git hooks")
    run_step([uv, "sync", "--extra", "dev"], BACKEND_DIR, "Installing backend dependencies (uv)")
    run_step([npm, "ci"], FRONTEND_DIR, "Installing frontend dependencies (npm)")
    cmd_test()
    print("\nSetup complete. All checks passed.")


def cmd_up() -> None:
    """Start the full stack with Docker Compose."""
    docker = resolve_tool("docker")
    run_step([docker, "compose", "up", "--build"], REPO_ROOT, "Starting Docker Compose stack")


def main() -> None:
    """Parse CLI subcommands and dispatch to the requested action."""
    parser = argparse.ArgumentParser(description="LanguageCRM local dev & setup helper.")
    parser.add_argument(
        "action",
        nargs="?",
        default="setup",
        choices=["setup", "test", "up"],
        help="Action to run (default: setup).",
    )
    args = parser.parse_args()

    actions = {
        "setup": cmd_setup,
        "test": cmd_test,
        "up": cmd_up,
    }
    actions[args.action]()


if __name__ == "__main__":
    main()
