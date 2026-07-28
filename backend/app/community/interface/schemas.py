"""Pydantic schemas for Community (Clubs) endpoints.

Reference: ADR-0006, clubs/requirements.md
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateClubRequest(BaseModel):
    """Request body for POST /clubs."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    group_id: UUID | None = None


class ClubResponse(BaseModel):
    """Response for a Club entity."""

    id: UUID
    name: str
    description: str | None
    group_id: UUID
    active_book_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClubMemberResponse(BaseModel):
    """Response for a club member (inherited from group membership)."""

    id: UUID
    user_id: UUID
    club_id: UUID
    name: str
    role: str
    created_at: datetime


class PostCommentRequest(BaseModel):
    """Request body for POST /clubs/{club_id}/comments."""

    text: str = Field(..., min_length=1, max_length=5000)
    is_spoiler: bool = False


class CommentResponse(BaseModel):
    """Response for a Comment entity."""

    id: UUID
    user_id: UUID
    text: str
    is_spoiler: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SetActiveBookRequest(BaseModel):
    """Request body for POST /clubs/{club_id}/active-book."""

    book_id: UUID


class AvailableBookResponse(BaseModel):
    """Response for an available book (metadata only, no file_ref)."""

    id: UUID
    title: str
    author: str

    model_config = {"from_attributes": True}
