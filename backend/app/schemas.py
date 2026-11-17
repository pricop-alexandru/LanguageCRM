from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.identity import normalize_email, normalize_phone

IntentType = Literal["order", "stock_query", "add_client", "greeting", "unknown"]
ParserSource = Literal["openrouter", "fallback"]
SlotName = Literal["product", "quantity", "client", "phone", "email"]


class NaturalLanguagePrompt(BaseModel):
    prompt: str
    locale: str = Field(default="ro", description="Language locale ('ro' or 'en')")
    conversation_id: str | None = Field(
        default=None,
        max_length=64,
        description="Conversation identifier returned by a previous response, used to continue a clarification",
    )


class ClientResolutionRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, min_length=1, max_length=32)
    email: str | None = Field(default=None, min_length=1, max_length=254)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name must not be blank")
        return cleaned

    @field_validator("phone")
    @classmethod
    def canonicalize_phone(cls, value: str | None) -> str | None:
        return normalize_phone(value)

    @field_validator("email")
    @classmethod
    def canonicalize_email(cls, value: str | None) -> str | None:
        return normalize_email(value)

    @model_validator(mode="after")
    def require_identifier(self) -> Self:
        if self.name is None and self.phone is None and self.email is None:
            raise ValueError("Provide a client name, phone number or email")
        return self


class ClientRecord(BaseModel):
    """A stored client as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None
    email: str | None
    phone: str | None


class ClientResolutionResponse(ClientRecord):
    created: bool


class ExtractedEntities(BaseModel):
    product: str | None = Field(default=None, description="Detected product name")
    quantity: int | None = Field(default=None, description="Detected product quantity")
    client: str | None = Field(default=None, description="Detected client full name")
    phone: str | None = Field(
        default=None, description="Detected phone number in canonical international form"
    )
    email: str | None = Field(default=None, description="Detected email address (lowercase)")


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
    client_record: ClientResolutionResponse | None = Field(
        default=None, description="The stored client, set when an add-client request completes"
    )
