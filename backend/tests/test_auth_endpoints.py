"""Tests for auth endpoints: POST /auth/register and POST /auth/consent.

Uses PostgreSQL database via shared conftest.py fixtures.
Reference: authentication/tasks.md#3, requirements.md Req 1
"""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _register_payload(
    name="María García",
    email="maria@example.com",
    password="SecurePass123!",
    consent_policy_version="1.0",
    consent_purpose="account_creation",
):
    return {
        "name": name,
        "email": email,
        "password": password,
        "consent_policy_version": consent_policy_version,
        "consent_purpose": consent_purpose,
    }


class TestRegisterHappyPath:
    """POST /auth/register — successful registration."""

    def test_returns_201(self):
        response = client.post("/auth/register", json=_register_payload())
        assert response.status_code == 201

    def test_returns_user_data(self):
        response = client.post("/auth/register", json=_register_payload())
        data = response.json()

        assert data["name"] == "María García"
        assert data["email"] == "maria@example.com"
        assert "id" in data
        assert "created_at" in data

    def test_does_not_expose_password(self):
        response = client.post("/auth/register", json=_register_payload())
        data = response.json()

        assert "password" not in data
        assert "password_hash" not in data


class TestRegisterWithoutConsent:
    """POST /auth/register — missing consent rejected with 400."""

    def test_missing_consent_policy_version(self):
        payload = _register_payload(consent_policy_version="")
        response = client.post("/auth/register", json=payload)
        # Pydantic validation rejects empty string (min_length=1)
        assert response.status_code == 422

    def test_missing_consent_purpose(self):
        payload = _register_payload(consent_purpose="")
        response = client.post("/auth/register", json=payload)
        assert response.status_code == 422

    def test_null_consent_fields_rejected(self):
        payload = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "SecurePass123!",
        }
        response = client.post("/auth/register", json=payload)
        assert response.status_code == 422


class TestRegisterDuplicateEmail:
    """POST /auth/register — duplicate email returns 409."""

    def test_duplicate_email_returns_409(self):
        client.post("/auth/register", json=_register_payload())
        response = client.post("/auth/register", json=_register_payload())

        assert response.status_code == 409
        assert response.json()["detail"] == "email_already_exists"


class TestConsentEndpoint:
    """POST /auth/consent — standalone consent recording."""

    def test_returns_201(self):
        # First register a user to get a valid user_id
        reg_response = client.post("/auth/register", json=_register_payload())
        user_id = reg_response.json()["id"]

        payload = {
            "user_id": user_id,
            "policy_version": "2.0",
            "purpose": "marketing_emails",
        }
        response = client.post("/auth/consent", json=payload)
        assert response.status_code == 201

    def test_returns_consent_data(self):
        reg_response = client.post("/auth/register", json=_register_payload())
        user_id = reg_response.json()["id"]

        payload = {
            "user_id": user_id,
            "policy_version": "2.0",
            "purpose": "marketing_emails",
        }
        response = client.post("/auth/consent", json=payload)
        data = response.json()

        assert data["user_id"] == user_id
        assert data["policy_version"] == "2.0"
        assert data["purpose"] == "marketing_emails"
        assert "id" in data
        assert "timestamp" in data

    def test_consent_with_arbitrary_user_id(self):
        """Consent can be recorded for any user_id."""
        user_id = str(uuid4())
        payload = {
            "user_id": user_id,
            "policy_version": "1.0",
            "purpose": "data_analytics",
        }
        response = client.post("/auth/consent", json=payload)
        assert response.status_code == 201
