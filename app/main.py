from fastapi import FastAPI

from app.api.routes.health import router as health_router

app = FastAPI(
    title="Miru API",
    version="0.1.0",
    description="Miru backend API - V0.1",
)

app.include_router(health_router, prefix="/health", tags=["Health"])