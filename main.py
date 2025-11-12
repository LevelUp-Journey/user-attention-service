from typing import Annotated

from fastapi import Depends, FastAPI, Header
from sqlmodel import Session
from sqlmodel.main import SQLModel

from src.db_config import engine
from src.jwt import get_current_user
from src.models import CommonHeader, CreateSuggestion, Suggestion

app = FastAPI(title="User Attention Service")


# Configuration for database
@app.on_event("startup")
async def startup():
    SQLModel.metadata.create_all(engine)
    print("Database tables created")


@app.get("/")
def read_root():
    return {"hello": "world"}


@app.post("/suggestions")
def create_suggestion(
    suggestion: CreateSuggestion, user_id: str = Depends(get_current_user)
):
    with Session(engine) as session:
        db_suggestion = Suggestion(comment=suggestion.comment)

        session.add(db_suggestion)
        session.commit()

        session.refresh(db_suggestion)

        return {"data": db_suggestion}


@app.get("/suggestions")
def read_suggestions(headers: Annotated[CommonHeader, Header()]):
    with Session(engine) as session:
        db_suggestions = session.query(Suggestion).all()
        return {"data": db_suggestions, "headers": headers}
