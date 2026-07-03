from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.journal_entry import JournalEntry


def create_journal_entry(
    db: Session,
    user_id: UUID,
    content: str,
) -> JournalEntry:
    journal_entry = JournalEntry(
        user_id=user_id,
        content=content,
    )

    db.add(journal_entry)
    db.commit()
    db.refresh(journal_entry)

    return journal_entry


def get_journal_entry_by_id(
    db: Session,
    journal_entry_id: UUID,
) -> JournalEntry | None:
    return (
        db.query(JournalEntry)
        .filter(JournalEntry.id == journal_entry_id)
        .first()
    )