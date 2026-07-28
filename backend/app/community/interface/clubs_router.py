"""Clubs REST endpoints.

Reference: ADR-0006, clubs/requirements.md, clubs/design.md
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.community.application.create_club import CreateClub
from app.community.application.post_comment import PostComment
from app.community.application.set_active_book import SetActiveBook
from app.community.infrastructure.repositories import (
    SqlClubRepository,
    SqlCommentRepository,
    SqlReadingTurnRepository,
)
from app.community.interface.schemas import (
    AvailableBookResponse,
    ClubMemberResponse,
    ClubResponse,
    CommentResponse,
    CreateClubRequest,
    PostCommentRequest,
    SetActiveBookRequest,
)
from app.database import get_db
from app.identity.infrastructure.models import GroupMembershipModel, UserModel
from app.identity.interface.dependencies import get_current_user_id
from app.library.infrastructure.models import BookModel, CopyModel

router = APIRouter(prefix="/clubs", tags=["clubs"])


def _get_user_group_ids(db: Session, user_id: UUID) -> list[UUID]:
    """Get all group IDs the user is an active member of."""
    memberships = (
        db.query(GroupMembershipModel.group_id)
        .filter(
            GroupMembershipModel.user_id == user_id,
            GroupMembershipModel.status == "accepted",
        )
        .all()
    )
    return [m.group_id for m in memberships]


def _get_group_member_ids(db: Session, group_id: UUID) -> list[UUID]:
    """Get all active member user_ids for a given group."""
    memberships = (
        db.query(GroupMembershipModel.user_id)
        .filter(
            GroupMembershipModel.group_id == group_id,
            GroupMembershipModel.status == "accepted",
        )
        .all()
    )
    return [m.user_id for m in memberships]


@router.get("/", response_model=list[ClubResponse])
def list_clubs(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List clubs the user belongs to (via their group memberships)."""
    group_ids = _get_user_group_ids(db, user_id)
    if not group_ids:
        return []

    repo = SqlClubRepository(db)
    clubs = repo.find_by_group_ids(group_ids)

    return [
        ClubResponse(
            id=club.id,
            name=club.name,
            description=club.description,
            group_id=club.group_id,
            active_book_id=club.active_book_id,
            created_at=club.created_at,
        )
        for club in clubs
    ]


@router.post("/", response_model=ClubResponse, status_code=status.HTTP_201_CREATED)
def create_club(
    request: CreateClubRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new club within the user's group."""
    # Determine group_id: either from request or user's first group
    if request.group_id:
        group_id = request.group_id
    else:
        group_ids = _get_user_group_ids(db, user_id)
        if not group_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_has_no_group",
            )
        group_id = group_ids[0]

    # Verify user is a member of the target group
    user_group_ids = _get_user_group_ids(db, user_id)
    if group_id not in user_group_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not_member_of_group",
        )

    repo = SqlClubRepository(db)
    use_case = CreateClub(club_repository=repo)
    club = use_case.execute(group_id=group_id, name=request.name)

    # Update description if provided (use case doesn't support it yet)
    if request.description:
        club.description = request.description
        repo.update(club)

    db.commit()

    return ClubResponse(
        id=club.id,
        name=club.name,
        description=club.description,
        group_id=club.group_id,
        active_book_id=club.active_book_id,
        created_at=club.created_at,
    )


@router.get("/{club_id}", response_model=ClubResponse)
def get_club(
    club_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get club detail."""
    repo = SqlClubRepository(db)
    club = repo.find_by_id(club_id)
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="club_not_found")

    # Verify user has access (is member of the club's group)
    user_group_ids = _get_user_group_ids(db, user_id)
    if club.group_id not in user_group_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not_member_of_group")

    return ClubResponse(
        id=club.id,
        name=club.name,
        description=club.description,
        group_id=club.group_id,
        active_book_id=club.active_book_id,
        created_at=club.created_at,
    )


@router.get("/{club_id}/members", response_model=list[ClubMemberResponse])
def list_club_members(
    club_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List club members (inherited from the club's parent group)."""
    repo = SqlClubRepository(db)
    club = repo.find_by_id(club_id)
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="club_not_found")

    # Verify user has access
    user_group_ids = _get_user_group_ids(db, user_id)
    if club.group_id not in user_group_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not_member_of_group")

    # Get group memberships with user names
    memberships = (
        db.query(GroupMembershipModel, UserModel.name)
        .join(UserModel, GroupMembershipModel.user_id == UserModel.id)
        .filter(
            GroupMembershipModel.group_id == club.group_id,
            GroupMembershipModel.status == "accepted",
        )
        .all()
    )

    return [
        ClubMemberResponse(
            id=m.id,
            user_id=m.user_id,
            club_id=club_id,
            name=name,
            role="owner" if m.user_id == user_id else "member",
            created_at=m.created_at,
        )
        for m, name in memberships
    ]


