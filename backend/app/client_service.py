from sqlalchemy.orm import Session

from app.database import Client
from app.identity import normalize_name, normalize_phone


class ClientIdentityConflictError(Exception):
    """Raised when a name and phone number identify different client records."""


def resolve_or_create_client(
    db: Session, name: str | None, phone: str | None
) -> tuple[Client, bool] | None:
    """Reuse a client matched by normalized name or phone, or create one if possible."""
    normalized_name = normalize_name(name) if name else None
    normalized_phone = normalize_phone(phone)

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
    if by_name is not None and by_phone is not None and by_name.id != by_phone.id:
        raise ClientIdentityConflictError(
            "The supplied name and phone number belong to different clients"
        )

    existing = by_phone or by_name
    if existing is not None:
        if normalized_phone and existing.phone is None:
            existing.phone = normalized_phone
            db.commit()
            db.refresh(existing)
        return existing, False

    if normalized_name is None:
        return None

    client = Client(
        name=name.strip() if name else None,
        normalized_name=normalized_name,
        phone=normalized_phone,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client, True
