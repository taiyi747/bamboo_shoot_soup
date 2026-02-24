"""V1 dashboard metrics service."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.consistency_check import EventLog


def _count(
    db: Session,
    *,
    event_name: str,
    since: datetime | None = None,
) -> int:
    query = db.query(EventLog).filter(EventLog.event_name == event_name)
    if since:
        query = query.filter(EventLog.occurred_at >= since)
    return query.count()


def build_dashboard_metrics(db: Session, *, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    since_7d = now - timedelta(days=7)
    since_28d = now - timedelta(days=28)

    onboarding_completed = _count(db, event_name="onboarding_completed", since=since_28d)
    identity_selected = _count(db, event_name="identity_selected", since=since_28d)
    launch_kit_generated = _count(db, event_name="launch_kit_generated", since=since_28d)
    content_published_7d = _count(db, event_name="content_published", since=since_7d)
    monetization_started_28d = _count(db, event_name="monetization_plan_started", since=since_28d)
    monetization_validated_28d = _count(
        db,
        event_name="first_revenue_or_lead_confirmed",
        since=since_28d,
    )

    week_retention = 0.0
    if onboarding_completed > 0:
        active_users_7d = (
            db.query(EventLog.user_id)
            .filter(EventLog.occurred_at >= since_7d)
            .distinct()
            .count()
        )
        baseline_users_28d = (
            db.query(EventLog.user_id)
            .filter(
                EventLog.event_name == "onboarding_completed",
                EventLog.occurred_at >= since_28d,
            )
            .distinct()
            .count()
        )
        if baseline_users_28d > 0:
            week_retention = round(active_users_7d / baseline_users_28d, 4)

    publish_rate = round(content_published_7d / max(identity_selected, 1), 4)
    monetization_validation_rate = round(
        monetization_validated_28d / max(monetization_started_28d, 1),
        4,
    )

    return {
        "window": {"retention_days": 28, "publishing_days": 7},
        "funnel": {
            "onboarding_completed": onboarding_completed,
            "identity_selected": identity_selected,
            "launch_kit_generated": launch_kit_generated,
        },
        "weekly_retention": week_retention,
        "publish_rate": publish_rate,
        "monetization_validation_rate": monetization_validation_rate,
    }
