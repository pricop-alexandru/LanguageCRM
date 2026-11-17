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
    # Clarification dialogue rules (US-04)
    cancel_pattern: re.Pattern[str]
    qty_only_pattern: re.Pattern[str]
    answer_prefix_pattern: re.Pattern[str]
    unit_words_pattern: re.Pattern[str]
    # Answers to "who is the order for?": optional lead-in before the name, and
    # words that show the reply is not a name (e.g. "multumesc frumos").
    client_answer_prefix_pattern: re.Pattern[str]
    non_name_pattern: re.Pattern[str]
    # Client creation rules (US-05)
    add_client_keywords: re.Pattern[str]
    # Name right after "client"/"customer" in lowercase text, e.g. "adauga clientul ion popescu".
    new_client_name_pattern: re.Pattern[str]
    # Words that label contact details ("telefon", "email", ...), removed before reading a name.
    contact_label_pattern: re.Pattern[str]
