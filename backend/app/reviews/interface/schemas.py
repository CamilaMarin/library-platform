"""Pydantic schemas for Reviews endpoints.

Reference: ADR-0007, reviews/requirements.md Req 1.1, 1.2, 1.3, 1.5
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.reviews.domain.entities import SharedWithType, Visibility


class CreateReviewRequest(BaseModel):
    """Request body for POST /reviews.

    visibility is REQUIRED — never defaults (Req 1.5).
    When visibility is 'shared', shared_with_type and shared_with_id are required (Req 1.3).
    """

    book_id: UUID
    rating: int = Field(..., ge=1, le=5)
    visibility: Visibility
    text: str | None = Field(default=None, max_length=5000)
    shared_with_type: SharedWithType | None = None
    shared_with_id: UUID | None = None

    @model_validator(mode="after")
    def validate_visibility_target(self) -> "CreateReviewRequest":
        """Enforce visibility invariants at the API boundary."""
        if self.visibility == Visibility.SHARED:
            if self.shared_with_type is None or self.shared_with_id is None:
                raise ValueError(
                    "shared_with_type and shared_with_id are required when visibility is 'shared'"
                )
        if self.visibility == Visibility.PRIVATE:
            if self.shared_with_type is not None or self.shared_with_id is not None:
                raise ValueError(
                    "shared_with_type and shared_with_id must be null when visibility is 'private'"
                )
        return self


class ReviewResponse(BaseModel):
    """Response for a Review entity."""

    id: UUID
    user_id: UUID
    book_id: UUID
    rating: int
    text: str | None
    visibility: str
    shared_with_type: str | None
    shared_with_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UpdateReviewRequest(BaseModel):
    """Request body for PATCH /reviews/{id}.

    All fields are optional — partial update.
    Visibility invariants are enforced: if changing to 'shared',
    shared_with_type and shared_with_id become required.
    """

    rating: int | None = Field(default=None, ge=1, le=5)
    text: str | None = Field(default=None, max_length=5000)
    visibility: Visibility | None = None
    shared_with_type: SharedWithType | None = None
    shared_with_id: UUID | None = None

    @model_validator(mode="after")
    def validate_visibility_target(self) -> "UpdateReviewRequest":
        """Enforce visibility invariants when visibility is explicitly changed."""
        if self.visibility == Visibility.SHARED:
            if self.shared_with_type is None or self.shared_with_id is None:
                raise ValueError(
                    "shared_with_type and shared_with_id are required when visibility is 'shared'"
                )
        if self.visibility == Visibility.PRIVATE:
            if self.shared_with_type is not None or self.shared_with_id is not None:
                raise ValueError(
                    "shared_with_type and shared_with_id must be null when visibility is 'private'"
                )
        return self
