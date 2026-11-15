"""English NLP language pack: numerals, stopwords, and regex patterns."""

import re
from app.nlp.lang.base import LanguagePack

_NUM_WORDS = "one|a|an|two|three|four|five|six|seven|eight|nine|ten"

EN_PACK = LanguagePack(
    code="en",
    numerals={
        "a": 1,
        "an": 1,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "twenty": 20,
    },
    ambiguous_product_words=frozenset(
        {
            "something",
            "nothing",
            "anything",
            "products",
            "product",
            "items",
            "item",
            "stuff",
            "things",
            "order",
            "stock",
            "in stock",
        }
    ),
    greeting_pattern=re.compile(
        r"^(hello|hi|hey|good\s+(?:morning|afternoon|evening)|greetings)\b[!.?\s]*$",
        re.IGNORECASE,
    ),
    stock_keywords=re.compile(
        r"\b(stock|available|availability|how\s+many|do\s+you\s+have|in\s+stock)\b",
        re.IGNORECASE,
    ),
    order_keywords=re.compile(
        r"\b(order|buy|purchase|want\s+to\s+(?:order|buy)|would\s+like\s+to\s+(?:order|buy)|create\s+(?:an\s+)?order|place\s+(?:an\s+)?order)\b",
        re.IGNORECASE,
    ),
    conflict_question_token="how many",
    order_noun_prefix="order",
    stopwords_tail=re.compile(
        r"\s+\b(?:for(?:\s+client|\s+customer)?|under\s+the\s+name|client|customer|in\s+stock|available|now|please|thanks|thank\s+you)\b.*$",
        re.IGNORECASE,
    ),
    client_patterns=(
        re.compile(
            r"\b(?:[Ff]or(?:\s+client|\s+customer)?|[Cc]lient|[Cc]ustomer)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})"
        ),
        re.compile(r"\b(?:[Ii]\s+am|[Mm]y\s+name\s+is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})"),
    ),
    qty_product_pattern=re.compile(
        rf"\b(?:order(?:\s+of)?|buy|purchase|want|have|how\s+many)\s+(\d+|{_NUM_WORDS})\s+(?:units\s+of\s+|pieces\s+of\s+)?([a-z0-9][a-z0-9\s\-]*)",
        re.IGNORECASE,
    ),
    order_of_qty_product_pattern=re.compile(
        rf"\border\s+(?:of|for)\s+(\d+|{_NUM_WORDS})\s+(?:units\s+of\s+)?([a-z0-9][a-z0-9\s\-]*)",
        re.IGNORECASE,
    ),
    stock_patterns=(
        re.compile(
            r"\bhow\s+many\s+([a-z0-9][a-z0-9\s\-]*?)\s+(?:do\s+you\s+have|are\s+available|are\s+in\s+stock)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bdo\s+you\s+have\s+([a-z0-9][a-z0-9\s\-]*?)(?:\s+in\s+stock|\s+available)?$",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:stock|availability)\s+(?:for|of)\s+([a-z0-9][a-z0-9\s\-]*)$",
            re.IGNORECASE,
        ),
    ),
    leading_numeral_pattern=re.compile(rf"^(\d+|{_NUM_WORDS})\s+", re.IGNORECASE),
    order_product_pattern=re.compile(
        r"\b(?:order|buy|purchase)\s+([a-z0-9][a-z0-9\s\-]*)",
        re.IGNORECASE,
    ),
)
