"""Tests for RegisterUser use case.

Verifies consent-gating invariant, password hashing, duplicate email detection,
and audit logging. Uses in-memory test doubles — no database required.

Reference: authentication/tasks.md#2, requirements.md Req 1
"""

from uuid import UUID

import bcrypt
import pytest

from app.identity.application.audit_service import AuditService
from app.identity.application.register_user import (
    ConsentRequiredError,
    EmailAlreadyExistsError,
    RegisterUser,
    RegisterUserInput,
)
from app.identity.domain.entities import AuditAction, AuditLog, DataConsent, User

# --- Test doubles ---


class InMemoryUserRepository:
    """Test double for UserRepository."""

    def __init__(self):
        self.users: list[User] = []

    def save(self, user: User) -> User:
        self.users.append(user)
        return user

    def find_by_email(self, email: str) -> User | None:
        return next((u for u in self.users if u.email == email), None)

    def find_by_id(self, user_id: UUID) -> User | None:
        return next((u for u in self.users if u.id == user_id), None)


class InMemoryDataConsentRepository:
    """Test double for DataConsentRepository."""

    def __init__(self):
        self.consents: list[DataConsent] = []

    def save(self, consent: DataConsent) -> DataConsent:
        self.consents.append(consent)
        return consent

    def find_by_user_id(self, user_id: UUID) -> DataConsent | None:
        return next((c for c in self.consents if c.user_id == user_id), None)


class InMemoryAuditLogRepository:
    """Test double for AuditLogRepository."""

    def __init__(self):
        self.entries: list[AuditLog] = []

    def save(self, entry: AuditLog) -> AuditLog:
        self.entries.append(entry)
        return entry

    def find_by_actor(self, actor_user_id: UUID) -> list[AuditLog]:
        return [e for e in self.entries if e.actor_user_id == actor_user_id]


# --- Fixtures ---


@pytest.fixture
def user_repo():
    return InMemoryUserRepository()


@pytest.fixture
def consent_repo():
    return InMemoryDataConsentRepository()


@pytest.fixture
def audit_repo():
    return InMemoryAuditLogRepository()


@pytest.fixture
def audit_service(audit_repo):
    return AuditService(repository=audit_repo)


@pytest.fixture
def use_case(user_repo, consent_repo, audit_service):
    return RegisterUser(
        user_repository=user_repo,
        consent_repository=consent_repo,
        audit_service=audit_service,
    )


@pytest.fixture
def valid_input():
    return RegisterUserInput(
        name="María García",
        email="maria@example.com",
        password="SecurePass123!",
        consent_policy_version="1.0",
        consent_purpose="account_creation",
    )


# --- Tests ---


class TestRegisterUserHappyPath:
    """Happy path: registers user with consent in same transaction."""

    def test_creates_user_and_consent(self, use_case, user_repo, consent_repo, valid_input):
        result = use_case.execute(valid_input)

        assert result.name == "María García"
        assert result.email == "maria@example.com"
        assert len(user_repo.users) == 1
        assert len(consent_repo.consents) == 1

    def test_consent_linked_to_user(self, use_case, user_repo, consent_repo, valid_input):
        use_case.execute(valid_input)

        consent = consent_repo.consents[0]
        user = user_repo.users[0]
        assert consent.user_id == user.id

    def test_consent_records_policy_version(self, use_case, consent_repo, valid_input):
        use_case.execute(valid_input)

        consent = consent_repo.consents[0]
        assert consent.policy_version == "1.0"
        assert consent.purpose == "account_creation"

    def test_audit_log_created(self, use_case, audit_repo, valid_input):
        result = use_case.execute(valid_input)

        assert len(audit_repo.entries) == 1
        entry = audit_repo.entries[0]
        assert entry.action == AuditAction.USER_REGISTERED
        assert entry.affected_entity == f"user:{result.id}"

    def test_returned_user_has_no_password_hash(self, use_case, valid_input):
        result = use_case.execute(valid_input)

        assert result.password_hash == ""


class TestConsentGating:
    """Consent-gating: fails if consent data is missing."""

    def test_missing_policy_version_raises(self, use_case):
        input = RegisterUserInput(
            name="Test User",
            email="test@example.com",
            password="Password123!",
            consent_policy_version="",
            consent_purpose="account_creation",
        )
        with pytest.raises(ConsentRequiredError):
            use_case.execute(input)

    def test_missing_purpose_raises(self, use_case):
        input = RegisterUserInput(
            name="Test User",
            email="test@example.com",
            password="Password123!",
            consent_policy_version="1.0",
            consent_purpose="",
        )
        with pytest.raises(ConsentRequiredError):
            use_case.execute(input)

    def test_no_user_created_when_consent_missing(self, use_case, user_repo):
        input = RegisterUserInput(
            name="Test User",
            email="test@example.com",
            password="Password123!",
            consent_policy_version="",
            consent_purpose="",
        )
        with pytest.raises(ConsentRequiredError):
            use_case.execute(input)

        assert len(user_repo.users) == 0


class TestDuplicateEmail:
    """Duplicate email: raises appropriate error."""

    def test_duplicate_email_raises(self, use_case, valid_input):
        use_case.execute(valid_input)

        with pytest.raises(EmailAlreadyExistsError):
            use_case.execute(valid_input)

    def test_no_second_user_created(self, use_case, user_repo, valid_input):
        use_case.execute(valid_input)

        with pytest.raises(EmailAlreadyExistsError):
            use_case.execute(valid_input)

        assert len(user_repo.users) == 1


class TestPasswordHashing:
    """Password stored as hash, not plain text."""

    def test_password_stored_as_bcrypt_hash(self, use_case, user_repo, valid_input):
        use_case.execute(valid_input)

        stored_user = user_repo.users[0]
        assert stored_user.password_hash != valid_input.password
        assert stored_user.password_hash.startswith("$2b$")

    def test_stored_hash_verifies_against_original(self, use_case, user_repo, valid_input):
        use_case.execute(valid_input)

        stored_user = user_repo.users[0]
        assert bcrypt.checkpw(
            valid_input.password.encode("utf-8"),
            stored_user.password_hash.encode("utf-8"),
        )
