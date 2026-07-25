"""Tests for InviteGroupMember / AcceptGroupInvitation use cases and endpoints.

Verifies invitation creation, explicit acceptance (Property 2), and error cases.
Reference: authentication/tasks.md#8, requirements.md Req 3.1, 3.2
"""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt import create_access_token
from app.identity.application.accept_group_invitation import (
    AcceptGroupInvitation,
    AcceptGroupInvitationInput,
    AlreadyAcceptedError,
    InvitationNotFoundError,
    NotInviteeError,
)
from app.identity.application.invite_group_member import (
    AlreadyMemberError,
    GroupNotFoundError,
    InviteGroupMember,
    InviteGroupMemberInput,
    NotGroupMemberError,
)
from app.identity.domain.entities import (
    FamilyGroup,
    GroupMembership,
    MembershipStatus,
)
from app.main import app

# --- In-memory test doubles for unit tests ---


class InMemoryFamilyGroupRepository:
    """Test double for FamilyGroupRepository."""

    def __init__(self):
        self.groups: list[FamilyGroup] = []

    def save(self, group: FamilyGroup) -> FamilyGroup:
        self.groups.append(group)
        return group

    def find_by_id(self, group_id: UUID) -> FamilyGroup | None:
        return next((g for g in self.groups if g.id == group_id), None)


class InMemoryGroupMembershipRepository:
    """Test double for GroupMembershipRepository."""

    def __init__(self):
        self.memberships: list[GroupMembership] = []

    def save(self, membership: GroupMembership) -> GroupMembership:
        self.memberships.append(membership)
        return membership

    def find_by_id(self, membership_id: UUID) -> GroupMembership | None:
        return next((m for m in self.memberships if m.id == membership_id), None)

    def find_by_group_id(self, group_id: UUID) -> list[GroupMembership]:
        return [m for m in self.memberships if m.group_id == group_id]

    def find_by_user_and_group(self, user_id: UUID, group_id: UUID) -> GroupMembership | None:
        return next(
            (m for m in self.memberships if m.user_id == user_id and m.group_id == group_id),
            None,
        )

    def update_status(self, membership_id: UUID, status: MembershipStatus) -> None:
        for m in self.memberships:
            if m.id == membership_id:
                m.status = status
                return


# --- Unit test fixtures ---


@pytest.fixture
def group_repo():
    return InMemoryFamilyGroupRepository()


@pytest.fixture
def membership_repo():
    return InMemoryGroupMembershipRepository()


@pytest.fixture
def invite_use_case(group_repo, membership_repo):
    return InviteGroupMember(
        family_group_repository=group_repo,
        group_membership_repository=membership_repo,
    )


@pytest.fixture
def accept_use_case(membership_repo):
    return AcceptGroupInvitation(group_membership_repository=membership_repo)


def _create_group(group_repo) -> FamilyGroup:
    """Helper: create and save a group."""
    group = FamilyGroup(name="Test Family")
    group_repo.save(group)
    return group


def _add_accepted_member(membership_repo, group_id: UUID, user_id: UUID) -> GroupMembership:
    """Helper: add a user as an accepted member of a group."""
    membership = GroupMembership(
        group_id=group_id,
        user_id=user_id,
        status=MembershipStatus.ACCEPTED,
    )
    membership_repo.save(membership)
    return membership


# --- Unit tests: InviteGroupMember use case ---


