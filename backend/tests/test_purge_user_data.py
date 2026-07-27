"""Tests for PurgeUserData service — ARCO cancellation data cleanup.

Verifies that account deletion purges:
- Digital files from storage
- Copies (physical + digital)
- Orphaned books
- Reviews
- Loans
- Audit log anonymization (beyond retention period)

Reference: privacy/requirements.md Req 1.2, 1.7
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.circulation.infrastructure.models import LoanModel
from app.identity.application.purge_user_data import (
    DEFAULT_AUDIT_RETENTION_DAYS,
    DELETED_USER_SENTINEL,
    PurgeUserData,
)
from app.identity.domain.entities import AuditAction, User
from app.identity.infrastructure.models import AuditLogModel, UserModel
from app.library.infrastructure.models import BookModel, CopyModel
from app.reviews.infrastructure.models import ReviewModel
from tests.conftest import TestSession


class InMemoryFileStorage:
    """Test double for FileStorage protocol."""

    def __init__(self):
        self.files: dict[str, bytes] = {}
        self.deleted: list[str] = []

    def upload(self, user_id, filename, content):
        ref = f"users/{user_id}/{filename}"
        self.files[ref] = content
        return ref

    def delete(self, file_ref: str) -> None:
        self.deleted.append(file_ref)
        self.files.pop(file_ref, None)


class TestPurgeDigitalFiles:
    """Digital files are deleted from storage when account is cancelled."""

    def test_digital_files_purged_on_deletion(self):
        """Req 1.2: Digital copies' files are removed from storage."""
        db = TestSession()
        try:
            storage = InMemoryFileStorage()
            user_id = uuid4()
            book_id = uuid4()

            # Create user
            db.add(UserModel(
                id=user_id, name="Test User", email="test@x.com", password_hash="h"
            ))

            # Create book
            db.add(BookModel(id=book_id, title="Test Book", author="Author"))

            # Upload a file and create a digital copy
            file_ref = storage.upload(user_id, "book.epub", b"epub-content")

            db.add(CopyModel(
                id=uuid4(),
                user_id=user_id,
                book_id=book_id,
                type="digital",
                file_ref=file_ref,
                status="available",
            ))
            db.flush()

            # Execute purge
            service = PurgeUserData(session=db, file_storage=storage)
            service.execute(user_id)
            db.flush()

            # File was deleted from storage
            assert file_ref in storage.deleted
            assert file_ref not in storage.files

            # Copy row is gone from DB
            copies = db.query(CopyModel).filter(CopyModel.user_id == user_id).all()
            assert copies == []
        finally:
            db.close()

    def test_multiple_digital_files_all_purged(self):
        """All digital files are purged, not just the first one."""
        db = TestSession()
        try:
            storage = InMemoryFileStorage()
            user_id = uuid4()
            book_id_1 = uuid4()
            book_id_2 = uuid4()

            db.add(UserModel(
                id=user_id, name="Multi", email="multi@x.com", password_hash="h"
            ))
            db.add(BookModel(id=book_id_1, title="Book 1", author="A"))
            db.add(BookModel(id=book_id_2, title="Book 2", author="B"))

            ref1 = storage.upload(user_id, "book1.pdf", b"pdf1")
            ref2 = storage.upload(user_id, "book2.epub", b"epub2")

            db.add(CopyModel(
                id=uuid4(), user_id=user_id, book_id=book_id_1,
                type="digital", file_ref=ref1, status="available",
            ))
            db.add(CopyModel(
                id=uuid4(), user_id=user_id, book_id=book_id_2,
                type="digital", file_ref=ref2, status="available",
            ))
            db.flush()

            service = PurgeUserData(session=db, file_storage=storage)
            service.execute(user_id)
            db.flush()

            assert ref1 in storage.deleted
            assert ref2 in storage.deleted
        finally:
            db.close()

    def test_physical_copies_deleted_no_file_access(self):
        """Physical copies are deleted but no file storage calls are made."""
        db = TestSession()
        try:
            storage = InMemoryFileStorage()
            user_id = uuid4()
            book_id = uuid4()

            db.add(UserModel(
                id=user_id, name="Phys", email="phys@x.com", password_hash="h"
            ))
            db.add(BookModel(id=book_id, title="Physical Book", author="A"))
            db.add(CopyModel(
                id=uuid4(), user_id=user_id, book_id=book_id,
                type="physical", file_ref=None, status="available",
            ))
            db.flush()

            service = PurgeUserData(session=db, file_storage=storage)
            service.execute(user_id)
            db.flush()

            # No file deletions attempted
            assert storage.deleted == []
            # But the copy row is gone
            copies = db.query(CopyModel).filter(CopyModel.user_id == user_id).all()
            assert copies == []
        finally:
            db.close()


