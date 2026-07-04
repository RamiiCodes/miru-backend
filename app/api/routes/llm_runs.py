from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.llm_run_repository import list_llm_runs_by_user_id
from app.db.session import get_db
from app.schemas.llm_run import LLMRunRead

router = APIRouter()


@router.get("", response_model=list[LLMRunRead])
def list_llm_runs_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_llm_runs_by_user_id(
        db=db,
        user_id=current_user.id,
    )