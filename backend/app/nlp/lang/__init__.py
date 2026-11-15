"""Language-specific NLP rule packs registry."""

from app.nlp.lang.base import LanguagePack
from app.nlp.lang.en import EN_PACK
from app.nlp.lang.ro import RO_PACK

LANGUAGE_PACKS: dict[str, LanguagePack] = {
    "ro": RO_PACK,
    "en": EN_PACK,
}

ALL_PACKS: tuple[LanguagePack, ...] = (RO_PACK, EN_PACK)
ALL_NUMERALS: dict[str, int] = {**EN_PACK.numerals, **RO_PACK.numerals}
ALL_AMBIGUOUS_PRODUCT_WORDS: frozenset[str] = (
    RO_PACK.ambiguous_product_words | EN_PACK.ambiguous_product_words
)

__all__ = [
    "ALL_AMBIGUOUS_PRODUCT_WORDS",
    "ALL_NUMERALS",
    "ALL_PACKS",
    "EN_PACK",
    "LANGUAGE_PACKS",
    "LanguagePack",
    "RO_PACK",
]
