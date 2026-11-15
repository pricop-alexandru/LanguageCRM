import re
import unicodedata

from app.nlp.ro_locale import ROMANIAN_NUMERALS


def strip_diacritics(text: str) -> str:
    """Remove Romanian and Latin diacritics."""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_text(text: str) -> str:
    """Strip diacritics, lowercase, and collapse whitespace."""
    cleaned = strip_diacritics(text).lower().strip()
    return re.sub(r"\s+", " ", cleaned)


def parse_quantity_text(raw: str | None) -> int | None:
    """Convert a numeric string or Romanian number word into a positive integer."""
    if not raw:
        return None
    cleaned = normalize_text(raw)
    digit_match = re.search(r"\b(\d+)\b", cleaned)
    if digit_match:
        val = int(digit_match.group(1))
        return val if val > 0 else None

    for token in re.findall(r"[a-z]+", cleaned):
        if token in ROMANIAN_NUMERALS:
            return ROMANIAN_NUMERALS[token]
    return None
