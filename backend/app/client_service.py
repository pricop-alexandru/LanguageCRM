from sqlalchemy.orm import Session

from app.database import Client
from app.identity import normalize_email, normalize_name, normalize_phone


class ClientIdentityConflictError(Exception):
    """Raised when the supplied name, phone number and email identify different clients."""


class MissingClientDetailsError(Exception):
    """Raised when a new client would be created without a name, phone number and email."""


def resolve_or_create_client(
    db: Session,
    name: str | None,
    phone: str | None,
    email: str | None = None,
    *,
    require_name_match: bool = False,
) -> tuple[Client, bool] | None:
    """Reuse a client matched by normalized name, phone or email, or create a new one.

    A matched client gets a missing phone number or email filled in. A new client is
    only created when name, phone number and email are all supplied (US-05); if no
    client matches and a name was given without the other two, ``MissingClientDetailsError``
    is raised. Returns None when a lookup without a name finds no client.

    With ``require_name_match`` a client found by phone or email whose name differs
    from ``name`` is reported as a conflict instead of being reused (used by the chat,
    where the operator asked to add a specific person).
    """
    normalized_name = normalize_name(name) if name else None
    normalized_phone = normalize_phone(phone)
    normalized_email = normalize_email(email)

    by_name = (
        db.query(Client).filter(Client.normalized_name == normalized_name).first()
        if normalized_name
        else None
    )
    by_phone = (
        db.query(Client).filter(Client.phone == normalized_phone).first()
        if normalized_phone
        else None
    )
    by_email = (
        db.query(Client).filter(Client.email == normalized_email).first()
        if normalized_email
        else None
    )
    matched_ids = {match.id for match in (by_name, by_phone, by_email) if match is not None}
    if len(matched_ids) > 1:
        raise ClientIdentityConflictError(
            "The supplied name, phone number and email belong to different clients"
        )

    existing = by_phone or by_email or by_name
    if (
        require_name_match
        and existing is not None
        and normalized_name
        and existing.normalized_name
        and existing.normalized_name != normalized_name
    ):
        raise ClientIdentityConflictError(
            "The supplied phone number or email belongs to a client with a different name"
        )
    if existing is not None:
        changed = False
        if normalized_phone and existing.phone is None:
            existing.phone = normalized_phone
            changed = True
        if normalized_email and existing.email is None:
            existing.email = normalized_email
            changed = True
        if changed:
            db.commit()
            db.refresh(existing)
        return existing, False

    if normalized_name is None:
        return None
    if normalized_phone is None or normalized_email is None:
        raise MissingClientDetailsError(
            "Name, phone number and email are required to create a client"
        )

    client = Client(
        name=name.strip() if name else None,
        normalized_name=normalized_name,
        phone=normalized_phone,
        email=normalized_email,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client, True
