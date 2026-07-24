"""RefreshToken use case — rotates refresh token and issues new token pair.

Validates the incoming refresh token (JWT signature + DB record), atomically
revokes the old token, stores a new one, and returns a fresh Access + Refresh
token pair.

Reference: authentication/requirements.md Req 2.3, 2.5
Design: Property 4 (rotation atomicity), Property 5 (revocation enforcement)
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt

from app.auth.jwt import create_access_token, create_refresh_token_value, verify_refresh_token
from app.config import settings
from app.identity.application.protocols import RefreshTokenRepository
from app.identity.domain.entities import RefreshToken


class TokenRevokedError(Exception):
    """Raised when a refresh token is revoked, expired, or not found.

    Generic error — does not reveal the specific reason to the caller.
    """

    pass


@dataclass
class RefreshTokenOutput:
    """Output DTO for the RefreshToken use case."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenUseCase:
    """Use case: rotate a Refresh Token and issue a new token pair.

    Enforces:
    - JWT signature verification before DB lookup
    - DB-level revocation check (revoked or expired → reject)
    - Atomic rotation: revoke old + store new in same transaction
    - SHA-256 hash storage (DB compromise doesn't leak raw tokens)
    """

    def __init__(self, refresh_token_repository: RefreshTokenRepository):
        self._refresh_token_repo = refresh_token_repository

    def execute(self, raw_token: str) -> RefreshTokenOutput:
        """Rotate the refresh token and return a new token pair.

        Args:
            raw_token: The raw JWT refresh token value from the client.

        Raises:
            TokenRevokedError: If the token is invalid, revoked, expired, or not found.
        """
        # 1. Verify JWT signature and decode
        try:
            payload = verify_refresh_token(raw_token)
        except jwt.InvalidTokenError:
            raise TokenRevokedError("token_revoked")

        user_id = payload["sub"]

        # 2. Compute SHA-256 hash of raw token
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        # 3. Look up RefreshToken record in DB
        existing_token = self._refresh_token_repo.find_by_token_hash(token_hash)

        # 4. Validate: exists, not revoked, not expired
        if existing_token is None or not existing_token.is_usable:
            raise TokenRevokedError("token_revoked")

        # 5. ATOMIC ROTATION: revoke old + store new (same transaction/flush)
        self._refresh_token_repo.revoke(existing_token.id)

        new_refresh_token_value = create_refresh_token_value(user_id=user_id)
        new_token_hash = hashlib.sha256(new_refresh_token_value.encode()).hexdigest()

        new_token_entity = RefreshToken(
            user_id=existing_token.user_id,
            token_hash=new_token_hash,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_expire_days),
        )
        self._refresh_token_repo.save(new_token_entity)

        # 6. Generate new Access Token
        access_token = create_access_token(user_id=user_id)

        return RefreshTokenOutput(
            access_token=access_token,
            refresh_token=new_refresh_token_value,
            token_type="bearer",
        )
