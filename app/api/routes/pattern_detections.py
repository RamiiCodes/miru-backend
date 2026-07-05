from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.pattern_detection_repository import (
    list_pattern_detections_by_user_id,
)
from app.db.session import get_db
from app.schemas.pattern_detection import PatternDetectionRead
from app.services.pattern_detection_service import detect_patterns_for_user

router = APIRouter()


@router.get("", response_model=list[PatternDetectionRead])
def list_pattern_detections_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_pattern_detections_by_user_id(
        db=db,
        user_id=current_user.id,
    )


@router.post("/detect", response_model=list[PatternDetectionRead])
def detect_pattern_detections_endpoint(
    window_days: int = Query(default=14, ge=2, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return detect_patterns_for_user(
        db=db,
        user_id=current_user.id,
        window_days=window_days,
    )