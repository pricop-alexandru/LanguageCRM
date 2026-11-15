from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.nlp.parser import format_reply, parse_message
from app.schemas import CommandResponse, NaturalLanguagePrompt

app = FastAPI(title="LanguageCRM API")

# Allow the TypeScript frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "LanguageCRM Backend"}


@app.post("/api/command", response_model=CommandResponse)
def process_command(data: NaturalLanguagePrompt) -> CommandResponse:
    parsed = parse_message(data.prompt)
    reply = format_reply(parsed, locale=data.locale)
    return CommandResponse(
        received_prompt=data.prompt,
        intent=parsed.intent,
        confidence=parsed.confidence,
        entities=parsed.entities,
        source=parsed.source,
        reply=reply,
    )
