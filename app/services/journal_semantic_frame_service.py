from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.journal_analyzer import JournalAnalysisResult
from app.db.models.journal_semantic_frame import JournalSemanticFrame
from app.db.repositories.journal_semantic_frame_repository import (
    create_journal_semantic_frame,
    get_journal_semantic_frame_by_user_id_and_id,
    list_journal_semantic_frames_by_user_id,
)
from app.services.semantic_frame_normalizer import normalize_semantic_frame

def create_semantic_frame_from_analysis_result(
    db: Session,
    user_id: UUID,
    journal_entry_id: UUID,
    journal_analysis_id: UUID,
    analysis_result: JournalAnalysisResult,
) -> JournalSemanticFrame | None:
    semantic_frame = analysis_result.semantic_frame

    if semantic_frame is None:
        return None

    normalized_semantic_frame = normalize_semantic_frame(
    semantic_frame=semantic_frame,
)
    return create_journal_semantic_frame(
    db=db,
    user_id=user_id,
    journal_entry_id=journal_entry_id,
    journal_analysis_id=journal_analysis_id,
    provider=analysis_result.provider,
    model_name=analysis_result.model_name,
    prompt_version=analysis_result.prompt_version,
    core_dimensions_json=normalized_semantic_frame.core_dimensions_json,
    emotion_labels_json=normalized_semantic_frame.emotion_labels_json,
    semantic_tags_json=normalized_semantic_frame.semantic_tags_json,
    life_domains_json=normalized_semantic_frame.life_domains_json,
    needs_json=normalized_semantic_frame.needs_json,
    additional_dimensions_json=normalized_semantic_frame.additional_dimensions_json,
    event_candidates_json=normalized_semantic_frame.event_candidates_json,
    safety_flags_json=normalized_semantic_frame.safety_flags_json,
    overall_confidence=normalized_semantic_frame.overall_confidence,
    raw_output_json=normalized_semantic_frame.raw_output_json,
)


def list_user_journal_semantic_frames(
    db: Session,
    user_id: UUID,
    limit: int = 50,
) -> list[JournalSemanticFrame]:
    return list_journal_semantic_frames_by_user_id(
        db=db,
        user_id=user_id,
        limit=limit,
    )


def get_user_journal_semantic_frame(
    db: Session,
    user_id: UUID,
    semantic_frame_id: UUID,
) -> JournalSemanticFrame | None:
    return get_journal_semantic_frame_by_user_id_and_id(
        db=db,
        user_id=user_id,
        semantic_frame_id=semantic_frame_id,
    )