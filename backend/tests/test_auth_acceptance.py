"""Comprehensive acceptance tests for the Authentication & Groups module.

Maps every acceptance criterion and correctness property in the spec to at least
one test. Self-contained — no dependencies on other test files.

Reference: .kiro/specs/authentication/requirements.md, design.md
"""

import os
from datetime import timedelta
from uuid import uuid4

# Override DATABASE_URL before any app import so the engine uses SQLite
os.environ["DATABASE_URL"] = "sqlite:///file::memory:?cache=shared"

import bcrypt  # noqa: E402
import jwt as pyjwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.auth.jwt import create_access_token  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

# --- Test infrastructure ---

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


# --- Helpers ---


def _register(
    email="maria@example.com",
    password="SecurePass123!",
    name="María García",
):
    """Register a user and return response."""
    return client.post(
        "/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password,
            "consent_policy_version": "1.0",
            "consent_purpose": "account_creation",
        },
    )


def _login(email="maria@example.com", password="SecurePass123!"):
    """Login and return response."""
    return client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )


def _auth_header(token: str) -> dict:
    """Create Authorization header from an access token."""
    return {"Authorization": f"Bearer {token}"}


def _register_and_login(email="maria@example.com", password="SecurePass123!"):
    """Register + login, returning (user_id, access_token, refresh_token)."""
    reg = _register(email=email, password=password)
    user_id = reg.json()["id"]
    login_resp = _login(email=email, password=password)
    data = login_resp.json()
    return user_id, data["access_token"], data["refresh_token"]


# =============================================================================
# Section 1: End-to-End Flow Test
# =============================================================================


class TestEndToEndAuthLifecycle:
    """Complete authentication lifecycle in a single test flow.

    Steps: Register → Login → Use token → Refresh → Logout → Verify revocation → Re-login
    """

    def test_full_authentication_lifecycle(self):
        # 1. Register with consent → get user data
        reg_response = _register()
        assert reg_response.status_code == 201
        user_data = reg_response.json()
        assert "id" in user_data
        assert user_data["email"] == "maria@example.com"

        # 2. Login → get access + refresh tokens
        login_response = _login()
        assert login_response.status_code == 200
        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        assert access_token
        assert refresh_token

        # 3. Use access token on authenticated endpoint → success
        export_response = client.get(
            "/users/me/export",
            headers=_auth_header(access_token),
        )
        assert export_response.status_code == 200
        assert export_response.json()["user"]["email"] == "maria@example.com"

        # 4. Refresh token → get new token pair, old refresh token invalid
        refresh_response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        new_refresh_token = new_tokens["refresh_token"]
        assert new_refresh_token != refresh_token

        # Old refresh token should be invalid now
        old_refresh_response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert old_refresh_response.status_code == 401

        # 5. Logout → revoke new refresh token
        logout_response = client.post(
            "/auth/logout",
            json={"refresh_token": new_refresh_token},
        )
        assert logout_response.status_code == 200

        # 6. Try refresh with revoked token → 401
        revoked_refresh = client.post(
            "/auth/refresh",
            json={"refresh_token": new_refresh_token},
        )
        assert revoked_refresh.status_code == 401

        # 7. Try login again → still works (only token was revoked, not account)
        re_login = _login()
        assert re_login.status_code == 200
        assert re_login.json()["access_token"]


# =============================================================================
# Section 2: Correctness Properties
# =============================================================================


class TestProperty1ConsentGating:
    """Property 1: User row is never created without a corresponding DataConsent row.

    **Validates: Requirements 1.1**
    """

    def test_registration_without_consent_fields_creates_no_user(self):
        """Registration without consent returns error AND no user is created in DB."""
        payload = {
            "name": "Test User",
            "email": "noconsent@example.com",
            "password": "SecurePass123!",
            # Missing consent_policy_version and consent_purpose
        }
        response = client.post("/auth/register", json=payload)
        assert response.status_code == 422

        # Verify no user exists in the database
        login_attempt = _login(email="noconsent@example.com", password="SecurePass123!")
        assert login_attempt.status_code == 401

    def test_consent_recorded_on_successful_registration(self):
        """Consent IS recorded when registration succeeds — verified via export."""
        _register()
        login_resp = _login()
        access_token = login_resp.json()["access_token"]

        # Export should contain the consent record
        export_resp = client.get(
            "/users/me/export",
            headers=_auth_header(access_token),
        )
        assert export_resp.status_code == 200
        data = export_resp.json()
        assert len(data["consents"]) >= 1
        assert data["consents"][0]["policy_version"] == "1.0"
        assert data["consents"][0]["purpose"] == "account_creation"


