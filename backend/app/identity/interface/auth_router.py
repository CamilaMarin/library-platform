"""Auth REST endpoints — registration, consent, login, token refresh, and logout.

Thin adapter layer: delegates all business logic to use cases.
Reference: authentication/design.md, authentication/tasks.md#3, #4, #5, #6
"""

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.application.audit_service import AuditService
from app.identity.application.login_user import InvalidCredentialsError, LoginUser, LoginUserInput
from app.identity.application.refresh_token_use_case import RefreshTokenUseCase, TokenRevokedError
from app.identity.application.register_user import (
    ConsentRequiredError,
    EmailAlreadyExistsError,
    RegisterUser,
    RegisterUserInput,
)
from app.identity.application.revoke_token_use_case import RevokeTokenUseCase, TokenNotFoundError
from app.identity.domain.entities import DataConsent
from app.identity.infrastructure.repositories import (
    SqlAuditLogRepository,
    SqlDataConsentRepository,
    SqlRefreshTokenRepository,
    SqlUserRepository,
)
from app.identity.interface.schemas import (
    ConsentRequest,
    ConsentResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user with explicit consent."""
    user_repo = SqlUserRepository(db)
    consent_repo = SqlDataConsentRepository(db)
    audit_repo = SqlAuditLogRepository(db)
    audit_service = AuditService(repository=audit_repo)

    use_case = RegisterUser(
        user_repository=user_repo,
        consent_repository=consent_repo,
        audit_service=audit_service,
    )

    input_dto = RegisterUserInput(
        name=request.name,
        email=request.email,
        password=request.password,
        consent_policy_version=request.consent_policy_version,
        consent_purpose=request.consent_purpose,
    )

    try:
        user = use_case.execute(input_dto)
    except ConsentRequiredError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="consent_required",
        )
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email_already_exists",
        )

    db.commit()

    return RegisterResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        created_at=user.created_at,
    )


@router.post("/consent", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
def record_consent(request: ConsentRequest, db: Session = Depends(get_db)):
    """Record standalone consent for an existing user."""
    consent_repo = SqlDataConsentRepository(db)

    consent = DataConsent(
        user_id=request.user_id,
        policy_version=request.policy_version,
        purpose=request.purpose,
    )

    consent_repo.save(consent)
    db.commit()

    return ConsentResponse(
        id=consent.id,
        user_id=consent.user_id,
        timestamp=consent.timestamp,
        policy_version=consent.policy_version,
        purpose=consent.purpose,
    )


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return Access + Refresh tokens."""
    user_repo = SqlUserRepository(db)
    refresh_token_repo = SqlRefreshTokenRepository(db)
    audit_repo = SqlAuditLogRepository(db)
    audit_service = AuditService(repository=audit_repo)

    use_case = LoginUser(
        user_repository=user_repo,
        refresh_token_repository=refresh_token_repo,
        audit_service=audit_service,
    )

    input_dto = LoginUserInput(
        email=request.email,
        password=request.password,
    )

    try:
        result = use_case.execute(input_dto)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_credentials",
        )

    db.commit()

    return LoginResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
    )


@router.post("/refresh", response_model=LoginResponse)
def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    """Rotate refresh token and return a new Access + Refresh token pair."""
    refresh_token_repo = SqlRefreshTokenRepository(db)

    use_case = RefreshTokenUseCase(refresh_token_repository=refresh_token_repo)

    try:
        result = use_case.execute(request.refresh_token)
    except (TokenRevokedError, jwt.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token_revoked",
        )

    db.commit()

    return LoginResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
    )


@router.post("/logout")
def logout(request: LogoutRequest, db: Session = Depends(get_db)):
    """Revoke a refresh token (logout).

    Always returns 200 regardless of token validity — prevents information leakage.
    Reference: authentication/requirements.md Req 2.4
    """
    refresh_token_repo = SqlRefreshTokenRepository(db)
    use_case = RevokeTokenUseCase(refresh_token_repository=refresh_token_repo)

    try:
        use_case.execute(request.refresh_token)
    except (TokenNotFoundError, jwt.InvalidTokenError):
        # Swallow errors — always return 200 (security best practice)
        pass

    db.commit()

    return {"detail": "logged_out"}
