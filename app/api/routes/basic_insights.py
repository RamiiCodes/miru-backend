from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.basic_insight_repository import list_basic_insights_by_user_id
from app.db.session import get_db
from app.schemas.basic_insight import BasicInsightRead
from app.services.basic_insight_service import generate_basic_insights

router = APIRouter()


@router.get("", response_model=list[BasicInsightRead])
def list_basic_insights_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_basic_insights_by_user_id(
        db=db,
        user_id=current_user.id,
    )


@router.post("/generate", response_model=list[BasicInsightRead])
def generate_basic_insights_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return generate_basic_insights(
        db=db,
        user_id=current_user.id,
    )