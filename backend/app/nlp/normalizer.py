import re
import unicodedata

from app.nlp.lang import ALL_NUMERALS


def strip_diacritics(text: str) -> str:
    """Remove Latin diacritics from text."""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_text(text: str) -> str:
    """Strip diacritics, lowercase, and collapse whitespace."""
    cleaned = strip_diacritics(text).lower().strip()
    return re.sub(r"\s+", " ", cleaned)


def parse_quantity_text(raw: str | None, numerals: dict[str, int] = ALL_NUMERALS) -> int | None:
    """Convert a numeric string or numeral word into a positive integer."""
    if not raw:
        return None
    cleaned = normalize_text(raw)
    digit_match = re.search(r"\b(\d+)\b", cleaned)
    if digit_match:
        val = int(digit_match.group(1))
        return val if val > 0 else None

    for token in re.findall(r"[a-z]+", cleaned):
        if token in numerals:
            return numerals[token]
    return None
