"""Monetization map API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.monetization_map import MonetizationMapGenerate, MonetizationMapResponse
from app.services import monetization_map as monetization_map_service
from app.services.event_log import log_event
from app.services.llm_client import LLMServiceError

router = APIRouter(prefix="/monetization-maps", tags=["monetization_map"])


@router.post("/generate", response_model=dict)
def generate_monetization_map(
    body: MonetizationMapGenerate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        monetization_map, degraded, degrade_reason = monetization_map_service.generate_monetization_map(
            db,
            user_id=body.user_id,
            identity_model_id=body.identity_model_id,
            constitution_id=body.constitution_id,
            hints=body.hints,
        )
    except LLMServiceError as error:
        raise HTTPException(status_code=502, detail=error.to_detail()) from error

    log_event(
        db,
        user_id=body.user_id,
        event_name="monetization_plan_started",
        stage="V1",
        identity_model_id=monetization_map.identity_model_id,
        payload={"map_id": monetization_map.id},
    )

    return {
        "id": monetization_map.id,
        "user_id": monetization_map.user_id,
        "identity_model_id": monetization_map.identity_model_id,
        "constitution_id": monetization_map.constitution_id,
        "degraded": degraded,
        "degrade_reason": degrade_reason,
    }


@router.get("/users/{user_id}", response_model=list[MonetizationMapResponse])
def get_user_monetization_maps(
    user_id: str,
    db: Session = Depends(get_db),
) -> list[MonetizationMapResponse]:
    return monetization_map_service.get_user_monetization_maps(db, user_id)


@router.get("/{map_id}", response_model=MonetizationMapResponse)
def get_monetization_map(
    map_id: str,
    db: Session = Depends(get_db),
) -> MonetizationMapResponse:
    monetization_map = monetization_map_service.get_monetization_map(db, map_id)
    if not monetization_map:
        raise HTTPException(status_code=404, detail="Monetization map not found")
    return monetization_map
