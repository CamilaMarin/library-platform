"""Users REST endpoints — ARCO rights (export, rectify, delete, oppose).

Thin adapter layer: delegates all business logic to use cases.
Reference: authentication/requirements.md Req 4.1, 4.2; privacy/requirements.md Req 1.2
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
from app.identity.application.get_user_oppositions import (
    GetUserOppositions,
)
from app.identity.application.get_user_oppositions import (
    UserNotFoundError as GetOppositionsUserNotFoundError,
)
from app.identity.application.oppose_data_processing import (
    OpposeDataProcessing,
)
from app.identity.application.oppose_data_processing import (
    UserNotFoundError as OpposeUserNotFoundError,
)
from app.identity.application.purge_user_data import PurgeUserData
from app.identity.application.rectify_user_data import (
    EmailAlreadyTakenError,
    InvalidEmailError,
    NoFieldsProvidedError,
    RectifyUserData,
)
from app.identity.application.rectify_user_data import (
    UserNotFoundError as RectifyUserNotFoundError,
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
    OpposeRequest,
    OpposeResponse,
    OppositionsResponse,
    RectifyRequest,
    RectifyResponse,
)
from app.library.infrastructure.file_storage import LocalFileStorage

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

    ARCO cancellation right — purges digital files, anonymizes old audit logs,
    and hard-deletes all identity-owned data. No recovery period.
    Reference: privacy/requirements.md Req 1.2, 1.7
    """
    # Step 1: Purge cross-context data (files, copies, reviews, loans, audit anonymization)
    purge_service = PurgeUserData(
        session=db,
        file_storage=LocalFileStorage(),
    )
    purge_service.execute(current_user_id)

    # Step 2: Delete identity-owned data (tokens, memberships, consents, user record)
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


@router.patch("/me", response_model=RectifyResponse)
def rectify_user_data(
    body: RectifyRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update the authenticated user's name and/or email.

    ARCO rectification right — allows users to correct inaccurate personal data.
    """
    user_repo = SqlUserRepository(db)
    audit_repo = SqlAuditLogRepository(db)
    audit_service = AuditService(repository=audit_repo)

    use_case = RectifyUserData(
        user_repository=user_repo,
        audit_service=audit_service,
    )

    try:
        result = use_case.execute(
            user_id=current_user_id,
            new_name=body.name,
            new_email=body.email,
        )
    except RectifyUserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user_not_found",
        )
    except NoFieldsProvidedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="no_fields_provided",
        )
    except InvalidEmailError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_email_format",
        )
    except EmailAlreadyTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email_already_taken",
        )

    db.commit()

    return RectifyResponse(
        user_id=result.user_id,
        name=result.name,
        email=result.email,
    )


@router.get("/me/oppositions", response_model=OppositionsResponse)
def get_user_oppositions(
    current_user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List all active data processing oppositions for the authenticated user.

    ARCO opposition right — read access.
    """
    user_repo = SqlUserRepository(db)
    audit_repo = SqlAuditLogRepository(db)
    audit_service = AuditService(repository=audit_repo)

    use_case = GetUserOppositions(
        user_repository=user_repo,
        audit_service=audit_service,
    )

    try:
        purposes = use_case.execute(current_user_id)
    except GetOppositionsUserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user_not_found",
        )

    db.commit()

    return OppositionsResponse(opposed_purposes=purposes)


@router.post("/me/oppose", response_model=OpposeResponse)
def oppose_data_processing(
    body: OpposeRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Register opposition to a specific data processing purpose.

    ARCO opposition right — allows users to opt-out of non-essential processing.
    """
    user_repo = SqlUserRepository(db)
    audit_repo = SqlAuditLogRepository(db)
    audit_service = AuditService(repository=audit_repo)

    use_case = OpposeDataProcessing(
        user_repository=user_repo,
        audit_service=audit_service,
    )

    try:
        result = use_case.execute(
            user_id=current_user_id,
            processing_purpose=body.purpose,
        )
    except OpposeUserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user_not_found",
        )

    db.commit()

    return OpposeResponse(
        user_id=result.user_id,
        processing_purpose=result.processing_purpose,
        opposed=result.opposed,
    )