@router.get("/{club_id}/comments", response_model=list[CommentResponse])
def list_club_comments(
    club_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List comments for the club's active reading turn."""
    repo = SqlClubRepository(db)
    club = repo.find_by_id(club_id)
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="club_not_found")

    # Verify user has access
    user_group_ids = _get_user_group_ids(db, user_id)
    if club.group_id not in user_group_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not_member_of_group")

    # Get the active reading turn
    turn_repo = SqlReadingTurnRepository(db)
    active_turn = turn_repo.find_active_by_club(club_id)
    if not active_turn:
        return []

    # Get comments for the active turn
    comment_repo = SqlCommentRepository(db)
    comments = comment_repo.find_by_turn(active_turn.id)

    return [
        CommentResponse(
            id=c.id,
            user_id=c.user_id,
            text=c.text,
            is_spoiler=c.is_spoiler,
            created_at=c.created_at,
        )
        for c in comments
    ]


@router.post(
    "/{club_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_club_comment(
    club_id: UUID,
    request: PostCommentRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Post a comment on the club's active reading turn."""
    repo = SqlClubRepository(db)
    club = repo.find_by_id(club_id)
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="club_not_found")

    # Verify user has access
    user_group_ids = _get_user_group_ids(db, user_id)
    if club.group_id not in user_group_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not_member_of_group")

    # Get or create the active reading turn
    turn_repo = SqlReadingTurnRepository(db)
    active_turn = turn_repo.find_active_by_club(club_id)
    if not active_turn:
        # No active turn — we need at least an active book
        if not club.active_book_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="no_active_book",
            )
        # Create a turn for the current book
        from app.community.domain.entities import ReadingTurn

        active_turn = ReadingTurn(
            club_id=club_id,
            book_id=club.active_book_id,
            current_user_id=user_id,
        )
        active_turn = turn_repo.save(active_turn)

    # Post the comment
    comment_repo = SqlCommentRepository(db)
    use_case = PostComment(comment_repository=comment_repo)
    comment = use_case.execute(
        turn_id=active_turn.id,
        user_id=user_id,
        text=request.text,
        is_spoiler=request.is_spoiler,
    )

    db.commit()

    return CommentResponse(
        id=comment.id,
        user_id=comment.user_id,
        text=comment.text,
        is_spoiler=comment.is_spoiler,
        created_at=comment.created_at,
    )


@router.post("/{club_id}/active-book", status_code=status.HTTP_200_OK)
def set_active_book(
    club_id: UUID,
    request: SetActiveBookRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Set the club's active book."""
    club_repo = SqlClubRepository(db)
    club = club_repo.find_by_id(club_id)
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="club_not_found")

    # Verify user has access
    user_group_ids = _get_user_group_ids(db, user_id)
    if club.group_id not in user_group_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not_member_of_group")

    use_case = SetActiveBook(club_repository=club_repo)
    use_case.execute(club_id=club_id, book_id=request.book_id)

    db.commit()

    return {"status": "ok"}


@router.get("/{club_id}/available-books", response_model=list[AvailableBookResponse])
def list_available_books(
    club_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List books available for the club (books from group members' libraries).

    Returns metadata only — never exposes file_ref (ADR-0001, ADR-0009).
    """
    club_repo = SqlClubRepository(db)
    club = club_repo.find_by_id(club_id)
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="club_not_found")

    # Verify user has access
    user_group_ids = _get_user_group_ids(db, user_id)
    if club.group_id not in user_group_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not_member_of_group")

    # Get all group member IDs
    member_ids = _get_group_member_ids(db, club.group_id)
    if not member_ids:
        return []

    # Get all books with copies owned by group members
    books = (
        db.query(BookModel)
        .join(CopyModel, CopyModel.book_id == BookModel.id)
        .filter(CopyModel.user_id.in_(member_ids))
        .distinct()
        .all()
    )

    return [
        AvailableBookResponse(
            id=b.id,
            title=b.title,
            author=b.author,
        )
        for b in books
    ]
