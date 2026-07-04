from sqlalchemy.orm import Session

from app.db.models.journal_entry import JournalEntry
from app.db.repositories.signal_catalog_repository import get_signal_by_code
from app.db.repositories.user_signal_repository import (
    create_user_signal,
    get_user_signal_by_source,
)


JOURNAL_SIGNAL_KEYWORDS = {
    "rumination_tendency": [
        "overthinking",
        "can't stop thinking",
        "cannot stop thinking",
        "thinking again and again",
        "loop",
        "ruminating",
        "obsessed",
        "stuck in my head",
        "je pense trop",
        "je n'arrête pas de penser",
        "boucle",
    ],
    "self_criticism": [
        "i am stupid",
        "i'm stupid",
        "i am useless",
        "i'm useless",
        "i hate myself",
        "my fault",
        "i'm not good enough",
        "i am not good enough",
        "je suis nul",
        "je suis inutile",
        "c'est ma faute",
    ],
    "fear_of_failure": [
        "failed",
        "failure",
        "i will fail",
        "afraid to fail",
        "scared to fail",
        "not capable",
        "i can't do it",
        "je vais échouer",
        "peur d'échouer",
        "échec",
    ],
    "work_sensitivity": [
        "work",
        "job",
        "manager",
        "colleague",
        "meeting",
        "deadline",
        "project",
        "travail",
        "boulot",
        "chef",
        "collègue",
        "réunion",
        "deadline",
        "projet",
    ],
}


def _calculate_signal_value(content: str, keywords: list[str]) -> float:
    normalized_content = content.lower()

    matches = 0

    for keyword in keywords:
        if keyword in normalized_content:
            matches += 1

    if matches == 0:
        return 0.0

    if matches == 1:
        return 0.4

    if matches == 2:
        return 0.7

    return 0.9


def create_user_signals_from_journal(
    db: Session,
    journal_entry: JournalEntry,
) -> None:
    for signal_code, keywords in JOURNAL_SIGNAL_KEYWORDS.items():
        value = _calculate_signal_value(
            content=journal_entry.content,
            keywords=keywords,
        )

        if value == 0.0:
            continue

        signal = get_signal_by_code(db=db, code=signal_code)

        if signal is None:
            raise ValueError(f"Signal not found in catalog: {signal_code}")

        existing_signal = get_user_signal_by_source(
            db=db,
            source_type="journal_entry",
            source_id=journal_entry.id,
            signal_id=signal.id,
        )

        if existing_signal:
            continue

        create_user_signal(
            db=db,
            user_id=journal_entry.user_id,
            signal_id=signal.id,
            value=value,
            confidence=0.55,
            source_type="journal_entry",
            source_id=journal_entry.id,
            recorded_at=journal_entry.created_at,
        )