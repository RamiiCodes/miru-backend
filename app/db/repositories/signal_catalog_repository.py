from sqlalchemy.orm import Session

from app.db.models.signal_catalog import SignalCatalog


def get_signal_by_code(db: Session, code: str) -> SignalCatalog | None:
    return (
        db.query(SignalCatalog)
        .filter(
            SignalCatalog.code == code,
            SignalCatalog.is_active.is_(True),
        )
        .first()
    )