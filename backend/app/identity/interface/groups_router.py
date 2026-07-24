"""Groups REST endpoints — family group creation and invitation management.

Thin adapter layer: delegates all business logic to use cases.
Reference: authentication/design.md, authentication/requirements.md Req 3.1, 3.2
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.application.accept_group_invitation import (
    AcceptGroupInvitation,
    AcceptGroupInvitationInput,
    AlreadyAcceptedError,
    InvitationNotFoundError,
    NotInviteeError,
)
from app.identity.application.create_family_group import CreateFamilyGroup, CreateFamilyGroupInput
from app.identity.application.invite_group_member import (
    AlreadyMemberError,
    GroupNotFoundError,
    InviteGroupMember,
    InviteGroupMemberInput,
    NotGroupMemberError,
)
from app.identity.infrastructure.repositories import (
    SqlFamilyGroupRepository,
    SqlGroupMembershipRepository,
)
from app.identity.interface.dependencies import get_current_user_id
from app.identity.interface.schemas import (
    CreateGroupRequest,
    CreateGroupResponse,
    InvitationResponse,
    InviteRequest,
)

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("/", response_model=CreateGroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    request: CreateGroupRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new family group. The authenticated user becomes the first member."""
    group_repo = SqlFamilyGroupRepository(db)
    membership_repo = SqlGroupMembershipRepository(db)

    use_case = CreateFamilyGroup(
        family_group_repository=group_repo,
        group_membership_repository=membership_repo,
    )

    input_dto = CreateFamilyGroupInput(
        name=request.name,
        creator_user_id=current_user_id,
    )

    group = use_case.execute(input_dto)
    db.commit()

    return CreateGroupResponse(
        id=group.id,
        name=group.name,
        created_at=group.created_at,
    )


@router.post(
    "/{group_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
def invite_member(
    group_id: UUID,
    request: InviteRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Invite a user to a family group. The inviter must be an accepted member."""
    group_repo = SqlFamilyGroupRepository(db)
    membership_repo = SqlGroupMembershipRepository(db)

    use_case = InviteGroupMember(
        family_group_repository=group_repo,
        group_membership_repository=membership_repo,
    )

    input_dto = InviteGroupMemberInput(
        group_id=group_id,
        invitee_user_id=request.user_id,
        inviter_user_id=current_user_id,
    )

    try:
        membership = use_case.execute(input_dto)
    except GroupNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="group_not_found",
        )
    except NotGroupMemberError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not_group_member",
        )
    except AlreadyMemberError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="already_member",
        )

    db.commit()

    return InvitationResponse(
        id=membership.id,
        group_id=membership.group_id,
        user_id=membership.user_id,
        status=membership.status.value,
        created_at=membership.created_at,
    )


@router.post(
    "/{group_id}/invitations/{invitation_id}/accept",
    response_model=InvitationResponse,
    status_code=status.HTTP_200_OK,
)
def accept_invitation(
    group_id: UUID,
    invitation_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Accept a group invitation. Only the invited user can accept."""
    membership_repo = SqlGroupMembershipRepository(db)

    use_case = AcceptGroupInvitation(group_membership_repository=membership_repo)

    input_dto = AcceptGroupInvitationInput(
        membership_id=invitation_id,
        accepting_user_id=current_user_id,
    )

    try:
        membership = use_case.execute(input_dto)
    except InvitationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="invitation_not_found",
        )
    except NotInviteeError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not_the_invitee",
        )
    except AlreadyAcceptedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="already_accepted",
        )

    db.commit()

    return InvitationResponse(
        id=membership.id,
        group_id=membership.group_id,
        user_id=membership.user_id,
        status=membership.status.value,
        created_at=membership.created_at,
    )
