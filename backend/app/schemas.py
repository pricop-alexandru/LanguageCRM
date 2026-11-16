from typing import Literal
from pydantic import BaseModel, Field

IntentType = Literal["order", "stock_query", "greeting", "unknown"]
ParserSource = Literal["openrouter", "fallback"]
SlotName = Literal["product", "quantity", "client"]


class NaturalLanguagePrompt(BaseModel):
    prompt: str
    locale: str = Field(default="ro", description="Language locale ('ro' or 'en')")
    conversation_id: str | None = Field(
        default=None,
        max_length=64,
        description="Conversation identifier returned by a previous response, used to continue a clarification",
    )


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
    conversation_id: str | None = Field(
        default=None, description="Conversation identifier to send back on the next turn"
    )
    needs_clarification: bool = Field(
        default=False, description="True when the chatbot is waiting for missing details"
    )
    missing_fields: list[SlotName] = Field(
        default_factory=list, description="Slots the chatbot is asking the user to provide"
    )
    order_ready: bool = Field(
        default=False, description="True when an order request is complete and ready to be placed"
    )
