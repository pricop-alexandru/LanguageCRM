"""Multi-turn dialogue handling: asks for missing details (US-04) and creates clients (US-05).

The dialogue layer sits between the HTTP endpoint and the NLP parser. It keeps
per-conversation context in the conversation store:

* the client the user identified as (in any message), applied to later requests;
* a pending request, while the chatbot asks a targeted question for the slots
  that are still missing. Follow-up answers are merged into it until complete.

Conversation state only lives in memory. The only database write is creating a
client once an "add client" request has a valid name, phone number and email.
"""

from sqlalchemy.orm import Session

from app.client_service import ClientIdentityConflictError, resolve_or_create_client
from app.conversation import ConversationState, ConversationStore, PendingRequest
from app.locales import get_messages
from app.nlp.contact import extract_email, extract_phone, strip_contact_details
from app.nlp.fallback import (
    extract_bare_name,
    extract_client_answer,
    extract_client_name,
    extract_slot_answer,
    is_cancel_request,
)
from app.nlp.parser import format_reply, parse_message
from app.schemas import (
    ClientRecord,
    ClientResolutionResponse,
    CommandResponse,
    ExtractedEntities,
    IntentType,
    ParsedMessage,
    SlotName,
)

REQUIRED_SLOTS: dict[str, tuple[SlotName, ...]] = {
    # The client is asked for last; it is filled automatically if named earlier.
    "order": ("product", "quantity", "client"),
    "stock_query": ("product",),
    # A new client needs all three details before anything is written (US-05).
    "add_client": ("client", "phone", "email"),
}
MAX_CLARIFICATION_ATTEMPTS = 3


def missing_slots(intent: IntentType, entities: ExtractedEntities) -> list[SlotName]:
    """Return the required slots that are still empty for the given intent."""
    return [slot for slot in REQUIRED_SLOTS.get(intent, ()) if getattr(entities, slot) is None]


def format_clarification(
    intent: IntentType, missing: list[SlotName], entities: ExtractedEntities, locale: str
) -> str:
    """Build a localized question asking for exactly the missing slots."""
    replies = get_messages(locale)
    if intent == "stock_query":
        return replies["clarify_stock_product"]
    if intent == "add_client":
        return _format_client_clarification(missing, entities, locale)
    # Ask for what is being ordered first, then who it is for.
    details = [slot for slot in missing if slot != "client"]
    if not details:
        return replies["clarify_order_client"].format(
            quantity=entities.quantity, product=entities.product
        )
    if details == ["quantity"]:
        return replies["clarify_order_quantity"].format(product=entities.product)
    if details == ["product"]:
        return replies["clarify_order_product"].format(quantity=entities.quantity)
    return replies["clarify_order_product_and_quantity"]


def _format_client_clarification(
    missing: list[SlotName], entities: ExtractedEntities, locale: str
) -> str:
    """Ask for the missing details of a new client."""
    replies = get_messages(locale)
    if len(missing) == 1:
        # The name is asked for alone only when it is the one thing missing,
        # so {client} is always known in the phone/email questions.
        key = "clarify_client_name" if missing[0] == "client" else f"clarify_client_{missing[0]}"
        return replies[key].format(client=entities.client)
    fields = [replies[f"field_{slot}"] for slot in missing]
    listed = ", ".join(fields[:-1]) + replies["list_and"] + fields[-1]
    return replies["clarify_client_details"].format(fields=listed)


def _invalid_contact_reply(prompt: str, missing: list[SlotName], locale: str) -> tuple[str, set[SlotName]]:
    """Describe phone numbers/emails in ``prompt`` that were needed but are not valid.

    Returns the reply text (empty if nothing was invalid) and the affected slots.
    """
    replies = get_messages(locale)
    parts: list[str] = []
    invalid: set[SlotName] = set()
    checks = (("phone", extract_phone, "invalid_phone"), ("email", extract_email, "invalid_email"))
    for slot, extract, reply_key in checks:
        if slot in missing:
            valid, raw = extract(prompt)
            if valid is None and raw is not None:
                parts.append(replies[reply_key].format(value=raw))
                invalid.add(slot)  # type: ignore[arg-type]
    return " ".join(parts), invalid


def _response(
    prompt: str,
    intent: IntentType,
    entities: ExtractedEntities,
    reply: str,
    confidence: float = 1.0,
    source: str = "fallback",
    missing: list[SlotName] | None = None,
    client_record: ClientResolutionResponse | None = None,
) -> CommandResponse:
    missing = missing or []
    return CommandResponse(
        received_prompt=prompt,
        intent=intent,
        confidence=confidence,
        entities=entities,
        source=source,  # type: ignore[arg-type]
        reply=reply,
        needs_clarification=bool(missing),
        missing_fields=missing,
        order_ready=intent == "order" and not missing,
        client_record=client_record,
    )


