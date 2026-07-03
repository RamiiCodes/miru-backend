from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.repositories.journal_repository import (
    create_journal_entry,
    get_journal_entry_by_id,
)
from app.db.repositories.user_repository import get_user_by_id
from app.db.session import get_db
from app.schemas.journal import JournalEntryCreate, JournalEntryRead

router = APIRouter()


@router.post("", response_model=JournalEntryRead, status_code=status.HTTP_201_CREATED)
def create_journal_entry_endpoint(
    payload: JournalEntryCreate,
    db: Session = Depends(get_db),
):
    user = get_user_by_id(db, payload.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return create_journal_entry(
        db=db,
        user_id=payload.user_id,
        content=payload.content,
    )


@router.get("/{journal_entry_id}", response_model=JournalEntryRead)
def get_journal_entry_endpoint(
    journal_entry_id: UUID,
    db: Session = Depends(get_db),
):
    journal_entry = get_journal_entry_by_id(db, journal_entry_id)

    if not journal_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journal entry not found.",
        )

    return journal_entry