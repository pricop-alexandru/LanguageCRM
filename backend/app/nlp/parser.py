import logging
import os
from typing import Any
import httpx

from app.locales import get_messages
from app.nlp.fallback import (
    extract_client_name,
    extract_quantity_and_product,
    fallback_parse_message,
)
from app.nlp.lang import ALL_AMBIGUOUS_PRODUCT_WORDS
from app.nlp.normalizer import normalize_text
from app.schemas import ExtractedEntities, IntentType, ParsedMessage

logger = logging.getLogger(__name__)

OPENROUTER_DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_DECIDER_MODEL = "perplexity/pplx-decider-flash-v1.3:free"
HTTP_TIMEOUT_SECONDS = 3.0
MIN_CONFIDENCE_THRESHOLD = 0.55
AMBIGUITY_PROB_THRESHOLD = 0.85

VALID_INTENTS: set[str] = {"order", "stock_query", "greeting", "unknown"}


def build_decider_payload(prompt: str, model: str) -> dict[str, Any]:
    """Build the OpenRouter Decisions API payload for pplx-decider."""
    return {
        "model": model,
        "state": prompt,
        "questions": {
            "intent": {
                "type": "choice",
                "instructions": (
                    "Classify the customer message intent (supports English and Romanian with or without diacritics)."
                ),
                "criteria": {
                    "order": (
                        "The customer or operator wants to place an order, buy, or purchase a product."
                    ),
                    "stock_query": (
                        "The user asks about stock availability, how many units are available, or if a product is in stock."
                    ),
                    "greeting": (
                        "The message is solely a greeting without an order or stock inquiry."
                    ),
                    "unknown": (
                        "The message is ambiguous, off-topic, unclear, or does not fit order, stock_query, or greeting."
                    ),
                },
            },
            "is_ambiguous": {
                "type": "noul",
                "instructions": (
                    "Answer yes ONLY if the message is completely vague or off-topic and cannot be understood as a greeting, stock check, or product order."
                ),
            },
        },
    }


def _extract_ambiguity_prob(answer: dict[str, Any] | None) -> float:
    """Extract the 'yes/true' probability from a Decider 'noul' answer."""
    if not isinstance(answer, dict):
        return 0.0
    for key in ("noul", "probability"):
        if isinstance(answer.get(key), (int, float)):
            return float(answer[key])
    probs = answer.get("probabilities")
    if isinstance(probs, dict):
        for key in ("true", "yes", "1"):
            if isinstance(probs.get(key), (int, float)):
                return float(probs[key])
    return 0.0


def parse_decider_response(prompt: str, data: dict[str, Any]) -> ParsedMessage:
    """Convert raw OpenRouter Decisions API JSON into a validated ParsedMessage."""
    answers = data.get("answers")
    if not isinstance(answers, dict):
        raise ValueError("Missing 'answers' in OpenRouter Decisions API response")

    intent_ans = answers.get("intent") or {}
    raw_choice = intent_ans.get("choice", "unknown")
    intent: IntentType = raw_choice if raw_choice in VALID_INTENTS else "unknown"  # type: ignore[assignment]
    confidence = float(intent_ans.get("confidence", 0.0) or 0.0)

    is_ambiguous_prob = _extract_ambiguity_prob(answers.get("is_ambiguous"))

    client = extract_client_name(prompt)
    quantity, product = extract_quantity_and_product(prompt, intent)
    if product and normalize_text(product) in ALL_AMBIGUOUS_PRODUCT_WORDS:
        product = None

    entities = ExtractedEntities(product=product, quantity=quantity, client=client)

    # Ambiguity & confidence guardrails:
    if is_ambiguous_prob >= AMBIGUITY_PROB_THRESHOLD or confidence < MIN_CONFIDENCE_THRESHOLD:
        return ParsedMessage(
            intent="unknown", confidence=confidence, entities=entities, source="openrouter"
        )

    return ParsedMessage(
        intent=intent, confidence=confidence, entities=entities, source="openrouter"
    )


def call_openrouter_decider(prompt: str, api_key: str, model: str) -> ParsedMessage:
    """Send state and questions to OpenRouter Decisions API and parse the result."""
    payload = build_decider_payload(prompt=prompt, model=model)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as client:
        response = client.post(OPENROUTER_DECISIONS_URL, json=payload, headers=headers)
        response.raise_for_status()
        return parse_decider_response(prompt, response.json())


def parse_message(prompt: str) -> ParsedMessage:
    """Parse a customer message using OpenRouter Decider with deterministic fallback."""
    if not prompt or not prompt.strip():
        return ParsedMessage(intent="unknown", confidence=1.0)

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    model = os.getenv("OPENROUTER_DECIDER_MODEL", DEFAULT_DECIDER_MODEL).strip() or DEFAULT_DECIDER_MODEL

    if api_key:
        try:
            return call_openrouter_decider(prompt=prompt, api_key=api_key, model=model)
        except Exception as exc:
            logger.warning("OpenRouter Decider call failed (%s); falling back to local parser.", exc)
            return fallback_parse_message(prompt)

    return fallback_parse_message(prompt)


def format_reply(parsed: ParsedMessage, locale: str = "ro") -> str:
    """Generate a localized reply summarizing the detected intent and entities."""
    replies = get_messages(locale)
    if parsed.intent == "greeting":
        return replies["greeting"]
    if parsed.intent == "order":
        if not parsed.entities.product:
            return replies["order_missing_product"]
        qty_str = f"{parsed.entities.quantity}x " if parsed.entities.quantity else ""
        client_str = (
            replies["order_client_prefix"].format(client=parsed.entities.client)
            if parsed.entities.client
            else ""
        )
        return replies["order_summary"].format(
            qty=qty_str,
            product=parsed.entities.product,
            client=client_str,
        )
    if parsed.intent == "stock_query":
        if not parsed.entities.product:
            return replies["stock_query_missing_product"]
        return replies["stock_query_summary"].format(product=parsed.entities.product)
    return replies["unknown"]
