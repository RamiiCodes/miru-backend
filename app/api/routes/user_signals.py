from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.user_signal_repository import list_user_signals_by_user_id
from app.db.session import get_db
from app.schemas.user_signal import UserSignalRead

router = APIRouter()


@router.get("", response_model=list[UserSignalRead])
def list_user_signals_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_user_signals_by_user_id(db=db, user_id=current_user.id)