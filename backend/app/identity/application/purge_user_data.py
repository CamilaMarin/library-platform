"""PurgeUserData service — cross-cutting data cleanup for ARCO cancellation.

When a user exercises their cancellation right (DELETE /users/me), this service
purges all user-owned data across bounded contexts:
- Digital files from storage (MinIO/local)
- Copies (physical + digital) from the library
- Books with no remaining copies
- Reviews
- Loans
- Audit log anonymization (beyond minimum legal retention)

This is intentionally cross-cutting: it operates at the DB/storage level because
account deletion requires coordinating cleanup across all modules.

Reference: privacy/requirements.md Req 1.2, 1.7
"""

from datetime import datetime, timedelta, timezone
from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from app.circulation.infrastructure.models import LoanModel
from app.identity.infrastructure.models import AuditLogModel
from app.library.infrastructure.models import BookModel, CopyModel
from app.reviews.infrastructure.models import ReviewModel


# Zero UUID used as anonymized placeholder for deleted users in audit logs
DELETED_USER_SENTINEL = UUID("00000000-0000-0000-0000-000000000000")

# Default minimum legal retention for audit logs (days).
# Logs newer than this are kept with the original actor_user_id intact.
# Configurable via RetentionPolicy table (data_type="audit_logs").
DEFAULT_AUDIT_RETENTION_DAYS = 30


class FileStorage(Protocol):
    """Protocol for file deletion — matches library FileStorage interface."""

    def delete(self, file_ref: str) -> None: ...


class PurgeUserData:
    """Service that purges all user data across bounded contexts on account cancellation.

    Order of operations:
    1. Delete digital files from storage
    2. Delete user's copies (physical + digital)
    3. Delete orphaned books (books with no remaining copies)
    4. Delete user's reviews
    5. Delete user's loans
    6. Anonymize old audit logs (beyond retention period)
    """

    def __init__(
        self,
        session: Session,
        file_storage: FileStorage,
        audit_retention_days: int = DEFAULT_AUDIT_RETENTION_DAYS,
    ):
        self._session = session
        self._file_storage = file_storage
        self._audit_retention_days = audit_retention_days

    def execute(self, user_id: UUID) -> None:
        """Purge all cross-context data for the given user."""
        self._purge_digital_files(user_id)
        orphaned_book_ids = self._get_orphaned_book_ids(user_id)
        self._delete_copies(user_id)
        self._delete_orphaned_books(orphaned_book_ids)
        self._delete_reviews(user_id)
        self._delete_loans(user_id)
        self._anonymize_audit_logs(user_id)

    def _purge_digital_files(self, user_id: UUID) -> None:
        """Delete all digital files from storage for the user's digital copies."""
        digital_copies = (
            self._session.query(CopyModel)
            .filter(CopyModel.user_id == user_id, CopyModel.type == "digital")
            .all()
        )
        for copy in digital_copies:
            if copy.file_ref:
                try:
                    self._file_storage.delete(copy.file_ref)
                except (FileNotFoundError, OSError):
                    # File may already be gone — continue cleanup
                    pass

    def _get_orphaned_book_ids(self, user_id: UUID) -> list[UUID]:
        """Find book IDs that will have no copies after this user's copies are removed."""
        # Get all book_ids for user's copies
        user_book_ids = (
            self._session.query(CopyModel.book_id)
            .filter(CopyModel.user_id == user_id)
            .distinct()
            .all()
        )
        user_book_ids = [row[0] for row in user_book_ids]

        orphaned = []
        for book_id in user_book_ids:
            # Count copies from OTHER users
            other_copies_count = (
                self._session.query(CopyModel)
                .filter(CopyModel.book_id == book_id, CopyModel.user_id != user_id)
                .count()
            )
            if other_copies_count == 0:
                orphaned.append(book_id)

        return orphaned

    def _delete_copies(self, user_id: UUID) -> None:
        """Delete all copies (physical + digital) owned by the user."""
        self._session.query(CopyModel).filter(CopyModel.user_id == user_id).delete()
        self._session.flush()

    def _delete_orphaned_books(self, book_ids: list[UUID]) -> None:
        """Delete books that have no remaining copies."""
        if not book_ids:
            return
        self._session.query(BookModel).filter(BookModel.id.in_(book_ids)).delete()
        self._session.flush()

    def _delete_reviews(self, user_id: UUID) -> None:
        """Delete all reviews authored by the user."""
        self._session.query(ReviewModel).filter(
            ReviewModel.user_id == user_id
        ).delete()
        self._session.flush()

    def _delete_loans(self, user_id: UUID) -> None:
        """Delete all loans where the user is the borrower."""
        self._session.query(LoanModel).filter(
            LoanModel.borrower_user_id == user_id
        ).delete()
        self._session.flush()

    def _anonymize_audit_logs(self, user_id: UUID) -> None:
        """Anonymize audit logs older than the minimum legal retention period.

        Logs within the retention window keep their actor_user_id intact
        (legal requirement). Older logs have actor_user_id replaced with
        the zero UUID sentinel.

        Reference: privacy/requirements.md Req 1.7 (configurable retention)
        """
        retention_cutoff = datetime.now(timezone.utc) - timedelta(
            days=self._audit_retention_days
        )

        self._session.query(AuditLogModel).filter(
            AuditLogModel.actor_user_id == user_id,
            AuditLogModel.timestamp < retention_cutoff,
        ).update(
            {AuditLogModel.actor_user_id: DELETED_USER_SENTINEL},
            synchronize_session="fetch",
        )
        self._session.flush()
