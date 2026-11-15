from typing import Literal
from pydantic import BaseModel, Field

IntentType = Literal["comanda", "interogare_stoc", "salut", "necunoscut"]
ParserSource = Literal["openrouter", "fallback"]


class NaturalLanguagePrompt(BaseModel):
    prompt: str


class ExtractedEntities(BaseModel):
    product: str | None = Field(default=None, description="Detected product name")
    quantity: int | None = Field(default=None, description="Detected product quantity")
    client: str | None = Field(default=None, description="Detected client full name")


class ParsedMessage(BaseModel):
    intent: IntentType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    entities: ExtractedEntities = Field(default_factory=ExtractedEntities)
    source: ParserSource = Field(default="fallback")


class CommandResponse(BaseModel):
    received_prompt: str
    intent: IntentType
    confidence: float
    entities: ExtractedEntities
    source: ParserSource
    reply: str
