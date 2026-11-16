import re

from app.nlp.lang import ALL_AMBIGUOUS_PRODUCT_WORDS, ALL_PACKS, LanguagePack
from app.nlp.normalizer import normalize_text, parse_quantity_text, strip_diacritics
from app.schemas import ExtractedEntities, IntentType, ParsedMessage, SlotName

_TRAILING_PUNCTUATION = re.compile(r"[?!.,;:]+$")
# A message consisting only of a 2-3 word capitalized full name, e.g. "Ion Popescu".
_BARE_NAME_PATTERN = re.compile(r"\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s*[.!]?\s*")
MAX_PRODUCT_ANSWER_WORDS = 5


def extract_client_name(original_text: str, packs: tuple[LanguagePack, ...] = ALL_PACKS) -> str | None:
    """Extract client full name using configured language pack patterns."""
    ascii_text = strip_diacritics(original_text)
    for pack in packs:
        for pattern in pack.client_patterns:
            match = pattern.search(ascii_text)
            if match:
                return match.group(1).strip()
    return None


def extract_bare_name(original_text: str) -> str | None:
    """Return the name if the whole message is just a capitalized full name."""
    match = _BARE_NAME_PATTERN.fullmatch(strip_diacritics(original_text))
    return match.group(1) if match else None


_NAME_WORDS_PATTERN = re.compile(r"[a-z]+(?:-[a-z]+)?(?:\s+[a-z]+(?:-[a-z]+)?){1,2}")


def extract_client_answer(
    original_text: str, packs: tuple[LanguagePack, ...] = ALL_PACKS
) -> str | None:
    """Extract a client name from a reply to "who is the order for?".

    More lenient than ``extract_client_name``: accepts lowercase names and an optional
    lead-in ("Sunt ...", "pentru ...", "I'm ..."). Use it only when the name is the one
    thing being asked for. Returns the name title-cased, e.g. "ion popescu" -> "Ion Popescu".
    """
    named = extract_client_name(original_text, packs)
    if named:
        return named
    if not original_text or "?" in original_text:
        return None
    norm = re.sub(r"\s+", " ", re.sub(r"[!.,;:]", " ", normalize_text(original_text))).strip()
    for pack in packs:
        candidate = pack.client_answer_prefix_pattern.sub("", norm, count=1).strip()
        if (
            _NAME_WORDS_PATTERN.fullmatch(candidate)
            and candidate not in ALL_AMBIGUOUS_PRODUCT_WORDS
            and not any(p.non_name_pattern.search(candidate) for p in packs)
        ):
            return candidate.title()
    return None


def _extract_for_pack(
    norm_clean: str, intent: IntentType, pack: LanguagePack
) -> tuple[int | None, str | None]:
    """Attempt quantity and product extraction using a single language pack.

    The quantity is returned even when no usable product is found, so that a
    clarification only has to ask for what is actually missing.
    """
    found_qty: int | None = None

    # 1. Explicit quantity + product phrasing
    match = pack.qty_product_pattern.search(norm_clean)
    if match:
        qty_raw, prod_raw = match.group(1), match.group(2)
        prod_clean = pack.stopwords_tail.sub("", prod_raw).strip()
        if not prod_clean.startswith(pack.order_noun_prefix):
            qty = parse_quantity_text(qty_raw, pack.numerals)
            if prod_clean and prod_clean not in pack.ambiguous_product_words:
                return qty, prod_clean
            found_qty = qty

    # 2. "order of <qty> <product>" phrasing
    after_order = pack.order_of_qty_product_pattern.search(norm_clean)
    if after_order:
        qty = parse_quantity_text(after_order.group(1), pack.numerals)
        prod_clean = pack.stopwords_tail.sub("", after_order.group(2)).strip()
        if prod_clean and prod_clean not in pack.ambiguous_product_words:
            return qty, prod_clean
        found_qty = found_qty or qty

    # 3. Stock query phrasings
    if intent == "stock_query":
        for pat in pack.stock_patterns:
            m = pat.search(norm_clean)
            if m:
                prod_clean = pack.stopwords_tail.sub("", m.group(1)).strip()
                qty = parse_quantity_text(prod_clean, pack.numerals)
                if qty is not None:
                    prod_clean = pack.leading_numeral_pattern.sub("", prod_clean).strip()
                if prod_clean and prod_clean not in pack.ambiguous_product_words:
                    return qty, prod_clean

    # 4. Order without explicit quantity
    if intent == "order":
        order_prod = pack.order_product_pattern.search(norm_clean)
        if order_prod:
            prod_clean = pack.stopwords_tail.sub("", order_prod.group(1)).strip()
            starts_with_qty = pack.leading_numeral_pattern.match(f"{prod_clean} ")
            if (
                prod_clean
                and not starts_with_qty
                and prod_clean not in pack.ambiguous_product_words
            ):
                return None, prod_clean

    # 5. Quantity without a product (e.g. "I want to order 3")
    if found_qty is None and intent == "order":
        qty_only = pack.qty_only_pattern.search(pack.stopwords_tail.sub("", norm_clean).strip())
        if qty_only:
            found_qty = parse_quantity_text(qty_only.group(1), pack.numerals)

    return found_qty, None


