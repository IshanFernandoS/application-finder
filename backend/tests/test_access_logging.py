import asyncio
from datetime import date
from dataclasses import replace
from types import SimpleNamespace

import backend.app.analytics.access_logger as access_logger_module
from backend.app.analytics.anonymize import anonymized_hash, coarse_user_agent
from backend.app.analytics.access_logger import AccessLogMiddleware
from starlette.responses import Response


def test_access_hash_does_not_expose_raw_ip():
    hashed = anonymized_hash("192.0.2.1", "Mozilla/5.0", "salt", day=date(2026, 6, 9))
    assert "192.0.2.1" not in hashed
    assert len(hashed) == 64


def test_coarse_user_agent_drops_raw_string():
    device, browser = coarse_user_agent("Mozilla/5.0 Chrome Mobile")
    assert device == "mobile"
    assert browser == "chrome"


def test_access_log_middleware_does_not_fail_request_when_database_write_fails(monkeypatch):
    class BrokenSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def add(self, record):
            pass

        def commit(self):
            raise RuntimeError("database is locked")

    monkeypatch.setattr(access_logger_module, "SessionLocal", lambda: BrokenSession())
    monkeypatch.setattr(
        access_logger_module,
        "settings",
        replace(access_logger_module.settings, enable_analytics=True, access_logging_enabled=True),
    )
    middleware = AccessLogMiddleware(app=lambda scope, receive, send: None)
    request = SimpleNamespace(
        headers={},
        client=SimpleNamespace(host="127.0.0.1"),
        url=SimpleNamespace(path="/api/health"),
        method="GET",
    )

    async def call_next(_request):
        return Response("ok", status_code=200)

    response = asyncio.run(middleware.dispatch(request, call_next))

    assert response.status_code == 200