def _remember_client(
    state: ConversationState,
    entities: ExtractedEntities,
    prompt: str,
    allow_bare_name: bool = False,
    expect_name: bool = False,
) -> bool:
    """Update the remembered client from this message and fill it into ``entities``.

    ``allow_bare_name`` accepts a message that is only a name (e.g. "Ion Popescu"),
    which is safe only when the message is not expected to be a product name.
    ``expect_name`` is set when the client was just asked for; lowercase names and
    lead-ins such as "Sunt ..." are then accepted too.
    Returns True if the message itself named a client.
    """
    named = entities.client or extract_client_name(prompt)
    if named is None and expect_name:
        named = extract_client_answer(prompt)
    if named is None and allow_bare_name:
        named = extract_bare_name(prompt)
    if named:
        state.client = named
    if entities.client is None:
        entities.client = state.client
    return named is not None


def _complete(prompt: str, parsed: ParsedMessage, locale: str) -> CommandResponse:
    """Respond to a fully specified request.

    For orders this is the hand-off point where order placement (US-11) will plug in.
    """
    return _response(
        prompt,
        parsed.intent,
        parsed.entities,
        format_reply(parsed, locale=locale),
        confidence=parsed.confidence,
        source=parsed.source,
    )


def _ask(prompt: str, pending: PendingRequest, locale: str) -> CommandResponse:
    missing = missing_slots(pending.intent, pending.entities)
    question = format_clarification(pending.intent, missing, pending.entities, locale)
    if pending.intent == "add_client":
        invalid_reply, invalid = _invalid_contact_reply(prompt, missing, locale)
        if invalid_reply:
            others = [slot for slot in missing if slot not in invalid]
            question = invalid_reply
            if others:
                question += " " + format_clarification(pending.intent, others, pending.entities, locale)
    return _response(
        prompt,
        pending.intent,
        pending.entities,
        question,
        confidence=pending.confidence,
        source=pending.source,
        missing=missing,
    )


def _create_client(
    prompt: str, state: ConversationState, request: ParsedMessage, locale: str, db: Session
) -> CommandResponse:
    """Store the new client once name, phone number and email are all known."""
    replies = get_messages(locale)
    state.pending = None
    entities = request.entities
    try:
        result = resolve_or_create_client(
            db, entities.client, entities.phone, entities.email, require_name_match=True
        )
    except ClientIdentityConflictError:
        return _response(
            prompt,
            "add_client",
            entities,
            replies["client_conflict"].format(client=entities.client),
            request.confidence,
            request.source,
        )
    assert result is not None  # a name is always present here, so a client is found or created
    stored, created = result
    state.client = stored.name
    record = ClientResolutionResponse(**ClientRecord.model_validate(stored).model_dump(), created=created)
    reply = replies["client_created" if created else "client_already_exists"].format(
        client=stored.name, phone=stored.phone or "-", email=stored.email or "-"
    )
    return _response(
        prompt,
        "add_client",
        entities,
        reply,
        request.confidence,
        request.source,
        client_record=record,
    )


def _start(
    prompt: str, state: ConversationState, parsed: ParsedMessage, locale: str, db: Session
) -> CommandResponse:
    """Handle a message that is not continuing a clarification."""
    state.pending = None
    if parsed.intent == "add_client":
        # The new client's name is never taken from the remembered client.
        return _advance_add_client(prompt, state, parsed, locale, db)

    named_client = _remember_client(
        state, parsed.entities, prompt, allow_bare_name=parsed.intent == "unknown"
    )

    if parsed.intent not in REQUIRED_SLOTS:
        if named_client:
            # The user only introduced themselves; remember them for later requests.
            reply = get_messages(locale)["client_noted"].format(client=state.client)
            return _response(
                prompt, parsed.intent, parsed.entities, reply, parsed.confidence, parsed.source
            )
        return _complete(prompt, parsed, locale)

    if not missing_slots(parsed.intent, parsed.entities):
        return _complete(prompt, parsed, locale)

    state.pending = PendingRequest(
        intent=parsed.intent,  # type: ignore[arg-type]
        entities=parsed.entities.model_copy(),
        confidence=parsed.confidence,
        source=parsed.source,
    )
    return _ask(prompt, state.pending, locale)


def _merge(base: ExtractedEntities, update: ExtractedEntities) -> ExtractedEntities:
    """Overlay the non-empty fields of ``update`` onto ``base``."""
    return base.model_copy(update=update.model_dump(exclude_none=True))


def _drop_pending(prompt: str, state: ConversationState, reply_key: str, locale: str) -> CommandResponse:
    """Abandon the pending request but keep the remembered client."""
    state.pending = None
    return _response(
        prompt,
        "unknown",
        ExtractedEntities(client=state.client),
        get_messages(locale)[reply_key],
    )


def _advance_add_client(
    prompt: str, state: ConversationState, request: ParsedMessage, locale: str, db: Session
) -> CommandResponse:
    """Create the client if all details are known, otherwise ask for the rest."""
    if not missing_slots("add_client", request.entities):
        return _create_client(prompt, state, request, locale, db)
    state.pending = PendingRequest(
        intent="add_client",
        entities=request.entities.model_copy(),
        confidence=request.confidence,
        source=request.source,
    )
    return _ask(prompt, state.pending, locale)


