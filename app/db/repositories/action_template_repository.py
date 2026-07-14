from sqlalchemy.orm import Session

from app.db.models.action_template import ActionTemplate


def list_active_action_templates(
    db: Session,
) -> list[ActionTemplate]:
    return (
        db.query(ActionTemplate)
        .filter(ActionTemplate.is_active.is_(True))
        .order_by(
            ActionTemplate.base_priority.desc(),
            ActionTemplate.code.asc(),
        )
        .all()
    )


def get_action_template_by_code(
    db: Session,
    code: str,
) -> ActionTemplate | None:
    return (
        db.query(ActionTemplate)
        .filter(ActionTemplate.code == code)
        .first()
    )