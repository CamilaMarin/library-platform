"""Integration tests for RegisterLoan use case and POST /copies/{id}/loans endpoint.

Tests:
- Successful loan for physical copy (201)
- Rejection for digital copy (422, "invalid_copy_type")
- Rejection when copy already on loan (409)
- Copy not found (404)
- Loan with estimated return date

Reference: loans/design.md, Requirements 1.1, 1.3
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.database import get_db
from app.library.infrastructure.models import BookModel, CopyModel
from app.main import app

client = TestClient(app)


def _get_auth_header(user_id=None):
    """Create a valid auth token for testing."""
    uid = user_id or uuid4()
    token = create_access_token(str(uid))
    return {"Authorization": f"Bearer {token}"}, uid


@pytest.fixture
def db_session():
    """Get a test database session that is properly managed."""
    gen = app.dependency_overrides[get_db]()
    session = next(gen)
    yield session
    try:
        next(gen)
    except StopIteration:
        pass


def _create_user(db: Session, user_id=None):
    """Insert a minimal user row for FK constraints."""
    from app.identity.infrastructure.models import UserModel

    uid = user_id or uuid4()
    user = UserModel(
        id=uid, name="Test User", email=f"{uid}@test.com", password_hash="hashed"
    )
    db.add(user)
    db.flush()
    return uid


def _create_book(db: Session):
    """Insert a minimal book row for FK constraints."""
    book_id = uuid4()
    book = BookModel(id=book_id, title="Test Book", author="Test Author")
    db.add(book)
    db.flush()
    return book_id


def _create_copy(db: Session, user_id, book_id, copy_type="physical"):
    """Insert a copy row."""
    copy_id = uuid4()
    file_ref = f"users/{user_id}/test.epub" if copy_type == "digital" else None
    copy = CopyModel(
        id=copy_id,
        user_id=user_id,
        book_id=book_id,
        type=copy_type,
        file_ref=file_ref,
        status="available",
    )
    db.add(copy)
    db.flush()
    return copy_id


class TestRegisterLoanEndpoint:
    """Integration tests for POST /copies/{copy_id}/loans."""

    def test_successful_loan_for_physical_copy(self, db_session):
        """201: Loan is created for a physical copy, status transitions to on_loan."""
        headers, owner_id = _get_auth_header()
        borrower_id = _create_user(db_session, uuid4())
        _create_user(db_session, owner_id)
        book_id = _create_book(db_session)
        copy_id = _create_copy(db_session, owner_id, book_id, "physical")
        db_session.commit()

        response = client.post(
            f"/copies/{copy_id}/loans",
            json={"borrower_user_id": str(borrower_id)},
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["copy_id"] == str(copy_id)
        assert data["borrower_user_id"] == str(borrower_id)
        assert data["status"] == "active"
        assert data["returned_date"] is None

        # Verify copy status was updated to on_loan
        db_session.expire_all()
        copy_model = db_session.get(CopyModel, copy_id)
        assert copy_model.status == "on_loan"

    def test_rejection_for_digital_copy(self, db_session):
        """422: Digital copies cannot be loaned (Req 1.3)."""
        headers, owner_id = _get_auth_header()
        borrower_id = _create_user(db_session, uuid4())
        _create_user(db_session, owner_id)
        book_id = _create_book(db_session)
        copy_id = _create_copy(db_session, owner_id, book_id, "digital")
        db_session.commit()

        response = client.post(
            f"/copies/{copy_id}/loans",
            json={"borrower_user_id": str(borrower_id)},
            headers=headers,
        )

        assert response.status_code == 422
        assert response.json()["detail"] == "invalid_copy_type"

    def test_rejection_when_copy_already_on_loan(self, db_session):
        """409: Cannot loan a copy that already has an active loan."""
        headers, owner_id = _get_auth_header()
        borrower_id = _create_user(db_session, uuid4())
        another_borrower_id = _create_user(db_session, uuid4())
        _create_user(db_session, owner_id)
        book_id = _create_book(db_session)
        copy_id = _create_copy(db_session, owner_id, book_id, "physical")
        db_session.commit()

        # First loan succeeds
        response = client.post(
            f"/copies/{copy_id}/loans",
            json={"borrower_user_id": str(borrower_id)},
            headers=headers,
        )
        assert response.status_code == 201

        # Second loan on same copy fails
        response = client.post(
            f"/copies/{copy_id}/loans",
            json={"borrower_user_id": str(another_borrower_id)},
            headers=headers,
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "copy_already_on_loan"

    def test_copy_not_found(self):
        """404: Non-existent copy returns 404."""
        headers, _ = _get_auth_header()
        non_existent_copy_id = uuid4()

        response = client.post(
            f"/copies/{non_existent_copy_id}/loans",
            json={"borrower_user_id": str(uuid4())},
            headers=headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Copy not found"

    def test_successful_loan_with_estimated_return_date(self, db_session):
        """201: Loan with estimated return date is recorded correctly."""
        headers, owner_id = _get_auth_header()
        borrower_id = _create_user(db_session, uuid4())
        _create_user(db_session, owner_id)
        book_id = _create_book(db_session)
        copy_id = _create_copy(db_session, owner_id, book_id, "physical")
        db_session.commit()

        response = client.post(
            f"/copies/{copy_id}/loans",
            json={
                "borrower_user_id": str(borrower_id),
                "estimated_return_date": "2030-08-15T00:00:00Z",
            },
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["estimated_return_date"] is not None
        assert "2030-08-15" in data["estimated_return_date"]
