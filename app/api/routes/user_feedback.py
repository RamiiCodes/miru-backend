from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.user_feedback_repository import list_user_feedback_by_user_id
from app.db.session import get_db
from app.schemas.user_feedback import UserFeedbackCreate, UserFeedbackRead
from app.services.user_feedback_service import create_or_update_user_feedback

router = APIRouter()


@router.get("", response_model=list[UserFeedbackRead])
def list_user_feedback_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_user_feedback_by_user_id(
        db=db,
        user_id=current_user.id,
    )


@router.post("", response_model=UserFeedbackRead)
def create_user_feedback_endpoint(
    payload: UserFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_or_update_user_feedback(
        db=db,
        user_id=current_user.id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        rating=payload.rating,
        comment=payload.comment,
    )