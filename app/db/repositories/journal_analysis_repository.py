from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.journal_analysis import JournalAnalysis
from app.db.models.journal_extracted_signal import JournalExtractedSignal


def create_journal_analysis(
    db: Session,
    user_id: UUID,
    journal_entry_id: UUID,
    provider: str,
    model_name: str,
    prompt_version: str,
    status: str,
    language: str | None,
    summary: str | None,
    emotional_tone: str | None,
    safety_flags: list[str] | None,
    themes: list[str] | None,
    life_event_candidates_json: list[dict] | None,
    raw_output_json: dict | None,
    error_message: str | None,
    latency_ms: int | None,
) -> JournalAnalysis:
    analysis = JournalAnalysis(
        user_id=user_id,
        journal_entry_id=journal_entry_id,
        provider=provider,
        model_name=model_name,
        prompt_version=prompt_version,
        status=status,
        language=language,
        summary=summary,
        emotional_tone=emotional_tone,
        safety_flags=safety_flags,
        themes=themes,
        life_event_candidates_json=life_event_candidates_json,
        raw_output_json=raw_output_json,
        error_message=error_message,
        latency_ms=latency_ms,
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return analysis


def create_journal_extracted_signal(
    db: Session,
    user_id: UUID,
    journal_entry_id: UUID,
    journal_analysis_id: UUID,
    signal_code: str,
    value: float,
    confidence: float,
    evidence: str | None,
    reason: str | None,
) -> JournalExtractedSignal:
    extracted_signal = JournalExtractedSignal(
        user_id=user_id,
        journal_entry_id=journal_entry_id,
        journal_analysis_id=journal_analysis_id,
        signal_code=signal_code,
        value=value,
        confidence=confidence,
        evidence=evidence,
        reason=reason,
    )

    db.add(extracted_signal)
    db.commit()
    db.refresh(extracted_signal)

    return extracted_signal


def list_journal_analyses_by_user_id(
    db: Session,
    user_id: UUID,
) -> list[JournalAnalysis]:
    return (
        db.query(JournalAnalysis)
        .filter(JournalAnalysis.user_id == user_id)
        .order_by(JournalAnalysis.created_at.desc())
        .all()
    )


def list_extracted_signals_by_analysis_id(
    db: Session,
    journal_analysis_id: UUID,
) -> list[JournalExtractedSignal]:
    return (
        db.query(JournalExtractedSignal)
        .filter(JournalExtractedSignal.journal_analysis_id == journal_analysis_id)
        .order_by(JournalExtractedSignal.created_at.asc())
        .all()
    )