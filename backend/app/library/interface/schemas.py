"""Pydantic schemas for Library endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateBookRequest(BaseModel):
    """Request body for POST /books."""

    title: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=500)
    genres: list[str] = Field(default_factory=list)
    description: str = ""
    pages: int | None = Field(default=None, ge=1)
    isbn: str | None = Field(default=None, max_length=20)


class BookResponse(BaseModel):
    """Response for a Book entity."""

    id: UUID
    title: str
    author: str
    genres: list[str]
    description: str
    pages: int | None
    isbn: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