class TestPurgeOrphanedBooks:
    """Books with no remaining copies are cleaned up."""

    def test_orphaned_book_deleted(self):
        """If user's copies were the only copies of a book, the book is deleted."""
        db = TestSession()
        try:
            storage = InMemoryFileStorage()
            user_id = uuid4()
            book_id = uuid4()

            db.add(UserModel(
                id=user_id, name="Orphan", email="orphan@x.com", password_hash="h"
            ))
            db.add(BookModel(id=book_id, title="Orphan Book", author="A"))
            db.add(CopyModel(
                id=uuid4(), user_id=user_id, book_id=book_id,
                type="physical", file_ref=None, status="available",
            ))
            db.flush()

            service = PurgeUserData(session=db, file_storage=storage)
            service.execute(user_id)
            db.flush()

            # Book should be deleted (no remaining copies)
            book = db.query(BookModel).filter(BookModel.id == book_id).first()
            assert book is None
        finally:
            db.close()

    def test_shared_book_not_deleted(self):
        """If another user also has a copy of the book, the book is preserved."""
        db = TestSession()
        try:
            storage = InMemoryFileStorage()
            user_id = uuid4()
            other_user_id = uuid4()
            book_id = uuid4()

            db.add(UserModel(
                id=user_id, name="Deleting", email="del@x.com", password_hash="h"
            ))
            db.add(UserModel(
                id=other_user_id, name="Keeper", email="keep@x.com", password_hash="h"
            ))
            db.add(BookModel(id=book_id, title="Shared Book", author="A"))
            db.add(CopyModel(
                id=uuid4(), user_id=user_id, book_id=book_id,
                type="physical", file_ref=None, status="available",
            ))
            db.add(CopyModel(
                id=uuid4(), user_id=other_user_id, book_id=book_id,
                type="physical", file_ref=None, status="available",
            ))
            db.flush()

            service = PurgeUserData(session=db, file_storage=storage)
            service.execute(user_id)
            db.flush()

            # Book is preserved (other user still has a copy)
            book = db.query(BookModel).filter(BookModel.id == book_id).first()
            assert book is not None
        finally:
            db.close()


class TestPurgeReviews:
    """User's reviews are deleted on account cancellation."""

    def test_reviews_deleted(self):
        """All reviews by the user are removed."""
        db = TestSession()
        try:
            storage = InMemoryFileStorage()
            user_id = uuid4()
            book_id = uuid4()

            db.add(UserModel(
                id=user_id, name="Reviewer", email="rev@x.com", password_hash="h"
            ))
            db.add(BookModel(id=book_id, title="Reviewed Book", author="A"))
            db.add(ReviewModel(
                id=uuid4(), user_id=user_id, book_id=book_id,
                rating=5, text="Great!", visibility="private",
            ))
            db.flush()

            service = PurgeUserData(session=db, file_storage=storage)
            service.execute(user_id)
            db.flush()

            reviews = db.query(ReviewModel).filter(ReviewModel.user_id == user_id).all()
            assert reviews == []
        finally:
            db.close()


