from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.journal_analyzer import JournalAnalysisResult
from app.db.models.journal_semantic_frame import JournalSemanticFrame
from app.db.repositories.journal_semantic_frame_repository import (
    create_journal_semantic_frame,
    get_journal_semantic_frame_by_user_id_and_id,
    list_journal_semantic_frames_by_user_id,
)


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

    return create_journal_semantic_frame(
        db=db,
        user_id=user_id,
        journal_entry_id=journal_entry_id,
        journal_analysis_id=journal_analysis_id,
        provider=analysis_result.provider,
        model_name=analysis_result.model_name,
        prompt_version=analysis_result.prompt_version,
        core_dimensions_json={
            key: value.model_dump(mode="json")
            for key, value in semantic_frame.core_dimensions.items()
        },
        emotion_labels_json=semantic_frame.emotion_labels,
        semantic_tags_json=semantic_frame.semantic_tags,
        life_domains_json=semantic_frame.life_domains,
        needs_json=semantic_frame.needs,
        additional_dimensions_json=[
            dimension.model_dump(mode="json")
            for dimension in semantic_frame.additional_dimensions
        ],
        event_candidates_json=[
            candidate.model_dump(mode="json")
            for candidate in semantic_frame.event_candidates
        ],
        safety_flags_json=semantic_frame.safety_flags,
        overall_confidence=semantic_frame.overall_confidence,
        raw_output_json=semantic_frame.raw_output,
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