"""Repository implementations for the privacy foundation.

These implement the protocols defined in application/protocols.py.
Reference: ADR-0017 (infrastructure implements abstractions)
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.identity.domain.entities import (
    AuditAction,
    AuditLog,
    DataConsent,
    DataProcessingRecord,
    FamilyGroup,
    GroupMembership,
    MembershipStatus,
    RefreshToken,
    RetentionPolicy,
    User,
)
from app.identity.infrastructure.models import (
    AuditLogModel,
    DataConsentModel,
    DataProcessingRecordModel,
    FamilyGroupModel,
    GroupMembershipModel,
    RefreshTokenModel,
    RetentionPolicyModel,
    UserModel,
)


class SqlDataConsentRepository:
    """SQLAlchemy implementation of DataConsentRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, consent: DataConsent) -> DataConsent:
        model = DataConsentModel(
            id=consent.id,
            user_id=consent.user_id,
            timestamp=consent.timestamp,
            policy_version=consent.policy_version,
            purpose=consent.purpose,
        )
        self._session.add(model)
        self._session.flush()
        return consent

    def find_by_user_id(self, user_id: UUID) -> DataConsent | None:
        model = (
            self._session.query(DataConsentModel)
            .filter(DataConsentModel.user_id == user_id)
            .first()
        )
        if not model:
            return None
        return DataConsent(
            id=model.id,
            user_id=model.user_id,
            timestamp=model.timestamp,
            policy_version=model.policy_version,
            purpose=model.purpose,
        )


class SqlDataProcessingRecordRepository:
    """SQLAlchemy implementation of DataProcessingRecordRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, record: DataProcessingRecord) -> DataProcessingRecord:
        model = DataProcessingRecordModel(
            id=record.id,
            user_id=record.user_id,
            data_type=record.data_type,
            purpose=record.purpose,
            legal_basis=record.legal_basis,
            collected_at=record.collected_at,
            retention_expires_at=record.retention_expires_at,
        )
        self._session.add(model)
        self._session.flush()
        return record

    def find_by_user_id(self, user_id: UUID) -> list[DataProcessingRecord]:
        models = (
            self._session.query(DataProcessingRecordModel)
            .filter(DataProcessingRecordModel.user_id == user_id)
            .all()
        )
        return [
            DataProcessingRecord(
                id=m.id,
                user_id=m.user_id,
                data_type=m.data_type,
                purpose=m.purpose,
                legal_basis=m.legal_basis,
                collected_at=m.collected_at,
                retention_expires_at=m.retention_expires_at,
            )
            for m in models
        ]


class SqlAuditLogRepository:
    """SQLAlchemy implementation of AuditLogRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, entry: AuditLog) -> AuditLog:
        model = AuditLogModel(
            id=entry.id,
            actor_user_id=entry.actor_user_id,
            action=entry.action.value,
            affected_entity=entry.affected_entity,
            timestamp=entry.timestamp,
        )
        self._session.add(model)
        self._session.flush()
        return entry

    def find_by_actor(self, actor_user_id: UUID) -> list[AuditLog]:
        models = (
            self._session.query(AuditLogModel)
            .filter(AuditLogModel.actor_user_id == actor_user_id)
            .order_by(AuditLogModel.timestamp.desc())
            .all()
        )
        return [
            AuditLog(
                id=m.id,
                actor_user_id=m.actor_user_id,
                action=AuditAction(m.action),
                affected_entity=m.affected_entity,
                timestamp=m.timestamp,
            )
            for m in models
        ]


class SqlRetentionPolicyRepository:
    """SQLAlchemy implementation of RetentionPolicyRepository."""

    def __init__(self, session: Session):
        self._session = session

    def find_active(self) -> list[RetentionPolicy]:
        models = (
            self._session.query(RetentionPolicyModel)
            .filter(RetentionPolicyModel.active.is_(True))
            .all()
        )
        return [
            RetentionPolicy(
                id=m.id,
                data_type=m.data_type,
                duration_days=m.duration_days,
                description=m.description,
                active=m.active,
            )
            for m in models
        ]

    def find_by_data_type(self, data_type: str) -> RetentionPolicy | None:
        model = (
            self._session.query(RetentionPolicyModel)
            .filter(RetentionPolicyModel.data_type == data_type)
            .first()
        )
        if not model:
            return None
        return RetentionPolicy(
            id=model.id,
            data_type=model.data_type,
            duration_days=model.duration_days,
            description=model.description,
            active=model.active,
        )


