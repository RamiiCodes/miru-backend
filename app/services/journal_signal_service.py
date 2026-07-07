import time

from sqlalchemy.orm import Session

from app.ai.journal_analyzer_factory import get_journal_analyzer
from app.db.models.journal_entry import JournalEntry
from app.db.repositories.llm_run_repository import create_llm_run
from app.db.repositories.signal_catalog_repository import get_signal_by_code
from app.services.safety_event_service import create_safety_events_from_flags
from app.db.repositories.user_signal_repository import (
    create_user_signal,
    get_user_signal_by_source,
)


def create_user_signals_from_journal(
    db: Session,
    journal_entry: JournalEntry,
) -> None:
    analyzer = get_journal_analyzer()

    started_at = time.perf_counter()

    try:
        analysis_result = analyzer.analyze(journal_entry.content)
        create_safety_events_from_flags(
            db=db,
            user_id=journal_entry.user_id,
            source_type="journal_entry",
            source_id=journal_entry.id,
            safety_flags=analysis_result.safety_flags,
                                        )

        latency_ms = int((time.perf_counter() - started_at) * 1000)

        create_llm_run(
            db=db,
            user_id=journal_entry.user_id,
            source_type="journal_entry",
            source_id=journal_entry.id,
            provider=analysis_result.provider,
            model_name=analysis_result.model_name,
            prompt_version=analysis_result.prompt_version,
            input_text=journal_entry.content,
            output_json=analysis_result.model_dump(mode="json"),
            status="success",
            error_message=None,
            latency_ms=latency_ms,
        )

    except Exception as exc:
        latency_ms = int((time.perf_counter() - started_at) * 1000)

        create_llm_run(
            db=db,
            user_id=journal_entry.user_id,
            source_type="journal_entry",
            source_id=journal_entry.id,
            provider=analyzer.provider,
            model_name=analyzer.model_name,
            prompt_version=analyzer.prompt_version,
            input_text=journal_entry.content,
            output_json=None,
            status="failed",
            error_message=str(exc),
            latency_ms=latency_ms,
        )

        raise

    for detected_signal in analysis_result.detected_signals:
        signal = get_signal_by_code(
            db=db,
            code=detected_signal.signal_code,
        )

        if signal is None:
            raise ValueError(
                f"Signal not found in catalog: {detected_signal.signal_code}"
            )

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
            value=detected_signal.value,
            confidence=detected_signal.confidence,
            source_type="journal_entry",
            source_id=journal_entry.id,
            recorded_at=journal_entry.created_at,
        )