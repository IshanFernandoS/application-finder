from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from ..analytics.dashboard_queries import AnalyticsQueries
from ..config import settings
from ..schemas import AnalyticsSummary


class AnalyticsService:
    def require_admin(self, provided_key: Optional[str]) -> None:
        if not settings.admin_api_key:
            raise PermissionError("ADMIN_API_KEY is required to access analytics endpoints.")
        if provided_key != settings.admin_api_key:
            raise PermissionError("Invalid admin API key.")

    def summary(self, db: Session) -> AnalyticsSummary:
        return AnalyticsQueries().summary(db)

    def recent(self, db: Session) -> List[Dict[str, object]]:
        return AnalyticsQueries().recent(db)

    def routes(self, db: Session) -> List[Dict[str, object]]:
        return AnalyticsQueries().routes(db)

    def referrers(self, db: Session) -> List[Dict[str, object]]:
        return AnalyticsQueries().referrers(db)

    def visitors_daily(self, db: Session) -> List[Dict[str, object]]:
        return AnalyticsQueries().visitors_daily(db)
