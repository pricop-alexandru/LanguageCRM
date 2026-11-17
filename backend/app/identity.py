import re
import unicodedata


def normalize_name(name: str) -> str:
    """Normalize a client name for exact, case-insensitive matching."""
    decomposed = unicodedata.normalize("NFKD", name)
    without_diacritics = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return re.sub(r"\s+", " ", without_diacritics).strip().casefold()


def normalize_phone(phone: str | None) -> str | None:
    """Return a phone number in canonical international form."""
    if phone is None or not phone.strip():
        return None

    raw = phone.strip()
    if not re.fullmatch(r"[+0-9\s().-]+", raw) or raw.count("+") > 1:
        raise ValueError("Phone number contains unsupported characters")
    if "+" in raw and not raw.startswith("+"):
        raise ValueError("The international prefix must be at the start of the phone number")

    digits = re.sub(r"[^0-9]", "", raw)
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0"):
        if len(digits) != 10:
            raise ValueError("Romanian local phone numbers must contain 10 digits")
        digits = "40" + digits[1:]
    if not 8 <= len(digits) <= 15:
        raise ValueError("Phone number must contain 8 to 15 digits")
    return f"+{digits}"


_EMAIL_PATTERN = re.compile(
    r"[a-z0-9](?:[a-z0-9._%+-]*[a-z0-9_%+-])?@[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*\.[a-z]{2,}"
)


def normalize_email(email: str | None) -> str | None:
    """Return a trimmed, lowercased email address, or raise ValueError if it is invalid."""
    if email is None or not email.strip():
        return None
    cleaned = email.strip().lower()
    if ".." in cleaned or not _EMAIL_PATTERN.fullmatch(cleaned):
        raise ValueError("Email address is not valid")
    return cleaned
