from __future__ import annotations

import time
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware

from ..config import settings
from ..database import AccessLogRecord, SessionLocal
from .anonymize import anonymized_hash, coarse_user_agent


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        if settings.enable_analytics and settings.access_logging_enabled:
            try:
                duration_ms = (time.perf_counter() - start) * 1000.0
                user_agent = request.headers.get("user-agent", "")
                ip = request.client.host if request.client else ""
                visitor = anonymized_hash(ip, user_agent, settings.access_log_hash_salt or "local-dev")
                session = anonymized_hash(ip, user_agent, settings.access_log_hash_salt or "local-dev")
                device, browser = coarse_user_agent(user_agent)
                referrer = request.headers.get("referer") or request.headers.get("referrer") or ""
                referrer_domain = urlparse(referrer).netloc if referrer else None
                with SessionLocal() as db:
                    db.add(
                        AccessLogRecord(
                            route=request.url.path,
                            method=request.method,
                            status_code=response.status_code,
                            referrer_domain=referrer_domain,
                            device_category=device,
                            browser_family=browser,
                            visitor_hash=visitor,
                            session_hash=session,
                            request_duration_ms=duration_ms,
                            deployment_env=settings.deployment_env,
                            raw_ip=ip if settings.access_log_store_raw_ip else None,
                            raw_user_agent=user_agent if settings.access_log_store_user_agent_raw else None,
                        )
                    )
                    db.commit()
            except Exception:
                pass
        return response
