"""Data structure defining a language-specific NLP rule pack."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class LanguagePack:
    code: str
    numerals: dict[str, int]
    ambiguous_product_words: frozenset[str]
    greeting_pattern: re.Pattern[str]
    stock_keywords: re.Pattern[str]
    order_keywords: re.Pattern[str]
    conflict_question_token: str
    order_noun_prefix: str
    stopwords_tail: re.Pattern[str]
    client_patterns: tuple[re.Pattern[str], ...]
    qty_product_pattern: re.Pattern[str]
    order_of_qty_product_pattern: re.Pattern[str]
    stock_patterns: tuple[re.Pattern[str], ...]
    leading_numeral_pattern: re.Pattern[str]
    order_product_pattern: re.Pattern[str]
