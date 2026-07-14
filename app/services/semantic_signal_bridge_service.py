from typing import Any

from sqlalchemy.orm import Session

from app.db.models.journal_semantic_frame import JournalSemanticFrame
from app.db.models.signal_catalog import SignalCatalog
from app.db.models.user_signal import UserSignal


SEMANTIC_DIMENSION_SIGNAL_CODE_MAP = {
    "valence": "semantic_valence",
    "arousal": "semantic_arousal",
    "threat": "semantic_threat",
    "control": "semantic_control",
    "social_connection": "semantic_social_connection",
    "uncertainty": "semantic_uncertainty",
    "self_evaluation": "semantic_self_evaluation",
    "energy": "semantic_energy",
}


def create_user_signals_from_semantic_frame(
    db: Session,
    semantic_frame: JournalSemanticFrame | None,
) -> list[UserSignal]:
    """
    Bridge JournalSemanticFrame core dimensions into UserSignals.

    This does not infer new meaning.
    It only converts already-normalized semantic dimensions into generic signals.
    """

    if semantic_frame is None:
        return []

    created_signals: list[UserSignal] = []

    core_dimensions = semantic_frame.core_dimensions_json or {}

    for dimension_name, signal_code in SEMANTIC_DIMENSION_SIGNAL_CODE_MAP.items():
        raw_dimension = core_dimensions.get(dimension_name)

        if not isinstance(raw_dimension, dict):
            continue

        value = _safe_score(raw_dimension.get("value"))
        confidence = _safe_score(raw_dimension.get("confidence"))

        if value is None or confidence is None:
            continue

        signal_catalog = _get_signal_catalog_by_code(
            db=db,
            code=signal_code,
        )

        if signal_catalog is None:
            continue

        existing_signal = _get_existing_semantic_user_signal(
            db=db,
            semantic_frame=semantic_frame,
            signal_catalog=signal_catalog,
        )

        if existing_signal is not None:
            continue

        user_signal = _create_semantic_user_signal(
            db=db,
            semantic_frame=semantic_frame,
            signal_catalog=signal_catalog,
            value=value,
            confidence=confidence,
            raw_dimension=raw_dimension,
        )

        created_signals.append(user_signal)

    return created_signals


def _get_signal_catalog_by_code(
    db: Session,
    code: str,
) -> SignalCatalog | None:
    query = db.query(SignalCatalog)

    if hasattr(SignalCatalog, "code"):
        query = query.filter(SignalCatalog.code == code)
    else:
        query = query.filter(SignalCatalog.signal_code == code)

    if hasattr(SignalCatalog, "is_active"):
        query = query.filter(SignalCatalog.is_active.is_(True))

    return query.first()


def _get_existing_semantic_user_signal(
    db: Session,
    semantic_frame: JournalSemanticFrame,
    signal_catalog: SignalCatalog,
) -> UserSignal | None:
    signal_fk_column = _get_user_signal_fk_column()

    return (
        db.query(UserSignal)
        .filter(UserSignal.user_id == semantic_frame.user_id)
        .filter(UserSignal.source_type == "journal_semantic_frame")
        .filter(UserSignal.source_id == semantic_frame.id)
        .filter(signal_fk_column == signal_catalog.id)
        .first()
    )


def _create_semantic_user_signal(
    db: Session,
    semantic_frame: JournalSemanticFrame,
    signal_catalog: SignalCatalog,
    value: float,
    confidence: float,
    raw_dimension: dict[str, Any],
) -> UserSignal:
    signal_kwargs: dict[str, Any] = {
        "user_id": semantic_frame.user_id,
        "source_type": "journal_semantic_frame",
        "source_id": semantic_frame.id,
        "value": value,
        "confidence": confidence,
    }

    if hasattr(UserSignal, "signal_catalog_id"):
        signal_kwargs["signal_catalog_id"] = signal_catalog.id
    else:
        signal_kwargs["signal_id"] = signal_catalog.id

    if hasattr(UserSignal, "evidence"):
        signal_kwargs["evidence"] = raw_dimension.get("evidence")

    if hasattr(UserSignal, "reason"):
        signal_kwargs["reason"] = raw_dimension.get("reason")

    if hasattr(UserSignal, "timestamp"):
        signal_kwargs["timestamp"] = semantic_frame.created_at

    if hasattr(UserSignal, "recorded_at"):
        signal_kwargs["recorded_at"] = semantic_frame.created_at

    user_signal = UserSignal(**signal_kwargs)

    db.add(user_signal)
    db.commit()
    db.refresh(user_signal)

    return user_signal


def _get_user_signal_fk_column():
    if hasattr(UserSignal, "signal_catalog_id"):
        return UserSignal.signal_catalog_id

    return UserSignal.signal_id


def _safe_score(value: Any) -> float | None:
    if value is None:
        return None

    try:
        parsed_value = float(value)
    except (TypeError, ValueError):
        return None

    return max(0.0, min(1.0, parsed_value))