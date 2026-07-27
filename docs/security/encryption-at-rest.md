# Encryption at Rest and in Transit — EntreLíneas

> Requirement 1.6: THE SYSTEM SHALL encrypt sensitive personal data and users' digital files, both in transit and at rest.

## Overview

EntreLíneas implements defense-in-depth encryption at multiple layers:

| Layer | Mechanism | Scope |
|-------|-----------|-------|
| Transit | HTTPS (TLS 1.2+) | All client-server communication |
| Application | Fernet field-level encryption | Email, display_name (PII fields) |
| Storage (files) | MinIO SSE-S3 | All uploaded digital files (EPUB, PDF) |
| Storage (database) | PostgreSQL disk encryption | Entire database volume |

## Transit Encryption

- **Production**: HTTPS enforced via reverse proxy (nginx/Caddy) with TLS 1.2+ certificates.
- **Development**: HTTP is acceptable (localhost only). No self-signed certs needed for dev.
- **Internal services**: Docker network communication between app, PostgreSQL, and MinIO is on an isolated bridge network. For production, enable TLS on inter-service connections.

## Application-Level Field Encryption

The `FieldEncryptor` class (`app/security/encryption.py`) provides Fernet symmetric encryption for the most sensitive PII fields.

### Which fields are personal data?

| Entity | Field | Classification | Field-level encryption? |
|--------|-------|---------------|------------------------|
| User | email | PII (identifier) | Ready (MVP infrastructure) |
| User | display_name | PII (personal) | Ready (MVP infrastructure) |
| User | hashed_password | Credential | Already hashed (bcrypt) |
| DigitalFile | file_ref | Indirect PII | Protected by MinIO SSE |
| Review | body | Personal opinion | Protected by disk encryption |
| AuditLog | actor_user_id | Indirect PII | Protected by disk encryption |

### Usage

```python
from app.security.encryption import FieldEncryptor
from app.config import settings

encryptor = FieldEncryptor(key=settings.encryption_key)

# Encrypt before storing
encrypted_email = encryptor.encrypt("user@example.com")

# Decrypt when reading
original_email = encryptor.decrypt(encrypted_email)
```

### Key Management

- **Environment variable**: `ENCRYPTION_KEY`
- **Generate a key**: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- **Development**: A default key is provided in `config.py` (for local dev only).
- **Production**: MUST use a unique key stored in a secrets manager (AWS Secrets Manager, GCP Secret Manager, Vault, etc.).
- **Key rotation**: Fernet supports key rotation via `MultiFernet`. Implement when needed.

## MinIO Server-Side Encryption (SSE-S3)

All user-uploaded digital files (EPUB, PDF) are stored in MinIO with Server-Side Encryption.

### Configuration

Set the following environment variables for MinIO:

```env
MINIO_KMS_KES_ENDPOINT=https://kes:7373
MINIO_KMS_KES_KEY_NAME=my-minio-key
# Or for simpler SSE-S3 with built-in keys:
MINIO_KMS_SECRET_KEY=my-minio-key:BASE64_ENCODED_256_BIT_KEY
```

For development with Docker Compose, SSE can be enabled with:

```yaml
environment:
  MINIO_KMS_SECRET_KEY: "entrelineas-dev-key:MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDE="
```

### Behavior

- All objects are encrypted at rest using AES-256.
- Decryption is transparent on read (handled by MinIO).
- No application code changes needed — encryption is at the storage layer.

## PostgreSQL Disk Encryption

- **Docker (dev)**: Use Docker volume encryption or an encrypted filesystem.
- **Cloud (prod)**: Enable storage encryption on the managed PostgreSQL instance (all major providers support this: AWS RDS, GCP Cloud SQL, Azure Database).
- **Self-hosted**: Use LUKS/dm-crypt on the data volume.

This provides transparent encryption of the entire database at the disk level, protecting all data including personal fields.

## Security Considerations

1. **Key separation**: The application encryption key (`ENCRYPTION_KEY`) is separate from MinIO and PostgreSQL encryption keys.
2. **No plaintext secrets in code**: Production keys must come from environment variables or a secrets manager.
3. **Backup encryption**: Database and file backups must also be encrypted (ensure backup tooling preserves encryption).
4. **Audit trail**: All access to encrypted fields is logged via the AuditLog service (Requirement 1.5).

## Future Enhancements (Post-MVP)

- Enable field-level encryption on existing data via migration (encrypt-in-place for email column).
- Implement `MultiFernet` for key rotation without downtime.
- Add envelope encryption for large files (client-side encryption before upload).
- Hardware Security Module (HSM) integration for key storage in high-security deployments.
