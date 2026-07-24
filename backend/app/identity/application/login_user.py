"""LoginUser use case — authenticates user and issues token pair.

Validates credentials against stored bcrypt hash, generates an Access Token
(short-lived JWT) and a Refresh Token (long-lived), stores the refresh token
hash in the database, and records an audit entry.

Reference: authentication/requirements.md Req 1.3, 2.1
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt

from app.auth.jwt import create_access_token, create_refresh_token_value
from app.config import settings
from app.identity.application.audit_service import AuditService
from app.identity.application.protocols import RefreshTokenRepository, UserRepository
from app.identity.domain.entities import AuditAction, RefreshToken


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid.

    Generic error — does not reveal whether email or password was wrong.
    Prevents user-enumeration attacks.
    """

    pass


@dataclass
class LoginUserInput:
    """Input DTO for the LoginUser use case."""

    email: str
    password: str


@dataclass
class LoginUserOutput:
    """Output DTO for the LoginUser use case."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginUser:
    """Use case: authenticate a user and issue Access + Refresh tokens.

    Enforces:
    - Secure password verification with bcrypt
    - Generic error for invalid credentials (no user-enumeration)
    - Refresh token stored as SHA-256 hash (DB compromise doesn't leak tokens)
    - Audit log for successful login
    """

    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        audit_service: AuditService,
    ):
        self._user_repo = user_repository
        self._refresh_token_repo = refresh_token_repository
        self._audit_service = audit_service

    def execute(self, input: LoginUserInput) -> LoginUserOutput:
        """Authenticate user and return token pair."""
        # Find user by email — if not found, raise generic error
        user = self._user_repo.find_by_email(input.email)
        if user is None:
            raise InvalidCredentialsError("invalid_credentials")

        # Verify password with bcrypt — if mismatch, raise generic error
        if not bcrypt.checkpw(
            input.password.encode("utf-8"),
            user.password_hash.encode("utf-8"),
        ):
            raise InvalidCredentialsError("invalid_credentials")

        # Generate Access Token (short-lived JWT)
        access_token = create_access_token(user_id=str(user.id))

        # Generate Refresh Token value (long-lived JWT)
        refresh_token_value = create_refresh_token_value(user_id=str(user.id))

        # Hash refresh token for secure storage
        token_hash = hashlib.sha256(refresh_token_value.encode()).hexdigest()

        # Store refresh token record in DB
        refresh_token_entity = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_expire_days),
        )
        self._refresh_token_repo.save(refresh_token_entity)

        # Audit log
        self._audit_service.log(
            actor_user_id=user.id,
            action=AuditAction.USER_LOGIN,
            affected_entity=f"user:{user.id}",
        )

        return LoginUserOutput(
            access_token=access_token,
            refresh_token=refresh_token_value,
            token_type="bearer",
        )
