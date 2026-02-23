"""Launch kit API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.launch_kit import LaunchKitGenerate, LaunchKitResponse
from app.services import launch_kit as launch_kit_service
from app.services.event_log import log_event

router = APIRouter(prefix="/launch-kits", tags=["launch_kit"])


@router.post("/generate", response_model=dict)
def generate_launch_kit(
    body: LaunchKitGenerate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Generate 7-Day Launch Kit."""
    kit = launch_kit_service.generate_launch_kit(
        db=db,
        user_id=body.user_id,
        identity_model_id=body.identity_model_id,
        constitution_id=body.constitution_id,
        sustainable_columns=body.sustainable_columns,
        growth_experiment_suggestion=body.growth_experiment_suggestion,
    )

    # Log event
    log_event(
        db=db,
        user_id=body.user_id,
        event_name="launch_kit_generated",
        stage="MVP",
        identity_model_id=body.identity_model_id,
    )

    return {
        "id": kit.id,
        "user_id": kit.user_id,
        "days": [
            {
                "day_no": d.day_no,
                "theme": d.theme,
                "opening_text": d.opening_text,
            }
            for d in kit.days
        ],
    }


@router.get("/users/{user_id}", response_model=list[LaunchKitResponse])
def get_user_launch_kits(
    user_id: str,
    db: Session = Depends(get_db),
) -> list[LaunchKitResponse]:
    """Get all launch kits for a user."""
    return launch_kit_service.get_user_launch_kits(db, user_id)


@router.get("/users/{user_id}/latest", response_model=LaunchKitResponse)
def get_latest_launch_kit(
    user_id: str,
    db: Session = Depends(get_db),
) -> LaunchKitResponse:
    """Get user's latest launch kit."""
    kit = launch_kit_service.get_latest_launch_kit(db, user_id)
    if not kit:
        raise HTTPException(status_code=404, detail="No launch kit found")
    return kit


@router.get("/{kit_id}", response_model=LaunchKitResponse)
def get_launch_kit(
    kit_id: str,
    db: Session = Depends(get_db),
) -> LaunchKitResponse:
    """Get launch kit by ID."""
    kit = launch_kit_service.get_launch_kit(db, kit_id)
    if not kit:
        raise HTTPException(status_code=404, detail="Launch kit not found")
    return kit
