from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.journal_repository import create_journal_entry
from app.db.session import get_db
from app.schemas.journal import JournalEntryCreate, JournalEntryRead
from app.services.current_emotional_state_service import calculate_current_emotional_state
from app.services.journal_signal_service import create_user_signals_from_journal

router = APIRouter()


@router.post("", response_model=JournalEntryRead, status_code=status.HTTP_201_CREATED)
def create_journal_entry_endpoint(
    payload: JournalEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    journal_entry = create_journal_entry(
        db=db,
        user_id=current_user.id,
        content=payload.content,
    )

    create_user_signals_from_journal(
        db=db,
        journal_entry=journal_entry,
    )

    calculate_current_emotional_state(
        db=db,
        user_id=current_user.id,
    )

    return journal_entry