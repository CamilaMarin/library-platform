"""RetentionJob — configurable data retention enforcement.

Reads active RetentionPolicy records from the database and processes data
that has exceeded its retention period. Duration is ALWAYS read from the
retention_policies table at runtime — never from a code constant.

Supported data_type handlers:
- "inactive_accounts": flags accounts with no login in duration_days days
- "audit_logs": anonymizes audit logs older than duration_days
- "expired_consents": removes consent records older than duration_days
- "processing_records": removes records past their retention_expires_at

Reference: privacy/requirements.md Req 1.7, ADR-0016
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.identity.application.audit_service import AuditService
from app.identity.domain.entities import AuditAction, RetentionPolicy
from app.identity.infrastructure.models import (
    AuditLogModel,
    DataConsentModel,
    DataProcessingRecordModel,
    RetentionPolicyModel,
    UserModel,
)


# Zero UUID used as anonymized placeholder for deleted users in audit logs
DELETED_USER_SENTINEL = UUID("00000000-0000-0000-0000-000000000000")


@dataclass
class RetentionJobResult:
    """Result of executing the retention job."""

    policies_processed: int = 0
    records_affected: int = 0
    details: list[str] = field(default_factory=list)


class RetentionJob:
    """Service that enforces data retention policies from the database.

    All retention durations come from the retention_policies table — never
    from hardcoded constants. This satisfies ADR-0016.
    """

    def __init__(self, session: Session, audit_service: AuditService):
        self._session = session
        self._audit_service = audit_service

    def execute(self) -> RetentionJobResult:
        """Run all active retention policies.

        Reads policies from the database and applies the appropriate handler
        for each data_type.
        """
        result = RetentionJobResult()

        # Read active policies from database (ADR-0016: never hardcoded)
        active_policies = (
            self._session.query(RetentionPolicyModel)
            .filter(RetentionPolicyModel.active.is_(True))
            .all()
        )

        for policy_model in active_policies:
            policy = RetentionPolicy(
                id=policy_model.id,
                data_type=policy_model.data_type,
                duration_days=policy_model.duration_days,
                description=policy_model.description,
                active=policy_model.active,
            )
            affected = self._process_policy(policy)
            result.policies_processed += 1
            result.records_affected += affected
            if affected > 0:
                result.details.append(
                    f"{policy.data_type}: {affected} records affected "
                    f"(retention: {policy.duration_days} days)"
                )
            else:
                result.details.append(
                    f"{policy.data_type}: no records to process "
                    f"(retention: {policy.duration_days} days)"
                )

        # Log the retention job execution
        self._audit_service.log(
            actor_user_id=None,
            action=AuditAction.ARCO_REQUEST,
            affected_entity=(
                f"retention_job: processed {result.policies_processed} policies, "
                f"{result.records_affected} records affected"
            ),
        )

        return result

    def _process_policy(self, policy: RetentionPolicy) -> int:
        """Dispatch to the appropriate handler based on data_type."""
        handlers = {
            "inactive_accounts": self._handle_inactive_accounts,
            "audit_logs": self._handle_audit_logs,
            "expired_consents": self._handle_expired_consents,
            "processing_records": self._handle_processing_records,
        }

        handler = handlers.get(policy.data_type)
        if handler is None:
            return 0

        return handler(policy)

    def _handle_inactive_accounts(self, policy: RetentionPolicy) -> int:
        """Flag accounts with no login in duration_days days.

        Uses the audit log to determine last login time. Accounts without
        any login record beyond the retention period are flagged (privacy_settings
        updated with flagged_for_deletion=True). Does NOT auto-delete.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=policy.duration_days)

        # Find all users
        all_users = self._session.query(UserModel).all()
        flagged_count = 0

        for user in all_users:
            # Check if user already flagged
            settings = user.privacy_settings or {}
            if settings.get("flagged_for_deletion"):
                continue

            # Find most recent login in audit logs
            last_login = (
                self._session.query(AuditLogModel.timestamp)
                .filter(
                    AuditLogModel.actor_user_id == user.id,
                    AuditLogModel.action == AuditAction.USER_LOGIN.value,
                )
                .order_by(AuditLogModel.timestamp.desc())
                .first()
            )

            # If no login at all, use account creation date
            last_activity = last_login[0] if last_login else user.created_at

            # Make timezone-aware if needed
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)

            if last_activity < cutoff:
                # Flag for deletion — do not auto-delete
                new_settings = dict(settings)
                new_settings["flagged_for_deletion"] = True
                new_settings["flagged_at"] = datetime.now(timezone.utc).isoformat()
                self._session.query(UserModel).filter(
                    UserModel.id == user.id
                ).update({"privacy_settings": new_settings})
                flagged_count += 1

        if flagged_count > 0:
            self._session.flush()

        return flagged_count

    def _handle_audit_logs(self, policy: RetentionPolicy) -> int:
        """Anonymize audit logs older than duration_days.

        Replaces actor_user_id with the zero UUID sentinel for logs past retention.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=policy.duration_days)

        affected = (
            self._session.query(AuditLogModel)
            .filter(
                AuditLogModel.timestamp < cutoff,
                AuditLogModel.actor_user_id != DELETED_USER_SENTINEL,
                AuditLogModel.actor_user_id.isnot(None),
            )
            .update(
                {AuditLogModel.actor_user_id: DELETED_USER_SENTINEL},
                synchronize_session="fetch",
            )
        )
        if affected > 0:
            self._session.flush()

        return affected

    def _handle_expired_consents(self, policy: RetentionPolicy) -> int:
        """Remove consent records older than duration_days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=policy.duration_days)

        affected = (
            self._session.query(DataConsentModel)
            .filter(DataConsentModel.timestamp < cutoff)
            .delete(synchronize_session="fetch")
        )
        if affected > 0:
            self._session.flush()

        return affected

    def _handle_processing_records(self, policy: RetentionPolicy) -> int:
        """Remove processing records past their retention_expires_at.

        Uses the record's own retention_expires_at field rather than computing
        from duration_days, since each record may have been created at different times.
        """
        now = datetime.now(timezone.utc)

        affected = (
            self._session.query(DataProcessingRecordModel)
            .filter(
                DataProcessingRecordModel.retention_expires_at.isnot(None),
                DataProcessingRecordModel.retention_expires_at < now,
            )
            .delete(synchronize_session="fetch")
        )
        if affected > 0:
            self._session.flush()

        return affected
