from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.conversation import ConversationStore, get_conversation_store
from app.client_service import ClientIdentityConflictError, resolve_or_create_client
from app.database import get_db, init_db
from app.dialogue import handle_turn
from app.schemas import (
    ClientResolutionRequest,
    ClientResolutionResponse,
    CommandResponse,
    NaturalLanguagePrompt,
)

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


@app.post("/api/clients/resolve", response_model=ClientResolutionResponse)
def resolve_client(
    data: ClientResolutionRequest, db: Session = Depends(get_db)
) -> ClientResolutionResponse:
    try:
        result = resolve_or_create_client(db, data.name, data.phone)
    except ClientIdentityConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(
            status_code=404, detail="No client matches the supplied phone number"
        )

    client, created = result
    return ClientResolutionResponse(
        id=client.id,
        name=client.name,
        email=client.email,
        phone=client.phone,
        created=created,
    )


@app.post("/api/command", response_model=CommandResponse)
def process_command(
    data: NaturalLanguagePrompt,
    store: ConversationStore = Depends(get_conversation_store),
) -> CommandResponse:
    return handle_turn(data.prompt, data.locale, data.conversation_id, store)
