"""Circulation domain entities.

Pure domain objects — no framework or infrastructure imports.
Reference: ADR-0015 (Loans reference Copies, not Books)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LoanStatus(str, Enum):
    """Status of a loan."""

    ACTIVE = "active"
    RETURNED = "returned"


@dataclass
class Loan:
    """Aggregate root representing a physical-book loan between people.

    Invariants:
    - Only physical copies can be loaned (Property 1)
    - A Copy cannot have two simultaneous active loans (enforced at application layer)
    """

    id: UUID = field(default_factory=uuid4)
    copy_id: UUID = field(default_factory=uuid4)
    borrower_user_id: UUID = field(default_factory=uuid4)
    loan_date: datetime = field(default_factory=_utcnow)
    estimated_return_date: datetime | None = None
    returned_date: datetime | None = None
    status: LoanStatus = LoanStatus.ACTIVE

    @staticmethod
    def create(
        copy_id: UUID,
        copy_type: str,
        borrower_user_id: UUID,
        estimated_return_date: datetime | None = None,
    ) -> "Loan":
        """Factory that enforces the physical-only constraint.

        Raises ValueError if copy_type is not 'physical'.
        """
        if copy_type != "physical":
            raise ValueError("Loans can only be created for physical copies")
        return Loan(
            copy_id=copy_id,
            borrower_user_id=borrower_user_id,
            estimated_return_date=estimated_return_date,
        )
