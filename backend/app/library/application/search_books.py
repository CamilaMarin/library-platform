"""SearchBooks use case.

Searches books within the user's personal library and their group's shared library.
Returns metadata only — never file_ref (ADR-0009 Property 5).

Reference: library/requirements.md Req 3, ADR-0010
"""

from uuid import UUID

from app.library.application.protocols import BookRepository
from app.library.domain.entities import Book


class SearchBooks:
    """Use case: search books by title, author, genre, or ISBN.

    Searches across:
    - User's own library (copies they own)
    - Group shared library (copies owned by group members) — metadata only

    Never exposes file_ref (Property 5).
    """

    def __init__(self, book_repository: BookRepository):
        self._book_repo = book_repository

    def execute(
        self,
        query: str,
        user_id: UUID,
        group_member_ids: list[UUID] | None = None,
    ) -> list[Book]:
        """Search books matching the query within accessible libraries.

        Args:
            query: Search term (matched against title, author, ISBN)
            user_id: The requesting user
            group_member_ids: IDs of the user's group members (for shared library)

        Returns:
            List of Book entities (metadata only, never file_ref)
        """
        if not query or not query.strip():
            return []

        return self._book_repo.search(
            query=query.strip(),
            user_id=user_id,
            group_member_ids=group_member_ids,
        )
