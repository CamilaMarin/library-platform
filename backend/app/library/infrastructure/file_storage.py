"""FileStorage implementations.

Local filesystem adapter for development. MinIO/S3 adapter to be added
when deploying to Supabase Storage or cloud.

Each user's files are isolated by prefix: users/{user_id}/
Reference: ADR-0009 (digital isolation), ADR-0017 (cloud agnostic)
"""

import os
from pathlib import Path
from uuid import UUID


class LocalFileStorage:
    """Local filesystem implementation of FileStorage protocol.

    Files stored under: {base_path}/users/{user_id}/{filename}
    Used for development. Production uses MinIO/S3.
    """

    def __init__(self, base_path: str = "./storage"):
        self._base_path = Path(base_path)

    def upload(self, user_id: UUID, filename: str, content: bytes) -> str:
        """Upload file to local filesystem. Returns the file reference."""
        user_dir = self._base_path / "users" / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        file_path = user_dir / filename
        file_path.write_bytes(content)

        # Return the relative reference (same format as S3 key)
        return f"users/{user_id}/{filename}"

    def download(self, file_ref: str) -> bytes:
        """Download file content by reference."""
        file_path = self._base_path / file_ref
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_ref}")
        return file_path.read_bytes()

    def delete(self, file_ref: str) -> None:
        """Delete file by reference."""
        file_path = self._base_path / file_ref
        if file_path.exists():
            os.remove(file_path)
