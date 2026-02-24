"""V1 monetization map API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import monetization_map as monetization_service
from app.services.event_log import log_event

router = APIRouter(prefix="/monetization-maps", tags=["monetization"])


class MonetizationMapGenerateRequest(BaseModel):
    user_id: str
    identity_model_id: str | None = None
    title: str = "12 周变现路线图"


@router.post("/generate", response_model=dict)
def generate_monetization_map(
    body: MonetizationMapGenerateRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    map_ = monetization_service.generate_monetization_map(
        db=db,
        user_id=body.user_id,
        identity_model_id=body.identity_model_id,
        title=body.title,
    )
    log_event(
        db=db,
        user_id=body.user_id,
        event_name="monetization_plan_started",
        stage="V1",
        identity_model_id=body.identity_model_id,
    )
    return {
        "id": map_.id,
        "title": map_.title,
        "status": map_.status,
        "weeks": [
            {
                "week_no": node.week_no,
                "objective": node.objective,
                "expected_output": node.expected_output,
                "validation_goal": node.validation_goal,
                "status": node.status,
            }
            for node in map_.week_nodes
        ],
    }


@router.get("", response_model=list[dict])
def list_monetization_maps(
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    maps = monetization_service.list_monetization_maps(db=db, user_id=user_id)
    return [
        {
            "id": map_.id,
            "title": map_.title,
            "status": map_.status,
            "created_at": map_.created_at.isoformat(),
            "weeks_count": len(map_.week_nodes),
        }
        for map_ in maps
    ]


@router.get("/{map_id}", response_model=dict)
def get_monetization_map(
    map_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    map_ = monetization_service.get_monetization_map(db, map_id)
    if not map_:
        raise HTTPException(status_code=404, detail="monetization map not found")
    return {
        "id": map_.id,
        "user_id": map_.user_id,
        "identity_model_id": map_.identity_model_id,
        "title": map_.title,
        "status": map_.status,
        "weeks": [
            {
                "id": node.id,
                "week_no": node.week_no,
                "objective": node.objective,
                "expected_output": node.expected_output,
                "validation_goal": node.validation_goal,
                "status": node.status,
            }
            for node in map_.week_nodes
        ],
    }
