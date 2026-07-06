from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.reflection_response_repository import (
    get_latest_reflection_response,
    list_reflection_responses_by_user_id,
)
from app.db.session import get_db
from app.schemas.reflection_response import ReflectionResponseRead
from app.services.reflection_response_service import (
    generate_reflection_response_for_user,
)

router = APIRouter()


@router.get("", response_model=list[ReflectionResponseRead])
def list_reflection_responses_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_reflection_responses_by_user_id(
        db=db,
        user_id=current_user.id,
    )


@router.get("/latest", response_model=ReflectionResponseRead)
def get_latest_reflection_response_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reflection_response = get_latest_reflection_response(
        db=db,
        user_id=current_user.id,
    )

    if reflection_response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reflection response not found.",
        )

    return reflection_response


@router.post("/generate", response_model=ReflectionResponseRead)
def generate_reflection_response_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return generate_reflection_response_for_user(
        db=db,
        user_id=current_user.id,
    )