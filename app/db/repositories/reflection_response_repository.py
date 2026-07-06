from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.reflection_response import ReflectionResponse


def create_reflection_response(
    db: Session,
    user_id: UUID,
    source_type: str,
    source_id: UUID | None,
    title: str,
    message: str,
    tone: str,
    response_type: str,
    suggested_action_id: UUID | None,
    source_snapshot_json: dict | None,
    model_version: str = "reflection_response_v0_1",
) -> ReflectionResponse:
    response = ReflectionResponse(
        user_id=user_id,
        source_type=source_type,
        source_id=source_id,
        title=title,
        message=message,
        tone=tone,
        response_type=response_type,
        suggested_action_id=suggested_action_id,
        source_snapshot_json=source_snapshot_json,
        model_version=model_version,
    )

    db.add(response)
    db.commit()
    db.refresh(response)

    return response


def list_reflection_responses_by_user_id(
    db: Session,
    user_id: UUID,
) -> list[ReflectionResponse]:
    return (
        db.query(ReflectionResponse)
        .filter(ReflectionResponse.user_id == user_id)
        .order_by(ReflectionResponse.created_at.desc())
        .all()
    )


def get_latest_reflection_response(
    db: Session,
    user_id: UUID,
) -> ReflectionResponse | None:
    return (
        db.query(ReflectionResponse)
        .filter(ReflectionResponse.user_id == user_id)
        .order_by(ReflectionResponse.created_at.desc())
        .first()
    )