class TestProperty2InvitationStateMachine:
    """Property 2: GroupMembership.status can only go invited→accepted via explicit action.

    **Validates: Requirements 3.2**
    """

    def test_no_direct_accepted_membership_via_invite_endpoint(self):
        """Invitation endpoint always creates status=invited, never accepted."""
        creator_id = uuid4()
        invitee_id = uuid4()
        token = create_access_token(str(creator_id))

        # Create group
        group_resp = client.post(
            "/groups/",
            json={"name": "Test Family"},
            headers=_auth_header(token),
        )
        assert group_resp.status_code == 201
        group_id = group_resp.json()["id"]

        # Invite a user
        invite_resp = client.post(
            f"/groups/{group_id}/invitations",
            json={"user_id": str(invitee_id)},
            headers=_auth_header(token),
        )
        assert invite_resp.status_code == 201
        assert invite_resp.json()["status"] == "invited"

    def test_creator_membership_auto_accepted_through_use_case(self):
        """The creator's membership is auto-accepted, but through the use case (exception)."""
        creator_id = uuid4()
        token = create_access_token(str(creator_id))

        group_resp = client.post(
            "/groups/",
            json={"name": "Family García"},
            headers=_auth_header(token),
        )
        assert group_resp.status_code == 201

        # The creator is automatically an accepted member — verified by ability to invite
        group_id = group_resp.json()["id"]
        invitee_id = uuid4()
        invite_resp = client.post(
            f"/groups/{group_id}/invitations",
            json={"user_id": str(invitee_id)},
            headers=_auth_header(token),
        )
        # If the creator wasn't accepted, this would return 403
        assert invite_resp.status_code == 201


class TestProperty3StatelessTokenValidation:
    """Property 3: Access token validation never requires a DB lookup.

    **Validates: Requirements 2.2**
    """

    def test_valid_jwt_for_nonexistent_user_passes_auth_check(self):
        """A valid JWT for a user_id not in DB still passes the auth dependency.

        The endpoint may fail for other reasons (use case can't find user),
        but the AUTH step succeeds (no DB lookup for token validation).
        """
        # Create a token for a user_id that doesn't exist in the database
        fake_user_id = uuid4()
        token = create_access_token(str(fake_user_id))

        # Try to access export — auth check passes, but use case returns 404
        response = client.get(
            "/users/me/export",
            headers=_auth_header(token),
        )
        # 404 means auth succeeded but user not found — confirms stateless validation
        assert response.status_code == 404
        assert response.json()["detail"] == "user_not_found"


class TestProperty4RefreshTokenRotationAtomicity:
    """Property 4: Rotation always invalidates previous token atomically.

    **Validates: Requirements 2.3**
    """

    def test_old_token_immediately_unusable_after_rotation(self):
        """After rotation, the OLD token is immediately unusable."""
        _, _, refresh_token = _register_and_login()

        # Rotate
        rotate_resp = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert rotate_resp.status_code == 200

        # Old token immediately fails
        replay_resp = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert replay_resp.status_code == 401

    def test_rapid_sequential_rotations(self):
        """Rapid sequential rotations — each new token works, all old ones fail."""
        _, _, refresh_token = _register_and_login(email="rapid@example.com")

        old_tokens = [refresh_token]
        current_token = refresh_token

        # Rotate 5 times rapidly
        for _ in range(5):
            resp = client.post(
                "/auth/refresh",
                json={"refresh_token": current_token},
            )
            assert resp.status_code == 200
            old_tokens.append(current_token)
            current_token = resp.json()["refresh_token"]

        # Current token should still work
        final_resp = client.post(
            "/auth/refresh",
            json={"refresh_token": current_token},
        )
        assert final_resp.status_code == 200

        # All old tokens should fail
        for old_token in old_tokens:
            fail_resp = client.post(
                "/auth/refresh",
                json={"refresh_token": old_token},
            )
            assert fail_resp.status_code == 401


class TestProperty5RevocationEnforcement:
    """Property 5: Revoked refresh token can never be used to obtain new tokens.

    **Validates: Requirements 2.4**
    """

    def test_logout_makes_refresh_fail(self):
        """After logout, refresh fails with correct error."""
        _, _, refresh_token = _register_and_login(email="logout@example.com")

        # Logout
        client.post("/auth/logout", json={"refresh_token": refresh_token})

        # Try to refresh
        resp = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "token_revoked"

    def test_account_deletion_revokes_all_tokens(self):
        """After account deletion, all tokens are revoked."""
        _, access_token, refresh_token = _register_and_login(email="delme@example.com")

        # Delete account
        delete_resp = client.delete(
            "/users/me",
            headers=_auth_header(access_token),
        )
        assert delete_resp.status_code == 200

        # Refresh should fail (token revoked as part of deletion)
        refresh_resp = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 401


# =============================================================================
# Section 3: Security Tests
# =============================================================================


