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
