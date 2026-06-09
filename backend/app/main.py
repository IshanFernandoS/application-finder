from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .analytics.access_logger import AccessLogMiddleware
from .api import analytics, application_space, evals, gaps, health, hpc, ingestion, materials, mattergen, pathways, rag, reports, scopes, validation
from .config import settings
from .database import SessionLocal, init_db
from .services.scope_service import ScopeService


def create_app() -> FastAPI:
    app = FastAPI(
        title="Application Finder",
        description="Application Finder — Electromagnetic Application-Space-Guided Generative Inverse Materials Design Platform",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url, "http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AccessLogMiddleware)
    app.include_router(health.router, prefix="/api")
    app.include_router(scopes.router, prefix="/api")
    app.include_router(ingestion.router, prefix="/api")
    app.include_router(application_space.router, prefix="/api")
    app.include_router(gaps.router, prefix="/api")
    app.include_router(rag.router, prefix="/api")
    app.include_router(pathways.router, prefix="/api")
    app.include_router(materials.router, prefix="/api")
    app.include_router(mattergen.router, prefix="/api")
    app.include_router(validation.router, prefix="/api")
    app.include_router(evals.router, prefix="/api")
    app.include_router(analytics.router, prefix="/api")
    app.include_router(reports.router, prefix="/api")
    app.include_router(hpc.router, prefix="/api")

    @app.on_event("startup")
    def startup() -> None:
        init_db()
        with SessionLocal() as db:
            ScopeService().ensure_default_scope(db)

    return app


app = create_app()
