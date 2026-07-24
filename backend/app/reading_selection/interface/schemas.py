"""Pydantic schemas for Reading Selection endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RunDrawRequest(BaseModel):
    """Request body for POST /groups/{id}/draws."""

    participant_ids: list[UUID] = Field(..., min_length=1)
    genre: str | None = None
    max_pages: int | None = Field(default=None, ge=1)
    unread_only: bool = False


class DrawResponse(BaseModel):
    """Response for a Draw result.

    Never includes file_ref (Property 3).
    """

    id: UUID
    group_id: UUID
    filters: dict
    participants: list[UUID]
    result_book_id: UUID | None
    result_source_user_id: UUID | None
    timestamp: datetime

    model_config = {"from_attributes": True}


class NextPickerResponse(BaseModel):
    """Response for who picks next in pick-by-turn."""

    next_picker_user_id: UUID | None
