"""Romanian language constants, NLP patterns, and user-facing reply templates."""

import re

ROMANIAN_NUMERALS: dict[str, int] = {
    "un": 1,
    "o": 1,
    "unu": 1,
    "una": 1,
    "doi": 2,
    "doua": 2,
    "trei": 3,
    "patru": 4,
    "cinci": 5,
    "sase": 6,
    "sapte": 7,
    "opt": 8,
    "noua": 9,
    "zece": 10,
    "unsprezece": 11,
    "doisprezece": 12,
    "douasprezece": 12,
    "douazeci": 20,
}

AMBIGUOUS_PRODUCT_WORDS: set[str] = {
    "ceva",
    "nimic",
    "produse",
    "produs",
    "articole",
    "chestii",
    "lucruri",
    "comanda",
    "stoc",
    "in stoc",
    "pe stoc",
}

GREETING_PATTERNS = re.compile(
    r"^(salut(?:are)?|buna(?:\s+ziua|\s+dimineata|\s+seara)?|hello|hey|servus|neata)\b[!.?\s]*$",
    re.IGNORECASE,
)

STOCK_KEYWORDS = re.compile(
    r"\b(stoc(?:ul|uri)?|disponibil(?:e|itate)?|cate|cati|aveti|mai\s+aveti|exista\s+in\s+stoc|in\s+stoc)\b",
    re.IGNORECASE,
)

ORDER_KEYWORDS = re.compile(
    r"\b(comand(?:a|am)?|vreau\s+sa\s+(?:comand|cumpar|iau)|as\s+dori\s+sa\s+(?:comand|cumpar)|creeaza\s+(?:o\s+)?comanda|adauga\s+(?:o\s+)?comanda|cumpar(?:a)?|plaseaza\s+(?:o\s+)?comanda)\b",
    re.IGNORECASE,
)

STOPWORDS_TAIL = re.compile(
    r"\s+\b(?:pentru(?:\s+clientul)?|pe\s+numele|client(?:ul)?|in\s+stoc|pe\s+stoc|disponibil(?:e)?|acum|va\s+rog|te\s+rog|multumesc)\b.*$",
    re.IGNORECASE,
)

CLIENT_PATTERNS: tuple[str, ...] = (
    r"\b(?:[Pp]entru(?:\s+clientul)?|[Pp]e\s+numele|[Cc]lient(?:ul)?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
    r"\b(?:[Ss]unt|[Mm]a\s+numesc)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
)

REPLIES: dict[str, str] = {
    "salut": "Salut! Cu ce te pot ajuta astăzi? Poți întreba de stoc sau plasa o comandă.",
    "comanda_missing_product": "Am înțeles intenția de comandă. Te rog să specifici produsul și cantitatea dorită.",
    "comanda_summary": "Am înțeles intenția de comandă: {qty}{product}{client}.",
    "comanda_client_prefix": " pentru {client}",
    "interogare_stoc_missing_product": "Am înțeles că întrebi despre stoc. Te rog să specifici produsul.",
    "interogare_stoc_summary": "Verific stocul pentru produsul: {product}.",
    "necunoscut": (
        "Nu am putut determina intenția exactă. Te rog să specifici clar produsul "
        "și cantitatea dorită sau întrebarea despre stoc."
    ),
}
