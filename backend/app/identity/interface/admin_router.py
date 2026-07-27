"""Admin REST endpoints — retention job trigger and other admin operations.

Requires authentication. In production, this would also require an admin role check.
Reference: privacy/requirements.md Req 1.7, ADR-0016
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.application.audit_service import AuditService
from app.identity.application.retention_job import RetentionJob, RetentionJobResult
from app.identity.infrastructure.repositories import SqlAuditLogRepository
from app.identity.interface.dependencies import get_current_user_id

router = APIRouter(prefix="/admin", tags=["admin"])


class RetentionJobResponse(BaseModel):
    """Response schema for the retention job endpoint."""

    policies_processed: int
    records_affected: int
    details: list[str]


@router.post("/retention/run", response_model=RetentionJobResponse)
def run_retention_job(
    current_user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> RetentionJobResponse:
    """Trigger the data retention job manually.

    Reads all active retention policies from the database and enforces them.
    Duration is always from the retention_policies table — never hardcoded.

    Requires authentication. In production, add an admin role guard.
    """
    audit_repo = SqlAuditLogRepository(db)
    audit_service = AuditService(repository=audit_repo)

    job = RetentionJob(session=db, audit_service=audit_service)
    result: RetentionJobResult = job.execute()

    db.commit()

    return RetentionJobResponse(
        policies_processed=result.policies_processed,
        records_affected=result.records_affected,
        details=result.details,
    )
