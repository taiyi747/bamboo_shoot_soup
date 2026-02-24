"""事件日志服务。"""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.consistency_check import EventLog


def log_event(
    db: Session,
    user_id: str,
    event_name: str,
    stage: str,
    identity_model_id: str | None = None,
    payload: dict | None = None,
) -> EventLog:
    """
    Log an event for analytics.
    
    Per product-spec 2.8:
    - event_name must be one of the defined events
    - stage must be MVP/V1/V2
    - Each event includes user_id, timestamp, stage, identity_model_id
    """
    # 事件名称白名单统一在服务层维护，避免多处口径漂移。
    valid_events = [
        "onboarding_started",
        "onboarding_completed",
        "identity_models_generated",
        "identity_selected",
        "launch_kit_generated",
        "content_published",
        "consistency_check_triggered",
        "experiment_created",
        "monetization_plan_started",
        "first_revenue_or_lead_confirmed",
    ]

    if event_name not in valid_events:
        raise ValueError(f"Invalid event_name: {event_name}. Must be one of {valid_events}")

    if stage not in ["MVP", "V1", "V2"]:
        raise ValueError(f"Invalid stage: {stage}. Must be MVP/V1/V2")

    # payload 以 JSON 文本存储，便于后续字段扩展。
    payload = payload or {}

    event = EventLog(
        user_id=user_id,
        event_name=event_name,
        stage=stage,
        identity_model_id=identity_model_id,
        payload_json=json.dumps(payload, ensure_ascii=False),
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(event)
    # 事件日志立即提交，保证可观测性与审计时效。
    db.commit()
    db.refresh(event)
    return event


def get_user_events(db: Session, user_id: str, limit: int = 100) -> list[EventLog]:
    """Get events for a user."""
    return (
        db.query(EventLog)
        .filter(EventLog.user_id == user_id)
        .order_by(EventLog.occurred_at.desc())
        .limit(limit)
        .all()
    )


def get_events_by_name(db: Session, event_name: str, limit: int = 100) -> list[EventLog]:
    """Get events by name."""
    return (
        db.query(EventLog)
        .filter(EventLog.event_name == event_name)
        .order_by(EventLog.occurred_at.desc())
        .limit(limit)
        .all()
    )


def get_recent_events(db: Session, limit: int = 100) -> list[EventLog]:
    """Get recent events across all users."""
    return db.query(EventLog).order_by(EventLog.occurred_at.desc()).limit(limit).all()
