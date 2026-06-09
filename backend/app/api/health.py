from __future__ import annotations

from fastapi import APIRouter

from ..config import settings
from ..services.deployment_service import DeploymentService
from ..services.mattergen_setup_service import MatterGenSetupService

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    mattergen = MatterGenSetupService().status()
    return {
        "status": "ok",
        "project": "Application Finder",
        "openai_configured": settings.openai_configured,
        "mattergen_status": mattergen.status,
        "deployment": DeploymentService().status(),
    }
