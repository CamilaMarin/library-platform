"""RevokeToken use case — revokes a refresh token (logout).

Verifies the JWT, looks up the token by hash, and revokes it.
Raises TokenNotFoundError if the token is not found or already revoked.
The endpoint layer catches all errors and returns 200 regardless (no info leakage).

Reference: authentication/requirements.md Req 2.4
Design: Property 5 (revocation enforcement)
"""

import hashlib

from app.auth.jwt import verify_refresh_token
from app.identity.application.protocols import RefreshTokenRepository


class TokenNotFoundError(Exception):
    """Raised when a refresh token is not found or already revoked."""

    pass


class RevokeTokenUseCase:
    """Use case: revoke a Refresh Token (logout).

    Enforces:
    - JWT signature verification before DB lookup
    - DB-level lookup by SHA-256 hash
    - Revocation of the token record
    """

    def __init__(self, refresh_token_repository: RefreshTokenRepository):
        self._refresh_token_repo = refresh_token_repository

    def execute(self, raw_token: str) -> None:
        """Revoke the given refresh token.

        Args:
            raw_token: The raw JWT refresh token value from the client.

        Raises:
            TokenNotFoundError: If the token is not found or already revoked.
            jwt.InvalidTokenError: If the JWT signature is invalid.
        """
        # 1. Verify JWT signature and decode
        verify_refresh_token(raw_token)

        # 2. Compute SHA-256 hash of raw token
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        # 3. Look up RefreshToken record in DB
        existing_token = self._refresh_token_repo.find_by_token_hash(token_hash)

        # 4. If not found or already revoked → raise
        if existing_token is None or existing_token.revoked:
            raise TokenNotFoundError("token_not_found")

        # 5. Revoke the token
        self._refresh_token_repo.revoke(existing_token.id)
