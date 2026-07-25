"""PostComment use case.

Posts a comment on a reading turn with spoiler flag (default: false).
Reference: clubs/requirements.md Req 1.3, Property 3
"""

from uuid import UUID

from app.community.application.protocols import CommentRepository
from app.community.domain.entities import Comment


class PostComment:
    """Use case: post a comment on a reading turn.

    is_spoiler defaults to False — user must explicitly mark (Property 3).
    """

    def __init__(self, comment_repository: CommentRepository):
        self._comment_repo = comment_repository

    def execute(
        self, turn_id: UUID, user_id: UUID, text: str, is_spoiler: bool = False
    ) -> Comment:
        """Create and persist a comment."""
        comment = Comment(
            turn_id=turn_id,
            user_id=user_id,
            text=text,
            is_spoiler=is_spoiler,
        )
        return self._comment_repo.save(comment)
