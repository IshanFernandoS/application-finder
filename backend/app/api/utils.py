from __future__ import annotations

from fastapi import HTTPException

from ..exceptions import ConfigurationError, DependencyUnavailableError, ValidationFailure


def raise_http(exc: Exception) -> None:
    if isinstance(exc, KeyError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, PermissionError):
        raise HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, (ConfigurationError, DependencyUnavailableError, ValidationFailure)):
        raise HTTPException(status_code=409, detail=str(exc))
    raise HTTPException(status_code=500, detail=str(exc))
