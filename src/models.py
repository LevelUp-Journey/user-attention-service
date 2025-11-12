from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class Suggestion(SQLModel, table=True):
    __tablename__ = "suggestions"
    id: Optional[int] = Field(default=None, primary_key=True)
    comment: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_solved: bool = Field(default=False)


class CreateSuggestion(SQLModel):
    comment: str = Field(max_length=255)


class CommonHeader(BaseModel):
    Authorization: str = Field(max_length=255)
