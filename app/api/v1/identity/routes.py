"""Identity model API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.identity_model import (
    IdentityModelGenerate,
    IdentityModelResponse,
    IdentitySelectionCreate,
    IdentitySelectionResponse,
)
from app.services import identity_model as identity_service
from app.services.event_log import log_event

router = APIRouter(prefix="/identity-models", tags=["identity"])


@router.post("/generate", response_model=list[dict])
def generate_identity_models(
    body: IdentityModelGenerate,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """
    Generate 3-5 identity models based on capability profile.
    
    Per product-spec 2.6:
    - differentiation must be non-empty
    - tone_examples >= 5 sentences
    - long_term_views 5-10 items
    """
    # Get capability profile if session_id provided
    capability_profile = body.capability_profile
    if body.session_id:
        from app.services.onboarding import get_profile
        profile = get_profile(db, body.session_id)
        if profile:
            import json
            capability_profile = {
                "skill_stack": json.loads(profile.skill_stack_json),
                "cognitive_style": profile.cognitive_style,
                "risk_tolerance": profile.risk_tolerance,
            }

    models = identity_service.generate_identity_models(
        db=db,
        user_id=body.user_id,
        session_id=body.session_id,
        capability_profile=capability_profile,
        count=body.count,
    )

    # Log event
    log_event(
        db=db,
        user_id=body.user_id,
        event_name="identity_models_generated",
        stage="MVP",
    )

    return [
        {
            "id": m.id,
            "title": m.title,
            "target_audience_pain": m.target_audience_pain,
            "differentiation": m.differentiation,
            "is_primary": m.is_primary,
            "is_backup": m.is_backup,
        }
        for m in models
    ]


@router.get("/users/{user_id}", response_model=list[IdentityModelResponse])
def get_user_identity_models(
    user_id: str,
    db: Session = Depends(get_db),
) -> list[IdentityModelResponse]:
    """Get all identity models for a user."""
    return identity_service.get_user_identity_models(db, user_id)


@router.get("/{model_id}", response_model=IdentityModelResponse)
def get_identity_model(
    model_id: str,
    db: Session = Depends(get_db),
) -> IdentityModelResponse:
    """Get identity model by ID."""
    model = identity_service.get_identity_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Identity model not found")
    return model


# Selection routes
selection_router = APIRouter(prefix="/identity-selections", tags=["identity"])


@selection_router.post("", response_model=dict)
def select_identity(
    body: IdentitySelectionCreate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Save user's primary and backup identity selection."""
    try:
        selection = identity_service.select_identity(
            db=db,
            user_id=body.user_id,
            primary_identity_id=body.primary_identity_id,
            backup_identity_id=body.backup_identity_id,
        )

        # Log event
        log_event(
            db=db,
            user_id=body.user_id,
            event_name="identity_selected",
            stage="MVP",
            identity_model_id=body.primary_identity_id,
        )

        return {
            "id": selection.id,
            "primary_identity_id": selection.primary_identity_id,
            "backup_identity_id": selection.backup_identity_id,
            "selected_at": selection.selected_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@selection_router.get("/users/{user_id}", response_model=IdentitySelectionResponse)
def get_user_selection(
    user_id: str,
    db: Session = Depends(get_db),
) -> IdentitySelectionResponse:
    """Get user's current identity selection."""
    selection = identity_service.get_user_selection(db, user_id)
    if not selection:
        raise HTTPException(status_code=404, detail="No selection found")
    return selection