class TestInviteGroupMemberUseCase:
    """Unit tests for InviteGroupMember use case logic."""

    def test_happy_path_creates_invitation_with_invited_status(
        self, invite_use_case, group_repo, membership_repo
    ):
        group = _create_group(group_repo)
        inviter_id = uuid4()
        invitee_id = uuid4()
        _add_accepted_member(membership_repo, group.id, inviter_id)

        input_dto = InviteGroupMemberInput(
            group_id=group.id,
            invitee_user_id=invitee_id,
            inviter_user_id=inviter_id,
        )
        result = invite_use_case.execute(input_dto)

        assert result.status == MembershipStatus.INVITED
        assert result.user_id == invitee_id
        assert result.group_id == group.id
        assert isinstance(result.id, UUID)

    def test_group_not_found_raises_error(self, invite_use_case):
        input_dto = InviteGroupMemberInput(
            group_id=uuid4(),
            invitee_user_id=uuid4(),
            inviter_user_id=uuid4(),
        )
        with pytest.raises(GroupNotFoundError):
            invite_use_case.execute(input_dto)

    def test_inviter_not_a_member_raises_error(self, invite_use_case, group_repo):
        group = _create_group(group_repo)
        input_dto = InviteGroupMemberInput(
            group_id=group.id,
            invitee_user_id=uuid4(),
            inviter_user_id=uuid4(),  # not a member
        )
        with pytest.raises(NotGroupMemberError):
            invite_use_case.execute(input_dto)

    def test_inviter_with_invited_status_cannot_invite(
        self, invite_use_case, group_repo, membership_repo
    ):
        """An inviter who is only 'invited' (not accepted) cannot invite others."""
        group = _create_group(group_repo)
        inviter_id = uuid4()
        # Add inviter with INVITED status (not accepted)
        membership = GroupMembership(
            group_id=group.id,
            user_id=inviter_id,
            status=MembershipStatus.INVITED,
        )
        membership_repo.save(membership)

        input_dto = InviteGroupMemberInput(
            group_id=group.id,
            invitee_user_id=uuid4(),
            inviter_user_id=inviter_id,
        )
        with pytest.raises(NotGroupMemberError):
            invite_use_case.execute(input_dto)

    def test_invitee_already_a_member_raises_error(
        self, invite_use_case, group_repo, membership_repo
    ):
        group = _create_group(group_repo)
        inviter_id = uuid4()
        invitee_id = uuid4()
        _add_accepted_member(membership_repo, group.id, inviter_id)
        _add_accepted_member(membership_repo, group.id, invitee_id)

        input_dto = InviteGroupMemberInput(
            group_id=group.id,
            invitee_user_id=invitee_id,
            inviter_user_id=inviter_id,
        )
        with pytest.raises(AlreadyMemberError):
            invite_use_case.execute(input_dto)

    def test_invitee_with_pending_invitation_raises_error(
        self, invite_use_case, group_repo, membership_repo
    ):
        """Duplicate invitation to same user is rejected."""
        group = _create_group(group_repo)
        inviter_id = uuid4()
        invitee_id = uuid4()
        _add_accepted_member(membership_repo, group.id, inviter_id)
        # Invitee already has a pending invitation
        membership = GroupMembership(
            group_id=group.id,
            user_id=invitee_id,
            status=MembershipStatus.INVITED,
        )
        membership_repo.save(membership)

        input_dto = InviteGroupMemberInput(
            group_id=group.id,
            invitee_user_id=invitee_id,
            inviter_user_id=inviter_id,
        )
        with pytest.raises(AlreadyMemberError):
            invite_use_case.execute(input_dto)


# --- Unit tests: AcceptGroupInvitation use case ---


class TestAcceptGroupInvitationUseCase:
    """Unit tests for AcceptGroupInvitation use case logic (Property 2)."""

    def test_happy_path_transitions_to_accepted(self, accept_use_case, membership_repo):
        invitee_id = uuid4()
        membership = GroupMembership(
            group_id=uuid4(),
            user_id=invitee_id,
            status=MembershipStatus.INVITED,
        )
        membership_repo.save(membership)

        input_dto = AcceptGroupInvitationInput(
            membership_id=membership.id,
            accepting_user_id=invitee_id,
        )
        result = accept_use_case.execute(input_dto)

        assert result.status == MembershipStatus.ACCEPTED
        # Verify persistence was updated
        stored = membership_repo.find_by_id(membership.id)
        assert stored.status == MembershipStatus.ACCEPTED

    def test_wrong_user_raises_not_invitee_error(self, accept_use_case, membership_repo):
        """Property 2: only the invited user can accept."""
        invitee_id = uuid4()
        other_user_id = uuid4()
        membership = GroupMembership(
            group_id=uuid4(),
            user_id=invitee_id,
            status=MembershipStatus.INVITED,
        )
        membership_repo.save(membership)

        input_dto = AcceptGroupInvitationInput(
            membership_id=membership.id,
            accepting_user_id=other_user_id,
        )
        with pytest.raises(NotInviteeError):
            accept_use_case.execute(input_dto)

    def test_already_accepted_raises_error(self, accept_use_case, membership_repo):
        invitee_id = uuid4()
        membership = GroupMembership(
            group_id=uuid4(),
            user_id=invitee_id,
            status=MembershipStatus.ACCEPTED,
        )
        membership_repo.save(membership)

        input_dto = AcceptGroupInvitationInput(
            membership_id=membership.id,
            accepting_user_id=invitee_id,
        )
        with pytest.raises(AlreadyAcceptedError):
            accept_use_case.execute(input_dto)

    def test_invitation_not_found_raises_error(self, accept_use_case):
        input_dto = AcceptGroupInvitationInput(
            membership_id=uuid4(),
            accepting_user_id=uuid4(),
        )
        with pytest.raises(InvitationNotFoundError):
            accept_use_case.execute(input_dto)


# --- Integration tests: endpoints ---

client = TestClient(app)


def _auth_header(user_id: UUID | None = None) -> dict:
    """Generate a valid Authorization header with an access token."""
    uid = user_id or uuid4()
    token = create_access_token(str(uid))
    return {"Authorization": f"Bearer {token}"}


def _create_group_via_api(user_id: UUID, name: str = "Test Family") -> dict:
    """Helper: create a group via API and return the response data."""
    headers = _auth_header(user_id)
    response = client.post("/groups/", json={"name": name}, headers=headers)
    assert response.status_code == 201
    return response.json()


