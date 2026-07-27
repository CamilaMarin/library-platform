"""Domain unit tests for Loan entity.

Tests the physical-only constraint and default field values.
Reference: loans/design.md Property 1
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.circulation.domain.entities import Loan, LoanStatus


class TestLoanCreate:
    def test_create_loan_for_physical_copy_succeeds(self):
        copy_id = uuid4()
        borrower_id = uuid4()

        loan = Loan.create(
            copy_id=copy_id,
            copy_type="physical",
            borrower_user_id=borrower_id,
        )

        assert loan.copy_id == copy_id
        assert loan.borrower_user_id == borrower_id
        assert loan.status == LoanStatus.ACTIVE

    def test_create_loan_for_digital_copy_raises_value_error(self):
        with pytest.raises(ValueError, match="Loans can only be created for physical copies"):
            Loan.create(
                copy_id=uuid4(),
                copy_type="digital",
                borrower_user_id=uuid4(),
            )

    def test_loan_default_status_is_active(self):
        loan = Loan.create(
            copy_id=uuid4(),
            copy_type="physical",
            borrower_user_id=uuid4(),
        )
        assert loan.status == LoanStatus.ACTIVE

    def test_estimated_return_date_is_optional(self):
        loan = Loan.create(
            copy_id=uuid4(),
            copy_type="physical",
            borrower_user_id=uuid4(),
        )
        assert loan.estimated_return_date is None

    def test_estimated_return_date_can_be_set(self):
        return_date = datetime(2025, 6, 15, tzinfo=timezone.utc)

        loan = Loan.create(
            copy_id=uuid4(),
            copy_type="physical",
            borrower_user_id=uuid4(),
            estimated_return_date=return_date,
        )

        assert loan.estimated_return_date == return_date

    def test_loan_has_uuid_id(self):
        loan = Loan.create(
            copy_id=uuid4(),
            copy_type="physical",
            borrower_user_id=uuid4(),
        )
        assert loan.id is not None

    def test_loan_date_defaults_to_utcnow(self):
        before = datetime.now(timezone.utc)
        loan = Loan.create(
            copy_id=uuid4(),
            copy_type="physical",
            borrower_user_id=uuid4(),
        )
        after = datetime.now(timezone.utc)

        assert before <= loan.loan_date <= after
