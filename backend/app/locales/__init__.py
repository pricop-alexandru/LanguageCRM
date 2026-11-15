"""Localization loader for user-facing JSON message catalogs."""

from functools import lru_cache
import json
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent
DEFAULT_LOCALE = "ro"
SUPPORTED_LOCALES: frozenset[str] = frozenset({"ro", "en"})


def normalize_locale(locale: str | None) -> str:
    """Return a supported locale code, falling back to DEFAULT_LOCALE."""
    if not locale:
        return DEFAULT_LOCALE
    candidate = locale.strip().lower()
    return candidate if candidate in SUPPORTED_LOCALES else DEFAULT_LOCALE


@lru_cache(maxsize=8)
def _load_catalog(locale: str) -> dict[str, str]:
    locale_file = LOCALES_DIR / f"{locale}.json"
    with locale_file.open(encoding="utf-8") as fh:
        return json.load(fh)


def get_messages(locale: str = DEFAULT_LOCALE) -> dict[str, str]:
    """Load and cache user-facing message templates for the given locale."""
    return _load_catalog(normalize_locale(locale))
