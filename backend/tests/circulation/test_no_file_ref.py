"""Regression test: no loans endpoint ever accepts or returns a digital file_ref.

This test verifies compliance with:
- ADR-0001: No shared file storage between accounts
- ADR-0009: Digital books strict isolation
- Requirement 1.3: No digital file transfer under any "loan" concept

Reference: loans/design.md, Testing Strategy
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
    from app.identity.infrastructure.models import UserModel

    uid = user_id or uuid4()
    user = UserModel(
        id=uid, name="Test User", email=f"{uid}@test.com", password_hash="hashed"
    )
    db.add(user)
    db.flush()
    return uid


def _create_book(db: Session):
    book_id = uuid4()
    book = BookModel(id=book_id, title="Test Book", author="Author")
    db.add(book)
    db.flush()
    return book_id


def _create_physical_copy(db: Session, user_id, book_id):
    copy_id = uuid4()
    copy = CopyModel(
        id=copy_id,
        user_id=user_id,
        book_id=book_id,
        type="physical",
        file_ref=None,
        status="available",
    )
    db.add(copy)
    db.flush()
    return copy_id


class TestNoFileRefInLoans:
    """Verify that no endpoint in the loans module exposes or accepts file_ref."""

    def test_create_loan_response_has_no_file_ref_field(self, db_session):
        """POST /copies/{id}/loans response must not contain file_ref."""
        headers, owner_id = _get_auth_header()
        borrower_id = _create_user(db_session, uuid4())
        _create_user(db_session, owner_id)
        book_id = _create_book(db_session)
        copy_id = _create_physical_copy(db_session, owner_id, book_id)
        db_session.commit()

        response = client.post(
            f"/copies/{copy_id}/loans",
            json={"borrower_user_id": str(borrower_id)},
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "file_ref" not in data
        assert "file" not in data
        assert "content" not in data

    def test_return_loan_response_has_no_file_ref_field(self, db_session):
        """PATCH /loans/{id}/return response must not contain file_ref."""
        headers, owner_id = _get_auth_header()
        borrower_id = _create_user(db_session, uuid4())
        _create_user(db_session, owner_id)
        book_id = _create_book(db_session)
        copy_id = _create_physical_copy(db_session, owner_id, book_id)
        db_session.commit()

        # Create loan first
        create_response = client.post(
            f"/copies/{copy_id}/loans",
            json={"borrower_user_id": str(borrower_id)},
            headers=headers,
        )
        assert create_response.status_code == 201
        loan_id = create_response.json()["id"]

        # Return loan
        response = client.patch(
            f"/loans/{loan_id}/return",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "file_ref" not in data
        assert "file" not in data
        assert "content" not in data

    def test_digital_copy_cannot_be_loaned(self, db_session):
        """POST /copies/{id}/loans rejects digital copies — no file access possible."""
        headers, owner_id = _get_auth_header()
        borrower_id = _create_user(db_session, uuid4())
        _create_user(db_session, owner_id)
        book_id = _create_book(db_session)

        # Create a digital copy
        digital_copy_id = uuid4()
        digital_copy = CopyModel(
            id=digital_copy_id,
            user_id=owner_id,
            book_id=book_id,
            type="digital",
            file_ref=f"users/{owner_id}/secret_book.epub",
            status="available",
        )
        db_session.add(digital_copy)
        db_session.commit()

        response = client.post(
            f"/copies/{digital_copy_id}/loans",
            json={"borrower_user_id": str(borrower_id)},
            headers=headers,
        )

        # Must reject — no digital loans allowed
        assert response.status_code == 422
        assert response.json()["detail"] == "invalid_copy_type"

    def test_create_loan_request_body_has_no_file_ref_field(self, db_session):
        """POST /copies/{id}/loans ignores any file_ref in request body."""
        headers, owner_id = _get_auth_header()
        borrower_id = _create_user(db_session, uuid4())
        _create_user(db_session, owner_id)
        book_id = _create_book(db_session)
        copy_id = _create_physical_copy(db_session, owner_id, book_id)
        db_session.commit()

        # Try to sneak file_ref in request body — should be ignored
        response = client.post(
            f"/copies/{copy_id}/loans",
            json={
                "borrower_user_id": str(borrower_id),
                "file_ref": "users/someone/evil.epub",
            },
            headers=headers,
        )

        # Should still succeed (extra fields ignored by Pydantic)
        assert response.status_code == 201
        data = response.json()
        assert "file_ref" not in data
