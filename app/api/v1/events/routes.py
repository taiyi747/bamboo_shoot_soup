"""事件日志 API 路由。"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.event_log import EventLogCreate, EventLogResponse
from app.services import event_log as event_service

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=dict)
def create_event(
    body: EventLogCreate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Log an event for analytics.
    
    Per product-spec 2.8:
    - Valid events: onboarding_started, onboarding_completed, identity_models_generated,
      identity_selected, launch_kit_generated, content_published, consistency_check_triggered,
      experiment_created, monetization_plan_started, first_revenue_or_lead_confirmed
    - stage must be MVP/V1/V2
    """
    try:
        # 事件校验（event_name/stage）下沉在 service 层执行。
        event = event_service.log_event(
            db=db,
            user_id=body.user_id,
            event_name=body.event_name,
            stage=body.stage,
            identity_model_id=body.identity_model_id,
            payload=body.payload,
        )

        return {
            "id": event.id,
            "event_name": event.event_name,
            "occurred_at": event.occurred_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}", response_model=list[EventLogResponse])
def get_user_events(
    user_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[EventLogResponse]:
    """Get events for a user."""
    return event_service.get_user_events(db, user_id, limit)


@router.get("/name/{event_name}", response_model=list[EventLogResponse])
def get_events_by_name(
    event_name: str,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[EventLogResponse]:
    """Get events by name."""
    return event_service.get_events_by_name(db, event_name, limit)


@router.get("/recent", response_model=list[EventLogResponse])
def get_recent_events(
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[EventLogResponse]:
    """Get recent events across all users."""
    return event_service.get_recent_events(db, limit)
