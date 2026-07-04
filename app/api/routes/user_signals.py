from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.repositories.user_signal_repository import list_user_signals_by_user_id
from app.db.session import get_db
from app.schemas.user_signal import UserSignalRead

router = APIRouter()


@router.get("/users/{user_id}", response_model=list[UserSignalRead])
def list_user_signals_endpoint(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    return list_user_signals_by_user_id(db=db, user_id=user_id)