class TestNoUserEnumeration:
    """Security: identical responses for wrong email vs wrong password."""

    def test_wrong_email_and_wrong_password_produce_identical_responses(self):
        """Login with WRONG EMAIL and WRONG PASSWORD produce identical HTTP status + body."""
        _register()

        resp_bad_email = client.post(
            "/auth/login",
            json={"email": "nonexistent@example.com", "password": "SecurePass123!"},
        )
        resp_bad_pass = client.post(
            "/auth/login",
            json={"email": "maria@example.com", "password": "WrongPassword999!"},
        )

        # Same status code
        assert resp_bad_email.status_code == resp_bad_pass.status_code == 401
        # Same response body (no difference that leaks which field was wrong)
        assert resp_bad_email.json() == resp_bad_pass.json()


class TestExpiredAccessToken:
    """Security: expired access token is rejected."""

    def test_expired_access_token_returns_401(self):
        """Access token with negative expiry is rejected."""
        user_id, _, _ = _register_and_login(email="expired@example.com")

        # Create an expired token (negative timedelta)
        expired_token = create_access_token(
            user_id=user_id,
            expires_delta=timedelta(seconds=-1),
        )

        response = client.get(
            "/users/me/export",
            headers=_auth_header(expired_token),
        )
        assert response.status_code == 401


