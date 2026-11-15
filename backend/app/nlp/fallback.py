import re
from app.nlp.normalizer import normalize_text, parse_quantity_text, strip_diacritics
from app.nlp.ro_locale import (
    AMBIGUOUS_PRODUCT_WORDS,
    CLIENT_PATTERNS,
    GREETING_PATTERNS,
    ORDER_KEYWORDS,
    STOCK_KEYWORDS,
    STOPWORDS_TAIL,
)
from app.schemas import ExtractedEntities, IntentType, ParsedMessage


def extract_client_name(original_text: str) -> str | None:
    """Extract client name from standard customer/operator phrasing."""
    ascii_text = strip_diacritics(original_text)
    for pattern in CLIENT_PATTERNS:
        match = re.search(pattern, ascii_text)
        if match:
            return match.group(1).strip()
    return None


def extract_quantity_and_product(original_text: str, intent: IntentType) -> tuple[int | None, str | None]:
    """Extract quantity and product name from order or stock query phrasings."""
    norm = normalize_text(original_text)
    norm_clean = re.sub(r"[?!.,;:]+$", "", norm).strip()

    # 1. Explicit quantity + product pattern: e.g. "de 3 laptopuri", "comand 2 monitoare", "un laptop"
    num_words = "un|o|unu|una|doi|doua|trei|patru|cinci|sase|sapte|opt|noua|zece"
    qty_prod_pattern = re.compile(
        rf"\b(?:comand(?:a)?(?:\s+de)?|cumpar(?:a)?|vreau|dori|aveti|cate|cati)\s+(?:de\s+)?(\d+|{num_words})\s+(?:bucati\s+de\s+|buc\s+)?([a-z0-9][a-z0-9\s\-]*)",
        re.IGNORECASE,
    )
    match = qty_prod_pattern.search(norm_clean)
    if match:
        qty_raw, prod_raw = match.group(1), match.group(2)
        prod_clean = STOPWORDS_TAIL.sub("", prod_raw).strip()
        # Avoid treating "o comanda de 3 laptopuri" as qty=1, product="comanda..."
        if not prod_clean.startswith("comanda"):
            qty = parse_quantity_text(qty_raw)
            if prod_clean and prod_clean not in AMBIGUOUS_PRODUCT_WORDS:
                return qty, prod_clean

    # 2. "comanda de <qty> <product>" or "<qty> <product>"
    after_de = re.search(
        rf"\bcomanda\s+de\s+(\d+|{num_words})\s+(?:bucati\s+de\s+)?([a-z0-9][a-z0-9\s\-]*)",
        norm_clean,
    )
    if after_de:
        qty = parse_quantity_text(after_de.group(1))
        prod_clean = STOPWORDS_TAIL.sub("", after_de.group(2)).strip()
        if prod_clean and prod_clean not in AMBIGUOUS_PRODUCT_WORDS:
            return qty, prod_clean

    # 3. Stock query patterns: "cate <product> aveti", "aveti <product> in stoc", "stoc pentru <product>"
    if intent == "interogare_stoc":
        stock_patterns = [
            r"\bcate\s+([a-z0-9][a-z0-9\s\-]*?)\s+(?:mai\s+)?(?:aveti|sunt|exista)\b",
            r"\b(?:mai\s+)?aveti\s+([a-z0-9][a-z0-9\s\-]*?)(?:\s+in\s+stoc|\s+pe\s+stoc|\s+disponibil(?:e)?)?$",
            r"\bstoc(?:ul)?\s+(?:pentru|la|de)\s+([a-z0-9][a-z0-9\s\-]*)$",
            r"\bdisponibilitate\s+(?:pentru|la)\s+([a-z0-9][a-z0-9\s\-]*)$",
        ]
        for pat in stock_patterns:
            m = re.search(pat, norm_clean)
            if m:
                prod_clean = STOPWORDS_TAIL.sub("", m.group(1)).strip()
                qty = parse_quantity_text(prod_clean)
                if qty is not None:
                    prod_clean = re.sub(rf"^(\d+|{num_words})\s+", "", prod_clean).strip()
                if prod_clean and prod_clean not in AMBIGUOUS_PRODUCT_WORDS:
                    return qty, prod_clean

    # 4. Order without quantity or with product after "comand / cumpar"
    if intent == "comanda":
        order_prod = re.search(
            r"\b(?:comand(?:a\s+de)?|cumpar)\s+([a-z0-9][a-z0-9\s\-]*)",
            norm_clean,
        )
        if order_prod:
            prod_clean = STOPWORDS_TAIL.sub("", order_prod.group(1)).strip()
            if prod_clean and prod_clean not in AMBIGUOUS_PRODUCT_WORDS:
                return None, prod_clean

    return None, None


def fallback_parse_message(prompt: str) -> ParsedMessage:
    """Deterministic Romanian rule-based parser for intent and entities."""
    norm = normalize_text(prompt)
    if not norm:
        return ParsedMessage(intent="necunoscut", confidence=1.0)

    if GREETING_PATTERNS.match(norm):
        return ParsedMessage(intent="salut", confidence=0.95)

    has_order = bool(ORDER_KEYWORDS.search(norm))
    has_stock = bool(STOCK_KEYWORDS.search(norm))

    # Conflicting intents in same short utterance -> ambiguous
    if has_order and has_stock and "cate" in norm:
        return ParsedMessage(intent="necunoscut", confidence=0.4)

    candidate_intent: IntentType = "necunoscut"
    if has_order:
        candidate_intent = "comanda"
    elif has_stock:
        candidate_intent = "interogare_stoc"

    if candidate_intent == "necunoscut":
        return ParsedMessage(intent="necunoscut", confidence=0.9)

    client = extract_client_name(prompt)
    quantity, product = extract_quantity_and_product(prompt, candidate_intent)

    # Ambiguity guardrail: an order or stock query without a clear product is unknown
    if not product:
        return ParsedMessage(
            intent="necunoscut",
            confidence=0.45,
            entities=ExtractedEntities(product=None, quantity=quantity, client=client),
        )

    return ParsedMessage(
        intent=candidate_intent,
        confidence=0.9,
        entities=ExtractedEntities(product=product, quantity=quantity, client=client),
    )
