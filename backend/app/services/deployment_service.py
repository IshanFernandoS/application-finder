from __future__ import annotations

from typing import Dict

from ..config import settings


class DeploymentService:
    def status(self) -> Dict[str, object]:
        return {
            "deployment_env": settings.deployment_env,
            "frontend_url": settings.frontend_url,
            "backend_url": settings.backend_url,
            "database_configured": bool(settings.database_url),
            "vector_backend": settings.vector_backend,
            "object_storage_backend": settings.object_storage_backend,
            "object_storage_configured": settings.supabase_storage_configured
            if settings.object_storage_backend.lower() == "supabase"
            else True,
            "openai_configured": settings.openai_configured,
            "analytics_enabled": settings.enable_analytics,
            "mattergen_enabled": settings.enable_mattergen,
            "hpc_enabled": settings.hpc_enabled,
            "hpc_configured": settings.hpc_configured,
        }
