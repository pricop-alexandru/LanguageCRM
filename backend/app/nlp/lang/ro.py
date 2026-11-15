"""Romanian NLP language pack: numerals, stopwords, and regex patterns."""

import re
from app.nlp.lang.base import LanguagePack

_NUM_WORDS = "un|o|unu|una|doi|doua|trei|patru|cinci|sase|sapte|opt|noua|zece"

RO_PACK = LanguagePack(
    code="ro",
    numerals={
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
    },
    ambiguous_product_words=frozenset(
        {
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
    ),
    greeting_pattern=re.compile(
        r"^(salut(?:are)?|buna(?:\s+ziua|\s+dimineata|\s+seara)?|hello|hey|servus|neata)\b[!.?\s]*$",
        re.IGNORECASE,
    ),
    stock_keywords=re.compile(
        r"\b(stoc(?:ul|uri)?|disponibil(?:e|itate)?|cate|cati|aveti|mai\s+aveti|exista\s+in\s+stoc|in\s+stoc)\b",
        re.IGNORECASE,
    ),
    order_keywords=re.compile(
        r"\b(comand(?:a|am)?|vreau\s+sa\s+(?:comand|cumpar|iau)|as\s+dori\s+sa\s+(?:comand|cumpar)|creeaza\s+(?:o\s+)?comanda|adauga\s+(?:o\s+)?comanda|cumpar(?:a)?|plaseaza\s+(?:o\s+)?comanda)\b",
        re.IGNORECASE,
    ),
    conflict_question_token="cate",
    order_noun_prefix="comanda",
    stopwords_tail=re.compile(
        r"\s+\b(?:pentru(?:\s+clientul)?|pe\s+numele|client(?:ul)?|in\s+stoc|pe\s+stoc|disponibil(?:e)?|acum|va\s+rog|te\s+rog|multumesc)\b.*$",
        re.IGNORECASE,
    ),
    client_patterns=(
        re.compile(
            r"\b(?:[Pp]entru(?:\s+clientul)?|[Pp]e\s+numele|[Cc]lient(?:ul)?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})"
        ),
        re.compile(r"\b(?:[Ss]unt|[Mm]a\s+numesc)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})"),
    ),
    qty_product_pattern=re.compile(
        rf"\b(?:comand(?:a)?(?:\s+de)?|cumpar(?:a)?|vreau|dori|aveti|cate|cati)\s+(?:de\s+)?(\d+|{_NUM_WORDS})\s+(?:bucati\s+de\s+|buc\s+)?([a-z0-9][a-z0-9\s\-]*)",
        re.IGNORECASE,
    ),
    order_of_qty_product_pattern=re.compile(
        rf"\bcomanda\s+de\s+(\d+|{_NUM_WORDS})\s+(?:bucati\s+de\s+)?([a-z0-9][a-z0-9\s\-]*)",
        re.IGNORECASE,
    ),
    stock_patterns=(
        re.compile(
            r"\bcate\s+([a-z0-9][a-z0-9\s\-]*?)\s+(?:mai\s+)?(?:aveti|sunt|exista)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:mai\s+)?aveti\s+([a-z0-9][a-z0-9\s\-]*?)(?:\s+in\s+stoc|\s+pe\s+stoc|\s+disponibil(?:e)?)?$",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bstoc(?:ul)?\s+(?:pentru|la|de)\s+([a-z0-9][a-z0-9\s\-]*)$",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bdisponibilitate\s+(?:pentru|la)\s+([a-z0-9][a-z0-9\s\-]*)$",
            re.IGNORECASE,
        ),
    ),
    leading_numeral_pattern=re.compile(rf"^(\d+|{_NUM_WORDS})\s+", re.IGNORECASE),
    order_product_pattern=re.compile(
        r"\b(?:comand(?:a\s+de)?|cumpar)\s+([a-z0-9][a-z0-9\s\-]*)",
        re.IGNORECASE,
    ),
)
