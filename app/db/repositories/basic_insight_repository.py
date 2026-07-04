from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.basic_insight import BasicInsight


def get_basic_insight_by_state_and_rule(
    db: Session,
    state_id: UUID,
    rule_code: str,
) -> BasicInsight | None:
    return (
        db.query(BasicInsight)
        .filter(
            BasicInsight.state_id == state_id,
            BasicInsight.rule_code == rule_code,
        )
        .first()
    )


def create_basic_insight(
    db: Session,
    user_id: UUID,
    state_id: UUID,
    rule_code: str,
    title: str,
    message: str,
    insight_type: str,
    severity: str,
    confidence: float,
    model_version: str = "basic_insight_v0_1",
) -> BasicInsight:
    existing_insight = get_basic_insight_by_state_and_rule(
        db=db,
        state_id=state_id,
        rule_code=rule_code,
    )

    if existing_insight:
        return existing_insight

    insight = BasicInsight(
        user_id=user_id,
        state_id=state_id,
        rule_code=rule_code,
        title=title,
        message=message,
        insight_type=insight_type,
        severity=severity,
        confidence=confidence,
        model_version=model_version,
    )

    db.add(insight)
    db.commit()
    db.refresh(insight)

    return insight


def list_basic_insights_by_user_id(
    db: Session,
    user_id: UUID,
) -> list[BasicInsight]:
    return (
        db.query(BasicInsight)
        .filter(BasicInsight.user_id == user_id)
        .order_by(BasicInsight.created_at.desc())
        .all()
    )