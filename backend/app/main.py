from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.conversation import ConversationStore, get_conversation_store
from app.database import init_db
from app.dialogue import handle_turn
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
def process_command(
    data: NaturalLanguagePrompt,
    store: ConversationStore = Depends(get_conversation_store),
) -> CommandResponse:
    return handle_turn(data.prompt, data.locale, data.conversation_id, store)
