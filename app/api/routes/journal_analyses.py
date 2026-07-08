from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.journal_analysis_repository import (
    list_extracted_signals_by_analysis_id,
    list_journal_analyses_by_user_id,
)
from app.db.session import get_db
from app.schemas.journal_analysis import JournalAnalysisRead

router = APIRouter()


@router.get("", response_model=list[JournalAnalysisRead])
def list_journal_analyses_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analyses = list_journal_analyses_by_user_id(
        db=db,
        user_id=current_user.id,
    )

    response_items = []

    for analysis in analyses:
        extracted_signals = list_extracted_signals_by_analysis_id(
            db=db,
            journal_analysis_id=analysis.id,
        )

        response_items.append(
            {
                **analysis.__dict__,
                "extracted_signals": extracted_signals,
            }
        )

    return response_items