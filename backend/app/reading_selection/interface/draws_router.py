"""Reading Selection REST endpoints.

Reference: reading-selection/tasks.md#3, #4, ADR-0008, ADR-0013
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.interface.dependencies import get_current_user_id
from app.reading_selection.application.pick_by_turn import PickByTurn
from app.reading_selection.application.run_reading_draw import RunDrawRequest as DrawInput
from app.reading_selection.application.run_reading_draw import RunReadingDraw
from app.reading_selection.infrastructure.repositories import (
    SqlBookQueryService,
    SqlCopyQueryService,
    SqlDrawRepository,
    SqlTurnHistoryRepository,
)
from app.reading_selection.interface.schemas import (
    DrawResponse,
    NextPickerResponse,
    RunDrawRequest,
)

router = APIRouter(prefix="/groups/{group_id}/draws", tags=["reading-selection"])


@router.post("/", response_model=DrawResponse, status_code=status.HTTP_200_OK)
def run_draw(
    group_id: UUID,
    request: RunDrawRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Execute a filtered random draw for the group.

    Returns 200 with empty result if no books match (not an error).
    Results show source library but never file_ref (Property 3).
    """
    use_case = RunReadingDraw(
        draw_repository=SqlDrawRepository(db),
        book_query=SqlBookQueryService(db),
        copy_query=SqlCopyQueryService(db),
    )

    draw = use_case.execute(
        DrawInput(
            group_id=group_id,
            participant_ids=request.participant_ids,
            genre=request.genre,
            max_pages=request.max_pages,
            unread_only=request.unread_only,
        )
    )

    db.commit()

    return DrawResponse(
        id=draw.id,
        group_id=draw.group_id,
        filters=draw.filters,
        participants=draw.participants,
        result_book_id=draw.result_book_id,
        result_source_user_id=draw.result_source_user_id,
        timestamp=draw.timestamp,
    )


@router.get("/", response_model=list[DrawResponse])
def get_draw_history(
    group_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get draw history for a group. Most recent first."""
    repo = SqlDrawRepository(db)
    draws = repo.find_by_group(group_id)

    return [
        DrawResponse(
            id=d.id,
            group_id=d.group_id,
            filters=d.filters,
            participants=d.participants,
            result_book_id=d.result_book_id,
            result_source_user_id=d.result_source_user_id,
            timestamp=d.timestamp,
        )
        for d in draws
    ]


@router.get("/next-picker", response_model=NextPickerResponse)
def get_next_picker(
    group_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get who picks next in pick-by-turn mode."""
    use_case = PickByTurn(turn_history_repository=SqlTurnHistoryRepository(db))
    next_user = use_case.get_next_picker(group_id)
    return NextPickerResponse(next_picker_user_id=next_user)
