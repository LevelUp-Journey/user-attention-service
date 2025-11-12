from typing import Annotated, Generator

from fastapi import Depends, FastAPI, Header
from sqlmodel import Session, select
from sqlmodel.main import SQLModel

from src.db_config import engine
from src.models import CommonHeader, CreateSuggestion, Suggestion

app = FastAPI(title="User Attention Service")


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


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
    suggestion: CreateSuggestion,
    session: Session = Depends(get_session),
):
    db_suggestion = Suggestion(comment=suggestion.comment)

    session.add(db_suggestion)
    session.commit()

    session.refresh(db_suggestion)

    return {"data": db_suggestion}


@app.get("/suggestions")
def read_suggestions(
    headers: Annotated[CommonHeader, Header()], session: Session = Depends(get_session)
):
    db_suggestions = session.exec(select(Suggestion)).all()
    return {"data": db_suggestions, "headers": headers}
