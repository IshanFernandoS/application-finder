from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import httpx

from ..config import settings
from ..exceptions import ConfigurationError, DependencyUnavailableError


class ObjectStorageService:
    def __init__(self) -> None:
        self.backend = settings.object_storage_backend.lower()

    @property
    def enabled(self) -> bool:
        return self.backend == "supabase"

    @property
    def configured(self) -> bool:
        if not self.enabled:
            return True
        return settings.supabase_storage_configured

    def upload_file(self, path: Path, object_path: Optional[str] = None, content_type: Optional[str] = None) -> str:
        if not self.enabled:
            return str(path)
        if not settings.supabase_storage_configured:
            raise ConfigurationError(
                "Supabase Storage is enabled but SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, or SUPABASE_STORAGE_BUCKET is missing."
            )

        object_key = self._normalize_object_path(object_path or path.name)
        guessed_type = content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return self.upload_bytes(path.read_bytes(), object_key, guessed_type)

    def upload_bytes(self, data: bytes, object_path: str, content_type: str = "application/octet-stream") -> str:
        if not self.enabled:
            return object_path
        if not settings.supabase_storage_configured:
            raise ConfigurationError(
                "Supabase Storage is enabled but SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, or SUPABASE_STORAGE_BUCKET is missing."
            )

        object_key = self._normalize_object_path(object_path)
        url = self._object_url(object_key)
        headers = {
            "apikey": settings.supabase_service_role_key or "",
            "authorization": f"Bearer {settings.supabase_service_role_key or ''}",
            "content-type": content_type,
            "x-upsert": "true",
        }
        try:
            response = httpx.post(url, headers=headers, content=data, timeout=60.0)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise DependencyUnavailableError(f"Supabase Storage upload failed for {object_key}: {exc}") from exc
        return self.storage_uri(object_key)

    def storage_uri(self, object_path: str) -> str:
        return f"supabase://{settings.supabase_storage_bucket}/{self._normalize_object_path(object_path)}"

    def _object_url(self, object_path: str) -> str:
        base_url = (settings.supabase_url or "").rstrip("/")
        bucket = quote(settings.supabase_storage_bucket, safe="")
        key = quote(self._normalize_object_path(object_path), safe="/")
        return f"{base_url}/storage/v1/object/{bucket}/{key}"

    def _normalize_object_path(self, object_path: str) -> str:
        return object_path.strip().lstrip("/")