class SqlUserRepository:
    """SQLAlchemy implementation of UserRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            name=user.name,
            email=user.email,
            password_hash=user.password_hash,
            privacy_settings=user.privacy_settings,
            created_at=user.created_at,
        )
        self._session.add(model)
        self._session.flush()
        return user

    def find_by_email(self, email: str) -> User | None:
        model = (
            self._session.query(UserModel)
            .filter(UserModel.email == email)
            .first()
        )
        if not model:
            return None
        return User(
            id=model.id,
            name=model.name,
            email=model.email,
            password_hash=model.password_hash,
            privacy_settings=model.privacy_settings or {},
            created_at=model.created_at,
        )

    def find_by_id(self, user_id: UUID) -> User | None:
        model = (
            self._session.query(UserModel)
            .filter(UserModel.id == user_id)
            .first()
        )
        if not model:
            return None
        return User(
            id=model.id,
            name=model.name,
            email=model.email,
            password_hash=model.password_hash,
            privacy_settings=model.privacy_settings or {},
            created_at=model.created_at,
        )


class SqlRefreshTokenRepository:
    """SQLAlchemy implementation of RefreshTokenRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, token: RefreshToken) -> RefreshToken:
        model = RefreshTokenModel(
            id=token.id,
            user_id=token.user_id,
            token_hash=token.token_hash,
            expires_at=token.expires_at,
            revoked=token.revoked,
            created_at=token.created_at,
        )
        self._session.add(model)
        self._session.flush()
        return token

    def find_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        model = (
            self._session.query(RefreshTokenModel)
            .filter(RefreshTokenModel.token_hash == token_hash)
            .first()
        )
        if not model:
            return None
        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            revoked=model.revoked,
            created_at=model.created_at,
        )

    def find_active_by_user_id(self, user_id: UUID) -> list[RefreshToken]:
        models = (
            self._session.query(RefreshTokenModel)
            .filter(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked.is_(False),
            )
            .all()
        )
        return [
            RefreshToken(
                id=m.id,
                user_id=m.user_id,
                token_hash=m.token_hash,
                expires_at=m.expires_at,
                revoked=m.revoked,
                created_at=m.created_at,
            )
            for m in models
        ]

    def revoke(self, token_id: UUID) -> None:
        self._session.query(RefreshTokenModel).filter(
            RefreshTokenModel.id == token_id
        ).update({"revoked": True})
        self._session.flush()


class SqlFamilyGroupRepository:
    """SQLAlchemy implementation of FamilyGroupRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, group: FamilyGroup) -> FamilyGroup:
        model = FamilyGroupModel(
            id=group.id,
            name=group.name,
            created_at=group.created_at,
        )
        self._session.add(model)
        self._session.flush()
        return group

    def find_by_id(self, group_id: UUID) -> FamilyGroup | None:
        model = (
            self._session.query(FamilyGroupModel)
            .filter(FamilyGroupModel.id == group_id)
            .first()
        )
        if not model:
            return None
        return FamilyGroup(
            id=model.id,
            name=model.name,
            created_at=model.created_at,
        )


class SqlGroupMembershipRepository:
    """SQLAlchemy implementation of GroupMembershipRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, membership: GroupMembership) -> GroupMembership:
        model = GroupMembershipModel(
            id=membership.id,
            group_id=membership.group_id,
            user_id=membership.user_id,
            status=membership.status.value,
            created_at=membership.created_at,
        )
        self._session.add(model)
        self._session.flush()
        return membership

    def find_by_id(self, membership_id: UUID) -> GroupMembership | None:
        model = (
            self._session.query(GroupMembershipModel)
            .filter(GroupMembershipModel.id == membership_id)
            .first()
        )
        if not model:
            return None
        return GroupMembership(
            id=model.id,
            group_id=model.group_id,
            user_id=model.user_id,
            status=MembershipStatus(model.status),
            created_at=model.created_at,
        )

    def find_by_group_id(self, group_id: UUID) -> list[GroupMembership]:
        models = (
            self._session.query(GroupMembershipModel)
            .filter(GroupMembershipModel.group_id == group_id)
            .all()
        )
        return [
            GroupMembership(
                id=m.id,
                group_id=m.group_id,
                user_id=m.user_id,
                status=MembershipStatus(m.status),
                created_at=m.created_at,
            )
            for m in models
        ]

    def find_by_user_and_group(self, user_id: UUID, group_id: UUID) -> GroupMembership | None:
        model = (
            self._session.query(GroupMembershipModel)
            .filter(
                GroupMembershipModel.user_id == user_id,
                GroupMembershipModel.group_id == group_id,
            )
            .first()
        )
        if not model:
            return None
        return GroupMembership(
            id=model.id,
            group_id=model.group_id,
            user_id=model.user_id,
            status=MembershipStatus(model.status),
            created_at=model.created_at,
        )

    def update_status(self, membership_id: UUID, status: MembershipStatus) -> None:
        self._session.query(GroupMembershipModel).filter(
            GroupMembershipModel.id == membership_id
        ).update({"status": status.value})
        self._session.flush()
