from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.user_coping_style_repository import (
    get_user_coping_style_by_user_id,
)
from app.db.session import get_db
from app.schemas.user_coping_style import (
    UserCopingStyleRead,
    UserCopingStyleUpdate,
    UserCopingStyleUpsert,
)
from app.services.user_coping_style_service import (
    create_or_replace_user_coping_style,
    update_user_coping_style_for_user,
)

router = APIRouter()


@router.get("", response_model=UserCopingStyleRead)
def get_user_coping_style_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    coping_style = get_user_coping_style_by_user_id(
        db=db,
        user_id=current_user.id,
    )

    if coping_style is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User coping style not found.",
        )

    return coping_style


@router.put("", response_model=UserCopingStyleRead)
def upsert_user_coping_style_endpoint(
    payload: UserCopingStyleUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_or_replace_user_coping_style(
        db=db,
        user_id=current_user.id,
        payload=payload,
    )


@router.patch("", response_model=UserCopingStyleRead)
def patch_user_coping_style_endpoint(
    payload: UserCopingStyleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_user_coping_style_for_user(
        db=db,
        user_id=current_user.id,
        payload=payload,
    )