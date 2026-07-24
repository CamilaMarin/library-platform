"""Users REST endpoints — user data export and account deletion (ARCO rights).

Thin adapter layer: delegates all business logic to use cases.
Reference: authentication/requirements.md Req 4.1, 4.2
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.application.audit_service import AuditService
from app.identity.application.delete_user_account import (
    DeleteUserAccount,
)
from app.identity.application.delete_user_account import (
    UserNotFoundError as DeleteUserNotFoundError,
)
from app.identity.application.export_user_data import (
    ExportUserData,
)
from app.identity.application.export_user_data import (
    UserNotFoundError as ExportUserNotFoundError,
)
from app.identity.infrastructure.repositories import (
    SqlAuditLogRepository,
    SqlDataConsentRepository,
    SqlDataProcessingRecordRepository,
    SqlGroupMembershipRepository,
    SqlRefreshTokenRepository,
    SqlUserRepository,
)
from app.identity.interface.dependencies import get_current_user_id
from app.identity.interface.schemas import (
    ExportConsentItem,
    ExportMembershipItem,
    ExportProcessingRecordItem,
    ExportResponse,
    ExportUserProfile,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/export", response_model=ExportResponse)
def export_user_data(
    current_user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Export all identity-owned personal data for the authenticated user.

    ARCO access right — returns structured JSON with all user data (no password_hash).
    """
    user_repo = SqlUserRepository(db)
    consent_repo = SqlDataConsentRepository(db)
    membership_repo = SqlGroupMembershipRepository(db)
    processing_record_repo = SqlDataProcessingRecordRepository(db)
    audit_repo = SqlAuditLogRepository(db)
    audit_service = AuditService(repository=audit_repo)

    use_case = ExportUserData(
        user_repository=user_repo,
        consent_repository=consent_repo,
        membership_repository=membership_repo,
        processing_record_repository=processing_record_repo,
        audit_service=audit_service,
    )

    try:
        result = use_case.execute(current_user_id)
    except ExportUserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user_not_found",
        )

    db.commit()

    return ExportResponse(
        user=ExportUserProfile(
            name=result.user.name,
            email=result.user.email,
            created_at=result.user.created_at,
        ),
        consents=[
            ExportConsentItem(
                id=c.id,
                timestamp=c.timestamp,
                policy_version=c.policy_version,
                purpose=c.purpose,
            )
            for c in result.consents
        ],
        memberships=[
            ExportMembershipItem(
                id=m.id,
                group_id=m.group_id,
                status=m.status,
                created_at=m.created_at,
            )
            for m in result.memberships
        ],
        processing_records=[
            ExportProcessingRecordItem(
                id=r.id,
                data_type=r.data_type,
                purpose=r.purpose,
                legal_basis=r.legal_basis,
                collected_at=r.collected_at,
                retention_expires_at=r.retention_expires_at,
            )
            for r in result.processing_records
        ],
    )


@router.delete("/me")
def delete_user_account(
    current_user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Permanently delete the authenticated user's account and all associated data.

    ARCO cancellation right — MVP hard-delete, no recovery period.
    """
    user_repo = SqlUserRepository(db)
    refresh_token_repo = SqlRefreshTokenRepository(db)
    membership_repo = SqlGroupMembershipRepository(db)
    consent_repo = SqlDataConsentRepository(db)
    processing_record_repo = SqlDataProcessingRecordRepository(db)
    audit_repo = SqlAuditLogRepository(db)
    audit_service = AuditService(repository=audit_repo)

    use_case = DeleteUserAccount(
        user_repository=user_repo,
        refresh_token_repository=refresh_token_repo,
        membership_repository=membership_repo,
        consent_repository=consent_repo,
        processing_record_repository=processing_record_repo,
        audit_service=audit_service,
    )

    try:
        use_case.execute(current_user_id)
    except DeleteUserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user_not_found",
        )

    db.commit()

    return {"detail": "account_deleted"}