class TestInviteEndpointHappyPath:
    """POST /groups/{group_id}/invitations — successful invitation."""

    def test_returns_201_with_invitation_data(self):
        creator_id = uuid4()
        invitee_id = uuid4()
        group = _create_group_via_api(creator_id)

        headers = _auth_header(creator_id)
        response = client.post(
            f"/groups/{group['id']}/invitations",
            json={"user_id": str(invitee_id)},
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == str(invitee_id)
        assert data["group_id"] == group["id"]
        assert data["status"] == "invited"
        assert "id" in data
        assert "created_at" in data


class TestInviteEndpointErrors:
    """POST /groups/{group_id}/invitations — error cases."""

    def test_group_not_found_returns_404(self):
        user_id = uuid4()
        headers = _auth_header(user_id)
        response = client.post(
            f"/groups/{uuid4()}/invitations",
            json={"user_id": str(uuid4())},
            headers=headers,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "group_not_found"

    def test_inviter_not_member_returns_403(self):
        # Create a group with one user, then try to invite from a different user
        creator_id = uuid4()
        other_user_id = uuid4()
        group = _create_group_via_api(creator_id)

        headers = _auth_header(other_user_id)  # not a member
        response = client.post(
            f"/groups/{group['id']}/invitations",
            json={"user_id": str(uuid4())},
            headers=headers,
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "not_group_member"

    def test_already_member_returns_409(self):
        creator_id = uuid4()
        group = _create_group_via_api(creator_id)

        # Try to invite the creator (who is already a member)
        headers = _auth_header(creator_id)
        response = client.post(
            f"/groups/{group['id']}/invitations",
            json={"user_id": str(creator_id)},
            headers=headers,
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "already_member"

    def test_missing_auth_returns_422(self):
        response = client.post(
            f"/groups/{uuid4()}/invitations",
            json={"user_id": str(uuid4())},
        )
        assert response.status_code == 422

    def test_invalid_token_returns_401(self):
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.post(
            f"/groups/{uuid4()}/invitations",
            json={"user_id": str(uuid4())},
            headers=headers,
        )
        assert response.status_code == 401


class TestAcceptEndpointHappyPath:
    """POST /groups/{group_id}/invitations/{id}/accept — successful acceptance."""

    def test_invite_then_accept_flow(self):
        """Full happy path: invite a user, then the invitee accepts."""
        creator_id = uuid4()
        invitee_id = uuid4()
        group = _create_group_via_api(creator_id)

        # Invite
        invite_headers = _auth_header(creator_id)
        invite_response = client.post(
            f"/groups/{group['id']}/invitations",
            json={"user_id": str(invitee_id)},
            headers=invite_headers,
        )
        assert invite_response.status_code == 201
        invitation = invite_response.json()
        assert invitation["status"] == "invited"

        # Accept (as the invitee)
        accept_headers = _auth_header(invitee_id)
        accept_response = client.post(
            f"/groups/{group['id']}/invitations/{invitation['id']}/accept",
            headers=accept_headers,
        )

        assert accept_response.status_code == 200
        data = accept_response.json()
        assert data["status"] == "accepted"
        assert data["user_id"] == str(invitee_id)
        assert data["id"] == invitation["id"]


class TestAcceptEndpointErrors:
    """POST /groups/{group_id}/invitations/{id}/accept — error cases."""

    def test_invitation_not_found_returns_404(self):
        user_id = uuid4()
        headers = _auth_header(user_id)
        response = client.post(
            f"/groups/{uuid4()}/invitations/{uuid4()}/accept",
            headers=headers,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "invitation_not_found"

    def test_wrong_user_returns_403(self):
        """Property 2: only the invited user can accept."""
        creator_id = uuid4()
        invitee_id = uuid4()
        wrong_user_id = uuid4()
        group = _create_group_via_api(creator_id)

        # Invite
        invite_headers = _auth_header(creator_id)
        invite_response = client.post(
            f"/groups/{group['id']}/invitations",
            json={"user_id": str(invitee_id)},
            headers=invite_headers,
        )
        invitation = invite_response.json()

        # Try to accept as wrong user
        accept_headers = _auth_header(wrong_user_id)
        response = client.post(
            f"/groups/{group['id']}/invitations/{invitation['id']}/accept",
            headers=accept_headers,
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "not_the_invitee"

    def test_already_accepted_returns_409(self):
        creator_id = uuid4()
        invitee_id = uuid4()
        group = _create_group_via_api(creator_id)

        # Invite + Accept
        invite_headers = _auth_header(creator_id)
        invite_response = client.post(
            f"/groups/{group['id']}/invitations",
            json={"user_id": str(invitee_id)},
            headers=invite_headers,
        )
        invitation = invite_response.json()

        accept_headers = _auth_header(invitee_id)
        client.post(
            f"/groups/{group['id']}/invitations/{invitation['id']}/accept",
            headers=accept_headers,
        )

        # Try to accept again
        response = client.post(
            f"/groups/{group['id']}/invitations/{invitation['id']}/accept",
            headers=accept_headers,
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "already_accepted"

    def test_missing_auth_returns_422(self):
        response = client.post(
            f"/groups/{uuid4()}/invitations/{uuid4()}/accept",
        )
        assert response.status_code == 422

    def test_invalid_token_returns_401(self):
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.post(
            f"/groups/{uuid4()}/invitations/{uuid4()}/accept",
            headers=headers,
        )
        assert response.status_code == 401
