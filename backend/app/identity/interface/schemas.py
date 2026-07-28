"""Pydantic request/response schemas for auth endpoints.

Reference: authentication/design.md, authentication/tasks.md#3
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """Request body for POST /auth/register."""

    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=8, max_length=128)
    consent_policy_version: str = Field(..., min_length=1, max_length=50)
    consent_purpose: str = Field(..., min_length=1)


class RegisterResponse(BaseModel):
    """Response body for successful registration."""

    id: UUID
    name: str
    email: str
    created_at: datetime


class ConsentRequest(BaseModel):
    """Request body for POST /auth/consent (standalone consent recording)."""

    user_id: UUID
    policy_version: str = Field(..., min_length=1, max_length=50)
    purpose: str = Field(..., min_length=1)


class ConsentResponse(BaseModel):
    """Response body for successful consent recording."""

    id: UUID
    user_id: UUID
    timestamp: datetime
    policy_version: str
    purpose: str


class LoginRequest(BaseModel):
    """Request body for POST /auth/login."""

    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=1, max_length=128)


class LoginResponse(BaseModel):
    """Response body for successful login."""

    access_token: str
    refresh_token: str
    token_type: str


class RefreshRequest(BaseModel):
    """Request body for POST /auth/refresh."""

    refresh_token: str = Field(..., min_length=1)


class LogoutRequest(BaseModel):
    """Request body for POST /auth/logout."""

    refresh_token: str = Field(..., min_length=1)


class CreateGroupRequest(BaseModel):
    """Request body for POST /groups."""

    name: str = Field(..., min_length=1, max_length=200)


class CreateGroupResponse(BaseModel):
    """Response body for successful group creation."""

    id: UUID
    name: str
    created_at: datetime


class InviteRequest(BaseModel):
    """Request body for POST /groups/{group_id}/invitations."""

    user_id: UUID | None = None
    email: str | None = None


class InvitationResponse(BaseModel):
    """Response body for invitation operations."""

    id: UUID
    group_id: UUID
    user_id: UUID
    status: str
    created_at: datetime


# --- ARCO / User data export schemas ---


class ExportUserProfile(BaseModel):
    """User profile section of the export response (no password_hash)."""

    name: str
    email: str
    created_at: datetime


class ExportConsentItem(BaseModel):
    """Single consent record in the export response."""

    id: UUID
    timestamp: datetime
    policy_version: str
    purpose: str


class ExportMembershipItem(BaseModel):
    """Single group membership record in the export response."""

    id: UUID
    group_id: UUID
    status: str
    created_at: datetime


class ExportProcessingRecordItem(BaseModel):
    """Single data processing record in the export response."""

    id: UUID
    data_type: str
    purpose: str
    legal_basis: str
    collected_at: datetime
    retention_expires_at: datetime | None


class ExportResponse(BaseModel):
    """Response body for GET /users/me/export — structured export of all identity-owned data."""

    user: ExportUserProfile
    consents: list[ExportConsentItem]
    memberships: list[ExportMembershipItem]
    processing_records: list[ExportProcessingRecordItem]


# --- ARCO Rectification & Opposition schemas ---


class RectifyRequest(BaseModel):
    """Request body for PATCH /users/me — rectify user data."""

    name: str | None = Field(None, min_length=1, max_length=200)
    email: str | None = Field(None, min_length=3, max_length=320)


class RectifyResponse(BaseModel):
    """Response body for successful rectification."""

    user_id: UUID
    name: str
    email: str


class OpposeRequest(BaseModel):
    """Request body for POST /users/me/oppose — oppose data processing."""

    purpose: str = Field(..., min_length=1, max_length=200)


class OpposeResponse(BaseModel):
    """Response body for successful opposition registration."""

    user_id: UUID
    processing_purpose: str
    opposed: bool