class TestPurgeLoans:
    """User's loans are deleted on account cancellation."""

    def test_loans_deleted(self):
        """All loans where user is borrower are removed."""
        db = TestSession()
        try:
            storage = InMemoryFileStorage()
            user_id = uuid4()
            owner_id = uuid4()
            book_id = uuid4()
            copy_id = uuid4()

            db.add(UserModel(
                id=user_id, name="Borrower", email="borrow@x.com", password_hash="h"
            ))
            db.add(UserModel(
                id=owner_id, name="Owner", email="owner@x.com", password_hash="h"
            ))
            db.add(BookModel(id=book_id, title="Loaned Book", author="A"))
            db.add(CopyModel(
                id=copy_id, user_id=owner_id, book_id=book_id,
                type="physical", file_ref=None, status="on_loan",
            ))
            db.flush()  # Flush copies first so FK constraint is satisfied

            db.add(LoanModel(
                id=uuid4(), copy_id=copy_id, borrower_user_id=user_id,
                status="active",
            ))
            db.flush()

            service = PurgeUserData(session=db, file_storage=storage)
            service.execute(user_id)
            db.flush()

            loans = db.query(LoanModel).filter(
                LoanModel.borrower_user_id == user_id
            ).all()
            assert loans == []
        finally:
            db.close()


class TestAnonymizeAuditLogs:
    """Audit logs older than retention period are anonymized."""

    def test_old_audit_logs_anonymized(self):
        """Logs older than retention period get actor_user_id set to zero UUID."""
        db = TestSession()
        try:
            storage = InMemoryFileStorage()
            user_id = uuid4()

            db.add(UserModel(
                id=user_id, name="Audited", email="audit@x.com", password_hash="h"
            ))

            # Create an old audit log (60 days ago — older than 30-day retention)
            old_timestamp = datetime.now(timezone.utc) - timedelta(days=60)
            old_log_id = uuid4()
            db.add(AuditLogModel(
                id=old_log_id,
                actor_user_id=user_id,
                action="user_login",
                affected_entity=f"user:{user_id}:login",
                timestamp=old_timestamp,
            ))
            db.flush()

            service = PurgeUserData(session=db, file_storage=storage)
            service.execute(user_id)
            db.flush()

            # Old log is anonymized
            log = db.query(AuditLogModel).filter(AuditLogModel.id == old_log_id).first()
            assert log.actor_user_id == DELETED_USER_SENTINEL
        finally:
            db.close()

    def test_recent_audit_logs_preserved(self):
        """Logs within retention period keep their original actor_user_id."""
        db = TestSession()
        try:
            storage = InMemoryFileStorage()
            user_id = uuid4()

            db.add(UserModel(
                id=user_id, name="Recent", email="recent@x.com", password_hash="h"
            ))

            # Create a recent audit log (5 days ago — within 30-day retention)
            recent_timestamp = datetime.now(timezone.utc) - timedelta(days=5)
            recent_log_id = uuid4()
            db.add(AuditLogModel(
                id=recent_log_id,
                actor_user_id=user_id,
                action="file_uploaded",
                affected_entity=f"user:{user_id}:file",
                timestamp=recent_timestamp,
            ))
            db.flush()

            service = PurgeUserData(session=db, file_storage=storage)
            service.execute(user_id)
            db.flush()

            # Recent log keeps its actor_user_id
            log = db.query(AuditLogModel).filter(AuditLogModel.id == recent_log_id).first()
            assert log.actor_user_id == user_id
        finally:
            db.close()

    def test_custom_retention_days(self):
        """Retention period is configurable — not hardcoded."""
        db = TestSession()
        try:
            storage = InMemoryFileStorage()
            user_id = uuid4()

            db.add(UserModel(
                id=user_id, name="Custom", email="custom@x.com", password_hash="h"
            ))

            # Create a log that's 10 days old
            ten_days_ago = datetime.now(timezone.utc) - timedelta(days=10)
            log_id = uuid4()
            db.add(AuditLogModel(
                id=log_id,
                actor_user_id=user_id,
                action="user_login",
                affected_entity=f"user:{user_id}:login",
                timestamp=ten_days_ago,
            ))
            db.flush()

            # With 7-day retention, this 10-day-old log SHOULD be anonymized
            service_short = PurgeUserData(
                session=db, file_storage=storage, audit_retention_days=7
            )
            service_short.execute(user_id)
            db.flush()

            log = db.query(AuditLogModel).filter(AuditLogModel.id == log_id).first()
            assert log.actor_user_id == DELETED_USER_SENTINEL
        finally:
            db.close()