def _continue_add_client(
    prompt: str, state: ConversationState, parsed: ParsedMessage, locale: str, db: Session
) -> CommandResponse:
    """Merge a follow-up answer (name, phone number and/or email) into a pending new client."""
    pending = state.pending
    assert pending is not None
    missing_at_start = missing_slots(pending.intent, pending.entities)

    if parsed.intent == "add_client":
        # The request restated with (some) details: newer values win.
        answer = parsed.entities
    else:
        answer = ExtractedEntities(
            client=extract_client_answer(prompt) if "client" in missing_at_start else None,
            phone=extract_phone(prompt)[0],
            email=extract_email(prompt)[0],
        )
    pending.entities = _merge(pending.entities, answer)

    missing = missing_slots(pending.intent, pending.entities)
    if not missing:
        completed = ParsedMessage(
            intent="add_client",
            confidence=pending.confidence,
            entities=pending.entities,
            source=pending.source,
        )
        return _create_client(prompt, state, completed, locale, db)

    if len(missing) < len(missing_at_start):
        pending.attempts = 0  # the user made progress
    else:
        # Nothing new (or only invalid values) was supplied.
        pending.attempts += 1
        if pending.attempts >= MAX_CLARIFICATION_ATTEMPTS:
            return _drop_pending(prompt, state, "clarification_abandoned", locale)

    return _ask(prompt, pending, locale)


def _continue(prompt: str, state: ConversationState, locale: str, db: Session) -> CommandResponse:
    """Handle a follow-up message while a clarification is pending."""
    pending = state.pending
    assert pending is not None

    if is_cancel_request(prompt):
        return _drop_pending(prompt, state, "clarification_cancelled", locale)

    missing_at_start = missing_slots(pending.intent, pending.entities)
    parsed = parse_message(prompt)

    if pending.intent == "add_client":
        if parsed.intent in ("order", "stock_query"):
            # The user moved on to another request: it replaces the pending client.
            return _start(prompt, state, parsed, locale, db)
        return _continue_add_client(prompt, state, parsed, locale, db)

    if parsed.intent == "add_client":
        # An explicit "add client" request always replaces a pending order/stock query.
        return _start(prompt, state, parsed, locale, db)

    if parsed.intent in REQUIRED_SLOTS:
        with_known_client = parsed.entities.model_copy(
            update={"client": parsed.entities.client or state.client}
        )
        is_complete = not missing_slots(parsed.intent, with_known_client)
        switched_intent = parsed.intent != pending.intent and extract_slot_answer(
            strip_contact_details(prompt), missing_at_start
        ) == (None, None)
        if is_complete or switched_intent:
            # The user started a new request: it replaces the pending one.
            return _start(prompt, state, parsed, locale, db)
        if parsed.intent == pending.intent:
            # Same intent restated with partial details: newer values win.
            pending.entities = _merge(pending.entities, parsed.entities)

    still_missing = missing_slots(pending.intent, pending.entities)
    # Phone digits must never be read as a quantity.
    quantity, product = extract_slot_answer(strip_contact_details(prompt), still_missing)
    pending.entities = _merge(
        pending.entities, ExtractedEntities(product=product, quantity=quantity)
    )
    pending.entities.client = None
    # Lenient name parsing only when the client was the one thing we asked for.
    only_client_missing = missing_at_start == ["client"]
    named_client = _remember_client(
        state,
        pending.entities,
        prompt,
        allow_bare_name="product" not in still_missing,
        expect_name=only_client_missing and parsed.intent not in REQUIRED_SLOTS,
    )

    missing = missing_slots(pending.intent, pending.entities)
    if not missing:
        state.pending = None
        completed = ParsedMessage(
            intent=pending.intent,
            confidence=pending.confidence,
            entities=pending.entities,
            source=pending.source,
        )
        return _complete(prompt, completed, locale)

    if len(missing) < len(missing_at_start) or named_client:
        pending.attempts = 0  # the user made progress
    else:
        pending.attempts += 1
        if pending.attempts >= MAX_CLARIFICATION_ATTEMPTS:
            return _drop_pending(prompt, state, "clarification_abandoned", locale)

    return _ask(prompt, pending, locale)


def handle_turn(
    prompt: str,
    locale: str,
    conversation_id: str | None,
    store: ConversationStore,
    db: Session,
) -> CommandResponse:
    """Process one chat message using and updating the conversation's stored context."""
    state = store.get(conversation_id) or ConversationState()
    conversation_id = conversation_id or store.new_id()

    if state.pending is not None:
        response = _continue(prompt, state, locale, db)
    else:
        response = _start(prompt, state, parse_message(prompt), locale, db)

    store.save(conversation_id, state)
    response.conversation_id = conversation_id
    return response