def extract_quantity_and_product(
    original_text: str, intent: IntentType, packs: tuple[LanguagePack, ...] = ALL_PACKS
) -> tuple[int | None, str | None]:
    """Extract quantity and product name across configured language packs."""
    norm_clean = _TRAILING_PUNCTUATION.sub("", normalize_text(original_text)).strip()
    first_qty: int | None = None
    for pack in packs:
        qty, product = _extract_for_pack(norm_clean, intent, pack)
        if product is not None:
            return qty, product
        if first_qty is None:
            first_qty = qty
    return first_qty, None


def fallback_parse_message(prompt: str) -> ParsedMessage:
    """Deterministic rule-based parser for intent and entities across supported languages."""
    norm = normalize_text(prompt)
    if not norm:
        return ParsedMessage(intent="unknown", confidence=1.0)

    for pack in ALL_PACKS:
        if pack.greeting_pattern.match(norm):
            return ParsedMessage(intent="greeting", confidence=0.95)

    for pack in ALL_PACKS:
        has_order = bool(pack.order_keywords.search(norm))
        has_stock = bool(pack.stock_keywords.search(norm))
        if not has_order and not has_stock:
            continue

        if has_order and has_stock and pack.conflict_question_token in norm:
            return ParsedMessage(intent="unknown", confidence=0.4)

        candidate_intent: IntentType = "order" if has_order else "stock_query"
        client = extract_client_name(prompt, (pack,)) or extract_client_name(prompt)
        quantity, product = _extract_for_pack(
            _TRAILING_PUNCTUATION.sub("", norm).strip(), candidate_intent, pack
        )

        if not product:
            # Intent is clear but details are missing: the dialogue layer asks for them.
            return ParsedMessage(
                intent=candidate_intent,
                confidence=0.6,
                entities=ExtractedEntities(product=None, quantity=quantity, client=client),
            )

        return ParsedMessage(
            intent=candidate_intent,
            confidence=0.9,
            entities=ExtractedEntities(product=product, quantity=quantity, client=client),
        )

    return ParsedMessage(intent="unknown", confidence=0.9)


def is_cancel_request(text: str, packs: tuple[LanguagePack, ...] = ALL_PACKS) -> bool:
    """Return True if the message asks to abandon the current request."""
    norm = normalize_text(text)
    return any(pack.cancel_pattern.search(norm) for pack in packs)


def _answer_for_pack(norm_clean: str, pack: LanguagePack) -> tuple[int | None, str]:
    """Split a bare clarification answer into (leading quantity, remaining text)."""
    body = pack.answer_prefix_pattern.sub("", norm_clean, count=1)
    body = pack.stopwords_tail.sub("", body)
    body = re.sub(r"\s+", " ", pack.unit_words_pattern.sub(" ", body)).strip()

    numeral = pack.leading_numeral_pattern.match(f"{body} ")
    if numeral:
        qty = parse_quantity_text(numeral.group(1), pack.numerals)
        return qty, body[numeral.end():].strip()
    return None, body


def _is_usable_product(candidate: str) -> bool:
    return bool(
        candidate
        and re.search(r"[a-z]", candidate)
        and len(candidate.split()) <= MAX_PRODUCT_ANSWER_WORDS
        and candidate not in ALL_AMBIGUOUS_PRODUCT_WORDS
    )


def extract_slot_answer(
    text: str, missing: list[SlotName], packs: tuple[LanguagePack, ...] = ALL_PACKS
) -> tuple[int | None, str | None]:
    """Extract missing slots from a short clarification answer such as "5" or "3 laptops".

    Only slots listed in ``missing`` are returned; questions are never taken as answers.
    """
    if not text or "?" in text:
        return None, None
    norm_clean = re.sub(r"\s+", " ", re.sub(r"[!.,;:]", " ", normalize_text(text))).strip()
    if not norm_clean:
        return None, None

    results = [_answer_for_pack(norm_clean, pack) for pack in packs]
    # Prefer the pack that recognised a quantity, otherwise the one that stripped the most filler.
    qty, rest = next(
        ((q, r) for q, r in results if q is not None),
        min(results, key=lambda item: len(item[1])),
    )

    quantity = qty if "quantity" in missing else None
    product = rest if "product" in missing and _is_usable_product(rest) else None
    return quantity, product
