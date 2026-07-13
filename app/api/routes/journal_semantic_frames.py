from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.journal_semantic_frame import JournalSemanticFrameRead
from app.services.journal_semantic_frame_service import (
    get_user_journal_semantic_frame,
    list_user_journal_semantic_frames,
)

router = APIRouter()


@router.get("", response_model=list[JournalSemanticFrameRead])
def list_journal_semantic_frames_endpoint(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_user_journal_semantic_frames(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )


@router.get("/{semantic_frame_id}", response_model=JournalSemanticFrameRead)
def get_journal_semantic_frame_endpoint(
    semantic_frame_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    semantic_frame = get_user_journal_semantic_frame(
        db=db,
        user_id=current_user.id,
        semantic_frame_id=semantic_frame_id,
    )

    if semantic_frame is None:
        raise HTTPException(
            status_code=404,
            detail="Journal semantic frame not found.",
        )

    return semantic_frame