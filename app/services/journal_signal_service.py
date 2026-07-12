from datetime import datetime, timezone
from time import perf_counter

from sqlalchemy.orm import Session

from app.ai.journal_analyzer_factory import get_journal_analyzer
from app.db.models.journal_entry import JournalEntry
from app.db.models.llm_run import LLMRun
from app.db.models.signal_catalog import SignalCatalog
from app.db.models.user_signal import UserSignal
from app.db.repositories.journal_analysis_repository import (
    create_journal_analysis,
    create_journal_extracted_signal,
)
from app.services.safety_event_service import create_safety_events_from_flags
from app.services.life_event_service import create_life_events_from_journal_analysis

def _to_json_safe_dict(value) -> dict:
    if value is None:
        return {}

    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")

    if isinstance(value, dict):
        return value

    return {}


def _get_signal_catalog_by_code(
    db: Session,
    signal_code: str,
) -> SignalCatalog | None:
    signal_code_column = getattr(SignalCatalog, "code", None)

    if signal_code_column is None:
        signal_code_column = getattr(SignalCatalog, "signal_code", None)

    if signal_code_column is None:
        raise AttributeError(
            "SignalCatalog must expose either a 'code' or 'signal_code' column."
        )

    return (
        db.query(SignalCatalog)
        .filter(signal_code_column == signal_code)
        .first()
    )


def _create_llm_run(
    db: Session,
    journal_entry: JournalEntry,
    provider: str,
    model_name: str,
    prompt_version: str,
    status: str,
    output_json: dict | None,
    error_message: str | None,
    latency_ms: int | None,
) -> LLMRun:
    llm_run = LLMRun(
        user_id=journal_entry.user_id,
        source_type="journal_entry",
        source_id=journal_entry.id,
        provider=provider,
        model_name=model_name,
        prompt_version=prompt_version,
        input_text=journal_entry.content,
        output_json=output_json,
        status=status,
        error_message=error_message,
        latency_ms=latency_ms,
    )

    db.add(llm_run)
    db.commit()
    db.refresh(llm_run)

    return llm_run


def _create_user_signal_from_extracted_signal(
    db: Session,
    journal_entry: JournalEntry,
    signal_catalog: SignalCatalog,
    extracted_signal,
) -> UserSignal:
    user_signal_kwargs = {
        "user_id": journal_entry.user_id,
        "value": extracted_signal.value,
        "confidence": extracted_signal.confidence,
        "source_type": "journal_extracted_signal",
        "source_id": extracted_signal.id,
        "recorded_at": getattr(
            journal_entry,
            "created_at",
            datetime.now(timezone.utc),
        ),
    }

    if hasattr(UserSignal, "signal_catalog_id"):
        user_signal_kwargs["signal_catalog_id"] = signal_catalog.id
    elif hasattr(UserSignal, "signal_id"):
        user_signal_kwargs["signal_id"] = signal_catalog.id
    else:
        raise AttributeError(
            "UserSignal must expose either 'signal_catalog_id' or 'signal_id'."
        )

    user_signal = UserSignal(**user_signal_kwargs)

    db.add(user_signal)
    db.commit()
    db.refresh(user_signal)

    return user_signal


def create_user_signals_from_journal(
    db: Session,
    journal_entry: JournalEntry,
) -> list[UserSignal]:
    analyzer = get_journal_analyzer()

    start_time = perf_counter()

    try:
        analysis_result = analyzer.analyze(journal_entry.content)
        latency_ms = int((perf_counter() - start_time) * 1000)

    except Exception as exc:
        latency_ms = int((perf_counter() - start_time) * 1000)

        create_journal_analysis(
            db=db,
            user_id=journal_entry.user_id,
            journal_entry_id=journal_entry.id,
            provider=getattr(analyzer, "provider", "unknown"),
            model_name=getattr(analyzer, "model_name", "unknown"),
            prompt_version=getattr(analyzer, "prompt_version", "unknown"),
            status="failed",
            language=None,
            summary=None,
            emotional_tone=None,
            safety_flags=[],
            themes=[],
            life_event_candidates_json=[],
            raw_output_json=None,
            error_message=str(exc),
            latency_ms=latency_ms,
        )

        _create_llm_run(
            db=db,
            journal_entry=journal_entry,
            provider=getattr(analyzer, "provider", "unknown"),
            model_name=getattr(analyzer, "model_name", "unknown"),
            prompt_version=getattr(analyzer, "prompt_version", "unknown"),
            status="failed",
            output_json=None,
            error_message=str(exc),
            latency_ms=latency_ms,
        )

        return []

    raw_output_json = _to_json_safe_dict(analysis_result)

    life_event_candidates_json = [
        candidate.model_dump(mode="json")
        if hasattr(candidate, "model_dump")
        else candidate
        for candidate in analysis_result.life_event_candidates
    ]

    journal_analysis = create_journal_analysis(
        db=db,
        user_id=journal_entry.user_id,
        journal_entry_id=journal_entry.id,
        provider=analysis_result.provider,
        model_name=analysis_result.model_name,
        prompt_version=analysis_result.prompt_version,
        status="success",
        language=analysis_result.language,
        summary=analysis_result.summary,
        emotional_tone=analysis_result.emotional_tone,
        safety_flags=analysis_result.safety_flags,
        themes=analysis_result.themes,
        life_event_candidates_json=life_event_candidates_json,
        raw_output_json=raw_output_json,
        error_message=None,
        latency_ms=latency_ms,
    )
    create_life_events_from_journal_analysis(
    db=db,
    user_id=journal_entry.user_id,
    journal_analysis_id=journal_analysis.id,
    life_event_candidates=life_event_candidates_json,
    )

    _create_llm_run(
        db=db,
        journal_entry=journal_entry,
        provider=analysis_result.provider,
        model_name=analysis_result.model_name,
        prompt_version=analysis_result.prompt_version,
        status="success",
        output_json=raw_output_json,
        error_message=None,
        latency_ms=latency_ms,
    )

    create_safety_events_from_flags(
        db=db,
        user_id=journal_entry.user_id,
        source_type="journal_entry",
        source_id=journal_entry.id,
        safety_flags=analysis_result.safety_flags,
    )

    created_user_signals: list[UserSignal] = []

    for detected_signal in analysis_result.detected_signals:
        extracted_signal = create_journal_extracted_signal(
            db=db,
            user_id=journal_entry.user_id,
            journal_entry_id=journal_entry.id,
            journal_analysis_id=journal_analysis.id,
            signal_code=detected_signal.signal_code,
            value=detected_signal.value,
            confidence=detected_signal.confidence,
            evidence=detected_signal.evidence,
            reason=detected_signal.reason,
        )

        signal_catalog = _get_signal_catalog_by_code(
            db=db,
            signal_code=detected_signal.signal_code,
        )

        if signal_catalog is None:
            continue

        user_signal = _create_user_signal_from_extracted_signal(
            db=db,
            journal_entry=journal_entry,
            signal_catalog=signal_catalog,
            extracted_signal=extracted_signal,
        )

        created_user_signals.append(user_signal)

    return created_user_signals
