import re

from app.nlp.lang import ALL_PACKS, LanguagePack
from app.nlp.normalizer import normalize_text, parse_quantity_text, strip_diacritics
from app.schemas import ExtractedEntities, IntentType, ParsedMessage


def extract_client_name(original_text: str, packs: tuple[LanguagePack, ...] = ALL_PACKS) -> str | None:
    """Extract client full name using configured language pack patterns."""
    ascii_text = strip_diacritics(original_text)
    for pack in packs:
        for pattern in pack.client_patterns:
            match = pattern.search(ascii_text)
            if match:
                return match.group(1).strip()
    return None


def _extract_for_pack(
    norm_clean: str, intent: IntentType, pack: LanguagePack
) -> tuple[int | None, str | None]:
    """Attempt quantity and product extraction using a single language pack."""
    # 1. Explicit quantity + product phrasing
    match = pack.qty_product_pattern.search(norm_clean)
    if match:
        qty_raw, prod_raw = match.group(1), match.group(2)
        prod_clean = pack.stopwords_tail.sub("", prod_raw).strip()
        if not prod_clean.startswith(pack.order_noun_prefix):
            qty = parse_quantity_text(qty_raw, pack.numerals)
            if prod_clean and prod_clean not in pack.ambiguous_product_words:
                return qty, prod_clean

    # 2. "order of <qty> <product>" phrasing
    after_order = pack.order_of_qty_product_pattern.search(norm_clean)
    if after_order:
        qty = parse_quantity_text(after_order.group(1), pack.numerals)
        prod_clean = pack.stopwords_tail.sub("", after_order.group(2)).strip()
        if prod_clean and prod_clean not in pack.ambiguous_product_words:
            return qty, prod_clean

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
            if prod_clean and prod_clean not in pack.ambiguous_product_words:
                return None, prod_clean

    return None, None


def extract_quantity_and_product(
    original_text: str, intent: IntentType, packs: tuple[LanguagePack, ...] = ALL_PACKS
) -> tuple[int | None, str | None]:
    """Extract quantity and product name across configured language packs."""
    norm = normalize_text(original_text)
    norm_clean = re.sub(r"[?!.,;:]+$", "", norm).strip()
    for pack in packs:
        qty, product = _extract_for_pack(norm_clean, intent, pack)
        if product is not None:
            return qty, product
    return None, None


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
            re.sub(r"[?!.,;:]+$", "", norm).strip(), candidate_intent, pack
        )

        if not product:
            return ParsedMessage(
                intent="unknown",
                confidence=0.45,
                entities=ExtractedEntities(product=None, quantity=quantity, client=client),
            )

        return ParsedMessage(
            intent=candidate_intent,
            confidence=0.9,
            entities=ExtractedEntities(product=product, quantity=quantity, client=client),
        )

    return ParsedMessage(intent="unknown", confidence=0.9)
