"""Run the data retention job manually.

Reads all active retention policies from the database and enforces them.
Duration is always from the retention_policies table — never hardcoded (ADR-0016).

Usage:
    python -m scripts.run_retention

Reference: privacy/requirements.md Req 1.7, ADR-0016
"""

import sys
from pathlib import Path

# Ensure the backend directory is on the path when run as a module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402
from app.identity.application.audit_service import AuditService  # noqa: E402
from app.identity.application.retention_job import RetentionJob  # noqa: E402
from app.identity.infrastructure.repositories import SqlAuditLogRepository  # noqa: E402


def main() -> None:
    """Execute the retention job and print results."""
    print("Starting data retention job...")
    print("Reading retention policies from database (ADR-0016: never hardcoded)")
    print()

    session = SessionLocal()
    try:
        audit_repo = SqlAuditLogRepository(session)
        audit_service = AuditService(repository=audit_repo)

        job = RetentionJob(session=session, audit_service=audit_service)
        result = job.execute()

        session.commit()

        print("Retention job completed:")
        print(f"  Policies processed: {result.policies_processed}")
        print(f"  Records affected:   {result.records_affected}")
        print()
        if result.details:
            print("Details:")
            for detail in result.details:
                print(f"  - {detail}")
        else:
            print("No active policies found.")

    except Exception as e:
        session.rollback()
        print(f"Error running retention job: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
