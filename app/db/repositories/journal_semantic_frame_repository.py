from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.journal_semantic_frame import JournalSemanticFrame


def create_journal_semantic_frame(
    db: Session,
    user_id: UUID,
    journal_entry_id: UUID,
    journal_analysis_id: UUID,
    provider: str,
    model_name: str | None,
    prompt_version: str | None,
    core_dimensions_json: dict,
    emotion_labels_json: list,
    semantic_tags_json: list,
    life_domains_json: list,
    needs_json: list,
    additional_dimensions_json: list,
    event_candidates_json: list,
    safety_flags_json: list,
    overall_confidence: float | None,
    raw_output_json: dict,
) -> JournalSemanticFrame:
    semantic_frame = JournalSemanticFrame(
        user_id=user_id,
        journal_entry_id=journal_entry_id,
        journal_analysis_id=journal_analysis_id,
        provider=provider,
        model_name=model_name,
        prompt_version=prompt_version,
        core_dimensions_json=core_dimensions_json,
        emotion_labels_json=emotion_labels_json,
        semantic_tags_json=semantic_tags_json,
        life_domains_json=life_domains_json,
        needs_json=needs_json,
        additional_dimensions_json=additional_dimensions_json,
        event_candidates_json=event_candidates_json,
        safety_flags_json=safety_flags_json,
        overall_confidence=overall_confidence,
        raw_output_json=raw_output_json,
    )

    db.add(semantic_frame)
    db.commit()
    db.refresh(semantic_frame)

    return semantic_frame

def get_latest_journal_semantic_frame_for_user(
    db: Session,
    user_id: UUID,
) -> JournalSemanticFrame | None:
    return (
        db.query(JournalSemanticFrame)
        .filter(JournalSemanticFrame.user_id == user_id)
        .order_by(JournalSemanticFrame.created_at.desc())
        .first()
    )

def get_journal_semantic_frame_by_user_id_and_id(
    db: Session,
    user_id: UUID,
    semantic_frame_id: UUID,
) -> JournalSemanticFrame | None:
    return (
        db.query(JournalSemanticFrame)
        .filter(JournalSemanticFrame.user_id == user_id)
        .filter(JournalSemanticFrame.id == semantic_frame_id)
        .first()
    )


def get_journal_semantic_frame_by_journal_analysis_id(
    db: Session,
    journal_analysis_id: UUID,
) -> JournalSemanticFrame | None:
    return (
        db.query(JournalSemanticFrame)
        .filter(JournalSemanticFrame.journal_analysis_id == journal_analysis_id)
        .first()
    )


def list_journal_semantic_frames_by_user_id(
    db: Session,
    user_id: UUID,
    limit: int = 50,
) -> list[JournalSemanticFrame]:
    return (
        db.query(JournalSemanticFrame)
        .filter(JournalSemanticFrame.user_id == user_id)
        .order_by(JournalSemanticFrame.created_at.desc())
        .limit(limit)
        .all()
    )