class TestTokenFormatValidation:
    """Security: malformed Authorization headers and wrong-secret JWTs rejected."""

    def test_basic_auth_scheme_rejected(self):
        """'Basic xxx' Authorization header is rejected."""
        response = client.get(
            "/users/me/export",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        assert response.status_code == 401

    def test_bearer_without_token_rejected(self):
        """'Bearer ' (with trailing space, no token) is rejected."""
        response = client.get(
            "/users/me/export",
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code == 401

    def test_empty_authorization_header_rejected(self):
        """Empty string Authorization header is rejected."""
        response = client.get(
            "/users/me/export",
            headers={"Authorization": ""},
        )
        assert response.status_code == 401

    def test_jwt_signed_with_wrong_secret_rejected(self):
        """A valid-format JWT signed with a WRONG secret returns 401."""
        payload = {
            "sub": str(uuid4()),
            "exp": 9999999999,
            "iat": 1700000000,
            "type": "access",
        }
        wrong_secret_token = pyjwt.encode(payload, "wrong-secret-key", algorithm="HS256")

        response = client.get(
            "/users/me/export",
            headers=_auth_header(wrong_secret_token),
        )
        assert response.status_code == 401


# =============================================================================
# Section 4: Acceptance Criteria Checklist
# =============================================================================


class TestAcceptanceCriteriaChecklist:
    """Individual tests named after each acceptance criterion for traceability."""

    def test_req1_1_consent_required_before_account_creation(self):
        """Req 1.1: Registration without consent is blocked."""
        payload = {
            "name": "No Consent User",
            "email": "noconsent@test.com",
            "password": "SecurePass123!",
        }
        response = client.post("/auth/register", json=payload)
        assert response.status_code == 422

        # Confirm no user was created
        login_resp = _login(email="noconsent@test.com", password="SecurePass123!")
        assert login_resp.status_code == 401

    def test_req1_2_consent_records_timestamp_and_policy_version(self):
        """Req 1.2: DataConsent has timestamp and policy_version."""
        _register(email="consent@test.com")
        login_resp = _login(email="consent@test.com")
        token = login_resp.json()["access_token"]

        export_resp = client.get(
            "/users/me/export",
            headers=_auth_header(token),
        )
        data = export_resp.json()
        consent = data["consents"][0]
        assert "timestamp" in consent
        assert consent["policy_version"] == "1.0"

    def test_req1_3_password_stored_as_bcrypt_hash(self):
        """Req 1.3: Password is stored as bcrypt hash, never plaintext."""
        _register(email="bcrypt@test.com", password="MyPassword123!")

        # Verify via direct DB query
        db = TestSession()
        try:
            result = db.execute(
                text("SELECT password_hash FROM users WHERE email = :email"),
                {"email": "bcrypt@test.com"},
            ).fetchone()
            assert result is not None
            password_hash = result[0]

            # Verify it's a bcrypt hash (starts with $2b$)
            assert password_hash.startswith("$2b$")
            # Verify it validates correctly
            assert bcrypt.checkpw(
                "MyPassword123!".encode("utf-8"),
                password_hash.encode("utf-8"),
            )
        finally:
            db.close()

    def test_req2_1_login_issues_access_and_refresh_tokens(self):
        """Req 2.1: Successful login returns Access Token + Refresh Token."""
        _register(email="tokens@test.com")
        response = _login(email="tokens@test.com")

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["token_type"] == "bearer"

    def test_req2_2_access_token_validated_without_db_lookup(self):
        """Req 2.2: Access token validation is stateless (no DB lookup)."""
        # A token for a non-existent user still passes auth (stateless)
        fake_user_id = uuid4()
        token = create_access_token(str(fake_user_id))

        response = client.get(
            "/users/me/export",
            headers=_auth_header(token),
        )
        # Auth passes (stateless), but endpoint returns 404 (user not in DB)
        assert response.status_code == 404

    def test_req2_3_refresh_rotates_and_invalidates_previous(self):
        """Req 2.3: Refresh rotation issues new token, invalidates old."""
        _, _, refresh_token = _register_and_login(email="rotate@test.com")

        resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        new_refresh = resp.json()["refresh_token"]
        assert new_refresh != refresh_token

        # Old token is now invalid
        old_resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert old_resp.status_code == 401

    def test_req2_4_logout_revokes_refresh_token(self):
        """Req 2.4: Logout revokes the refresh token."""
        _, _, refresh_token = _register_and_login(email="revoke@test.com")

        logout_resp = client.post("/auth/logout", json={"refresh_token": refresh_token})
        assert logout_resp.status_code == 200

        refresh_resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh_resp.status_code == 401

    def test_req2_5_expired_or_revoked_tokens_rejected(self):
        """Req 2.5: Expired or revoked tokens return 401."""
        user_id, _, refresh_token = _register_and_login(email="reject@test.com")

        # Expired access token
        expired_token = create_access_token(user_id, expires_delta=timedelta(seconds=-1))
        resp = client.get("/users/me/export", headers=_auth_header(expired_token))
        assert resp.status_code == 401

        # Revoked refresh token
        client.post("/auth/logout", json={"refresh_token": refresh_token})
        refresh_resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh_resp.status_code == 401

    def test_req3_1_can_create_group_and_invite(self):
        """Req 3.1: Can create a family group and invite other profiles."""
        creator_id = uuid4()
        invitee_id = uuid4()
        token = create_access_token(str(creator_id))

        # Create group
        group_resp = client.post(
            "/groups/",
            json={"name": "Familia García"},
            headers=_auth_header(token),
        )
        assert group_resp.status_code == 201
        group_id = group_resp.json()["id"]

        # Invite
        invite_resp = client.post(
            f"/groups/{group_id}/invitations",
            json={"user_id": str(invitee_id)},
            headers=_auth_header(token),
        )
        assert invite_resp.status_code == 201

    def test_req3_2_never_joins_without_explicit_acceptance(self):
        """Req 3.2: Invited profile never joins without explicitly accepting."""
        creator_id = uuid4()
        invitee_id = uuid4()
        creator_token = create_access_token(str(creator_id))

        # Create group + invite
        group_resp = client.post(
            "/groups/",
            json={"name": "Club de Lectura"},
            headers=_auth_header(creator_token),
        )
        group_id = group_resp.json()["id"]

        invite_resp = client.post(
            f"/groups/{group_id}/invitations",
            json={"user_id": str(invitee_id)},
            headers=_auth_header(creator_token),
        )
        invitation = invite_resp.json()
        assert invitation["status"] == "invited"  # Not "accepted"

        # Invitee must explicitly accept
        invitee_token = create_access_token(str(invitee_id))
        accept_resp = client.post(
            f"/groups/{group_id}/invitations/{invitation['id']}/accept",
            headers=_auth_header(invitee_token),
        )
        assert accept_resp.status_code == 200
        assert accept_resp.json()["status"] == "accepted"

    def test_req4_1_can_export_and_delete_without_support(self):
        """Req 4.1: Export and delete account from user's own profile, no support needed."""
        _, access_token, _ = _register_and_login(email="selfservice@test.com")

        # Export works directly
        export_resp = client.get(
            "/users/me/export",
            headers=_auth_header(access_token),
        )
        assert export_resp.status_code == 200

        # Delete works directly
        delete_resp = client.delete(
            "/users/me",
            headers=_auth_header(access_token),
        )
        assert delete_resp.status_code == 200
        assert delete_resp.json()["detail"] == "account_deleted"

    def test_req4_2_arco_export_includes_all_identity_data(self):
        """Req 4.2: Export includes all identity-owned personal data."""
        _, access_token, _ = _register_and_login(email="arco@test.com")

        export_resp = client.get(
            "/users/me/export",
            headers=_auth_header(access_token),
        )
        assert export_resp.status_code == 200
        data = export_resp.json()

        # Verify structured export contains all expected sections
        assert "user" in data
        assert "consents" in data
        assert "memberships" in data
        assert "processing_records" in data

        # User section has required fields
        assert data["user"]["name"] == "María García"
        assert data["user"]["email"] == "arco@test.com"
        assert "created_at" in data["user"]

        # Consent from registration is present
        assert len(data["consents"]) >= 1
