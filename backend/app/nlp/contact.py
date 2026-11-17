"""Language-independent extraction of contact details (phone number, email) from chat text.

Values are validated with the same rules the client service uses
(``app.identity.normalize_phone`` / ``normalize_email``), so whatever the chatbot
accepts can be stored as is.
"""

import re

from app.identity import normalize_email, normalize_phone

# Phone-like text: starts with "+", "00" or a local "0" (optionally in brackets) and
# continues with digits and common separators. Plain quantities ("5", "100") never
# start with "0" or "+", so they are not mistaken for phone numbers.
_PHONE_CANDIDATE = re.compile(r"(?<![\w@.+])\(?(?:\+|0)[\d\s().\-]{4,}\d(?![\w@])")
# Email-like text: any token containing "@".
_EMAIL_CANDIDATE = re.compile(r"[^\s,;:<>()\[\]\"']*@[^\s,;:<>()\[\]\"']*")
_TRAILING_DOTS = re.compile(r"[.]+$")

PHONE_PLACEHOLDER = "[phone]"
EMAIL_PLACEHOLDER = "[email]"


def _phone_candidates(text: str) -> list[str]:
    return [match.group(0).strip() for match in _PHONE_CANDIDATE.finditer(text)]


def _email_candidates(text: str) -> list[str]:
    candidates = (_TRAILING_DOTS.sub("", match.group(0)) for match in _EMAIL_CANDIDATE.finditer(text))
    return [candidate for candidate in candidates if candidate]


def extract_phone(text: str) -> tuple[str | None, str | None]:
    """Return ``(canonical phone, invalid phone-like text)`` found in the message.

    The first valid number wins. If the message only contains phone-like text that
    fails validation (e.g. "0722 12"), it is returned as the second element so the
    chatbot can say which value looks wrong.
    """
    invalid: str | None = None
    for candidate in _phone_candidates(text):
        try:
            return normalize_phone(candidate), None
        except ValueError:
            invalid = invalid or candidate
    return None, invalid


def extract_email(text: str) -> tuple[str | None, str | None]:
    """Return ``(normalized email, invalid email-like text)`` found in the message."""
    invalid: str | None = None
    for candidate in _email_candidates(text):
        try:
            return normalize_email(candidate), None
        except ValueError:
            invalid = invalid or candidate
    return None, invalid


def mask_contact_details(text: str) -> str:
    """Replace phone- and email-like text with placeholders before sending it to an external service."""
    masked = _EMAIL_CANDIDATE.sub(EMAIL_PLACEHOLDER, text)
    return _PHONE_CANDIDATE.sub(PHONE_PLACEHOLDER, masked)


def strip_contact_details(text: str) -> str:
    """Remove phone- and email-like text so that it is not parsed as names or quantities."""
    stripped = _EMAIL_CANDIDATE.sub(" ", text)
    stripped = _PHONE_CANDIDATE.sub(" ", stripped)
    return re.sub(r"[ \t]+", " ", stripped).strip()
