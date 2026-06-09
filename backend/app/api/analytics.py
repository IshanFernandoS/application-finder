from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.analytics_service import AnalyticsService
from .utils import raise_http

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _auth(x_admin_api_key: Optional[str] = Header(default=None)):
    try:
        AnalyticsService().require_admin(x_admin_api_key)
    except Exception as exc:
        raise_http(exc)


@router.get("/summary")
def summary(_: None = Depends(_auth), db: Session = Depends(get_db)):
    return AnalyticsService().summary(db)


@router.get("/recent")
def recent(_: None = Depends(_auth), db: Session = Depends(get_db)):
    return AnalyticsService().recent(db)


@router.get("/routes")
def routes(_: None = Depends(_auth), db: Session = Depends(get_db)):
    return AnalyticsService().routes(db)


@router.get("/referrers")
def referrers(_: None = Depends(_auth), db: Session = Depends(get_db)):
    return AnalyticsService().referrers(db)


@router.get("/visitors/daily")
def visitors_daily(_: None = Depends(_auth), db: Session = Depends(get_db)):
    return AnalyticsService().visitors_daily(db)
