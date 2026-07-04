from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.llm_run import LLMRun


def create_llm_run(
    db: Session,
    user_id: UUID,
    source_type: str,
    source_id: UUID,
    provider: str,
    model_name: str,
    prompt_version: str,
    input_text: str,
    output_json: dict | None,
    status: str,
    error_message: str | None = None,
    latency_ms: int | None = None,
) -> LLMRun:
    llm_run = LLMRun(
        user_id=user_id,
        source_type=source_type,
        source_id=source_id,
        provider=provider,
        model_name=model_name,
        prompt_version=prompt_version,
        input_text=input_text,
        output_json=output_json,
        status=status,
        error_message=error_message,
        latency_ms=latency_ms,
    )

    db.add(llm_run)
    db.commit()
    db.refresh(llm_run)

    return llm_run


def list_llm_runs_by_user_id(
    db: Session,
    user_id: UUID,
) -> list[LLMRun]:
    return (
        db.query(LLMRun)
        .filter(LLMRun.user_id == user_id)
        .order_by(LLMRun.created_at.desc())
        .all()
    )