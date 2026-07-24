"""Groups REST endpoints — family group creation.

Thin adapter layer: delegates all business logic to use cases.
Reference: authentication/design.md, authentication/requirements.md Req 3.1
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.application.create_family_group import CreateFamilyGroup, CreateFamilyGroupInput
from app.identity.infrastructure.repositories import (
    SqlFamilyGroupRepository,
    SqlGroupMembershipRepository,
)
from app.identity.interface.dependencies import get_current_user_id
from app.identity.interface.schemas import CreateGroupRequest, CreateGroupResponse

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
