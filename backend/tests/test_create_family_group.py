"""Tests for CreateFamilyGroup use case and POST /groups endpoint.

Verifies group creation, automatic creator membership, name validation,
and authentication enforcement.

Reference: authentication/tasks.md#7, requirements.md Req 3.1
"""

import os
from uuid import UUID, uuid4

# Override DATABASE_URL before any app import so the engine uses SQLite
os.environ["DATABASE_URL"] = "sqlite:///file::memory:?cache=shared"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.auth.jwt import create_access_token  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.identity.application.create_family_group import (  # noqa: E402
    CreateFamilyGroup,
    CreateFamilyGroupInput,
)
from app.identity.domain.entities import (  # noqa: E402
    FamilyGroup,
    GroupMembership,
    MembershipStatus,
)
from app.main import app  # noqa: E402

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

    def find_by_group_id(self, group_id: UUID) -> list[GroupMembership]:
        return [m for m in self.memberships if m.group_id == group_id]

    def find_by_user_and_group(self, user_id: UUID, group_id: UUID) -> GroupMembership | None:
        return next(
            (m for m in self.memberships if m.user_id == user_id and m.group_id == group_id),
            None,
        )


# --- Unit test fixtures ---


@pytest.fixture
def group_repo():
    return InMemoryFamilyGroupRepository()


@pytest.fixture
def membership_repo():
    return InMemoryGroupMembershipRepository()


@pytest.fixture
def use_case(group_repo, membership_repo):
    return CreateFamilyGroup(
        family_group_repository=group_repo,
        group_membership_repository=membership_repo,
    )


# --- Unit tests: CreateFamilyGroup use case ---


class TestCreateFamilyGroupUseCase:
    """Unit tests for CreateFamilyGroup use case logic."""

    def test_creates_group_with_name(self, use_case, group_repo):
        creator_id = uuid4()
        input_dto = CreateFamilyGroupInput(name="Familia García", creator_user_id=creator_id)

        result = use_case.execute(input_dto)

        assert result.name == "Familia García"
        assert len(group_repo.groups) == 1

    def test_creator_added_as_accepted_member(self, use_case, membership_repo):
        creator_id = uuid4()
        input_dto = CreateFamilyGroupInput(name="Mi Familia", creator_user_id=creator_id)

        result = use_case.execute(input_dto)

        assert len(membership_repo.memberships) == 1
        membership = membership_repo.memberships[0]
        assert membership.group_id == result.id
        assert membership.user_id == creator_id
        assert membership.status == MembershipStatus.ACCEPTED

    def test_returns_group_with_valid_id(self, use_case):
        creator_id = uuid4()
        input_dto = CreateFamilyGroupInput(name="Test Group", creator_user_id=creator_id)

        result = use_case.execute(input_dto)

        assert isinstance(result.id, UUID)
        assert result.created_at is not None

    def test_empty_name_raises_value_error(self, use_case):
        creator_id = uuid4()
        input_dto = CreateFamilyGroupInput(name="", creator_user_id=creator_id)

        with pytest.raises(ValueError, match="non-empty name"):
            use_case.execute(input_dto)

    def test_whitespace_only_name_raises_value_error(self, use_case):
        creator_id = uuid4()
        input_dto = CreateFamilyGroupInput(name="   ", creator_user_id=creator_id)

        with pytest.raises(ValueError, match="non-empty name"):
            use_case.execute(input_dto)


# --- Integration tests: POST /groups endpoint ---

# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///file::memory:?cache=shared"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


client = TestClient(app)


def _auth_header(user_id: UUID | None = None) -> dict:
    """Generate a valid Authorization header with an access token."""
    uid = user_id or uuid4()
    token = create_access_token(str(uid))
    return {"Authorization": f"Bearer {token}"}


class TestCreateGroupEndpointHappyPath:
    """POST /groups/ — successful group creation with auth."""

    def test_returns_201(self):
        headers = _auth_header()
        response = client.post("/groups/", json={"name": "Familia Test"}, headers=headers)
        assert response.status_code == 201

    def test_returns_group_data(self):
        headers = _auth_header()
        response = client.post("/groups/", json={"name": "Los García"}, headers=headers)
        data = response.json()

        assert data["name"] == "Los García"
        assert "id" in data
        assert "created_at" in data

    def test_creator_is_accepted_member(self):
        """Verify creator is automatically added as accepted member via DB."""
        user_id = uuid4()
        headers = _auth_header(user_id)
        response = client.post("/groups/", json={"name": "Mi Familia"}, headers=headers)
        assert response.status_code == 201

        # Verify through the database directly
        group_id = response.json()["id"]
        db = TestSession()
        from app.identity.infrastructure.repositories import SqlGroupMembershipRepository

        membership_repo = SqlGroupMembershipRepository(db)
        memberships = membership_repo.find_by_group_id(UUID(group_id))
        db.close()

        assert len(memberships) == 1
        assert memberships[0].user_id == user_id
        assert memberships[0].status == MembershipStatus.ACCEPTED


class TestCreateGroupEndpointAuth:
    """POST /groups/ — authentication enforcement."""

    def test_missing_auth_header_returns_422(self):
        """No Authorization header results in 422 (FastAPI validation)."""
        response = client.post("/groups/", json={"name": "Test"})
        assert response.status_code == 422

    def test_invalid_token_returns_401(self):
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.post("/groups/", json={"name": "Test"}, headers=headers)
        assert response.status_code == 401

    def test_malformed_auth_header_returns_401(self):
        headers = {"Authorization": "NotBearer sometoken"}
        response = client.post("/groups/", json={"name": "Test"}, headers=headers)
        assert response.status_code == 401


class TestCreateGroupEndpointValidation:
    """POST /groups/ — request validation."""

    def test_empty_name_returns_422(self):
        headers = _auth_header()
        response = client.post("/groups/", json={"name": ""}, headers=headers)
        assert response.status_code == 422

    def test_missing_name_returns_422(self):
        headers = _auth_header()
        response = client.post("/groups/", json={}, headers=headers)
        assert response.status_code == 422
