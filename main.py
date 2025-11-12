from fastapi import FastAPI
from sqlmodel import Session
from sqlmodel.main import SQLModel

from db.db_config import engine
from db.models import CreateSuggestion, Suggestion

app = FastAPI()


@app.get("/")
def read_root():
    return {"hello": "world"}


@app.post("/suggestions")
def create_suggestion(suggestion: CreateSuggestion):
    with Session(engine) as session:
        suggestion = Suggestion(comment=suggestion.comment)

        session.add(suggestion)
        session.commit()

        session.refresh(suggestion)

        return {"data": suggestion}


@app.on_event("startup")
async def startup():
    SQLModel.metadata.create_all(engine)
    print("Database tables created")
