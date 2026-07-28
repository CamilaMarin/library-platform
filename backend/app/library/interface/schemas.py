"""Pydantic schemas for Library endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.library.domain.entities import Copy


class CreateBookRequest(BaseModel):
    """Request body for POST /books."""

    title: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=500)
    genres: list[str] = Field(default_factory=list)
    description: str = ""
    pages: int | None = Field(default=None, ge=1)
    isbn: str | None = Field(default=None, max_length=20)
    initial_copy_format: str | None = Field(default=None)


class UpdateBookRequest(BaseModel):
    """Request body for PATCH /books/{id}. All fields optional."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    author: str | None = Field(default=None, min_length=1, max_length=500)
    genres: list[str] | None = None
    description: str | None = None
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


class CopyResponse(BaseModel):
    """Response for a Copy entity.

    Note: file_ref is NEVER included in API responses (ADR-0009 Property 2).
    """

    id: UUID
    user_id: UUID
    book_id: UUID
    type: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_copy(cls, copy: Copy) -> "CopyResponse":
        return cls(
            id=copy.id,
            user_id=copy.user_id,
            book_id=copy.book_id,
            type=copy.type.value,
            status=copy.status.value,
            created_at=copy.created_at,
        )
