"""AuditLog service — callable from any use case that performs high-value operations.

MVP scope (high-value operations only):
- User registration
- Login
- Account deletion
- Digital file upload
- ARCO requests

Design is extensible — to audit a new operation, add an AuditAction enum value
and call this service from the relevant use case.

Reference: ADR-0003, privacy/tasks.md#2
"""

from uuid import UUID

from app.identity.application.protocols import AuditLogRepository
from app.identity.domain.entities import AuditAction, AuditLog


class AuditService:
    """Service for recording high-value operations in the audit log."""

    def __init__(self, repository: AuditLogRepository):
        self._repository = repository

    def log(
        self,
        actor_user_id: UUID | None,
        action: AuditAction,
        affected_entity: str,
    ) -> AuditLog:
        """Record an audit entry for a high-value operation."""
        entry = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            affected_entity=affected_entity,
        )
        return self._repository.save(entry)
