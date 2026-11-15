from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import init_db

app = FastAPI(title="LanguageCRM API")

# Permite frontend-ului TypeScript sa comunice cu backend-ul
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

class NaturalLanguagePrompt(BaseModel):
    prompt: str

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "LanguageCRM Backend"}

@app.post("/api/command")
def process_command(data: NaturalLanguagePrompt):
    # TODO pentru echipa: De legat parserul NLP / LLM-ul si SQLAlchemy
    return {
        "received_prompt": data.prompt,
        "reply": f"[Schelet functional] Am primit comanda: '{data.prompt}'. Urmeaza procesarea in DB."
    }