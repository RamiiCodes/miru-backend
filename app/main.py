from fastapi import FastAPI

from app.api.routes.checkins import router as checkins_router
from app.api.routes.health import router as health_router
from app.api.routes.journals import router as journals_router
from app.api.routes.users import router as users_router
from app.api.routes.user_signals import router as user_signals_router
from app.api.routes.current_emotional_state import router as current_state_router
from app.api.routes.auth import router as auth_router

app = FastAPI(
    title="Miru API",
    version="0.1.0",
    description="Miru backend API - V0.1",
)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(journals_router, prefix="/journals", tags=["Journals"])
app.include_router(checkins_router, prefix="/checkins", tags=["Structured Check-ins"])
app.include_router(user_signals_router, prefix="/signals", tags=["UserSignals"])
app.include_router(current_state_router, prefix="/state", tags=["Current Emotional State"])