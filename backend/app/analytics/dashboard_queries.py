from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import settings
from ..database import AccessLogRecord
from ..schemas import AnalyticsSummary


def _today_start() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime.combine(now.date(), time.min, tzinfo=timezone.utc)


class AnalyticsQueries:
    def summary(self, db: Session) -> AnalyticsSummary:
        start = _today_start()
        today = db.query(AccessLogRecord).filter(AccessLogRecord.timestamp >= start)
        visits = today.count()
        unique_visitors = today.with_entities(AccessLogRecord.visitor_hash).distinct().count()
        avg_duration = today.with_entities(func.avg(AccessLogRecord.request_duration_ms)).scalar() or 0.0
        errors = (
            db.query(AccessLogRecord.route, func.count(AccessLogRecord.id))
            .filter(AccessLogRecord.status_code >= 400)
            .group_by(AccessLogRecord.route)
            .all()
        )
        return AnalyticsSummary(
            visits_today=visits,
            unique_anonymous_visitors_today=unique_visitors,
            average_request_time_ms=float(round(avg_duration, 2)),
            errors_by_endpoint={route: count for route, count in errors},
            top_routes=self.routes(db),
            top_referrers=self.referrers(db),
            deployment_env=settings.deployment_env,
        )

    def recent(self, db: Session, limit: int = 30) -> List[Dict[str, object]]:
        rows = db.query(AccessLogRecord).order_by(AccessLogRecord.timestamp.desc()).limit(limit).all()
        return [
            {
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                "route": row.route,
                "method": row.method,
                "status_code": row.status_code,
                "referrer_domain": row.referrer_domain,
                "device_category": row.device_category,
                "browser_family": row.browser_family,
                "request_duration_ms": row.request_duration_ms,
            }
            for row in rows
        ]

    def routes(self, db: Session, limit: int = 10) -> List[Dict[str, object]]:
        rows = (
            db.query(AccessLogRecord.route, func.count(AccessLogRecord.id).label("count"))
            .group_by(AccessLogRecord.route)
            .order_by(func.count(AccessLogRecord.id).desc())
            .limit(limit)
            .all()
        )
        return [{"route": route, "count": count} for route, count in rows]

    def referrers(self, db: Session, limit: int = 10) -> List[Dict[str, object]]:
        rows = (
            db.query(AccessLogRecord.referrer_domain, func.count(AccessLogRecord.id).label("count"))
            .filter(AccessLogRecord.referrer_domain.isnot(None))
            .group_by(AccessLogRecord.referrer_domain)
            .order_by(func.count(AccessLogRecord.id).desc())
            .limit(limit)
            .all()
        )
        return [{"referrer_domain": domain, "count": count} for domain, count in rows]

    def visitors_daily(self, db: Session) -> List[Dict[str, object]]:
        rows = (
            db.query(func.date(AccessLogRecord.timestamp), func.count(func.distinct(AccessLogRecord.visitor_hash)))
            .group_by(func.date(AccessLogRecord.timestamp))
            .order_by(func.date(AccessLogRecord.timestamp).desc())
            .limit(30)
            .all()
        )
        return [{"date": str(day), "unique_visitors": count} for day, count in rows]
