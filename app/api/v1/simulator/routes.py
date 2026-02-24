"""V2 simulator API routes."""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import simulator as simulator_service

router = APIRouter(prefix="/simulator", tags=["simulator"])


class PrepublishEvaluationRequest(BaseModel):
    user_id: str
    identity_model_id: str | None = None
    draft_text: str
    platform: str
    stage_goal: str


@router.post("/prepublish-evaluations", response_model=dict)
def prepublish_evaluation(
    body: PrepublishEvaluationRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    evaluation = simulator_service.evaluate_prepublish(
        db=db,
        user_id=body.user_id,
        identity_model_id=body.identity_model_id,
        draft_text=body.draft_text,
        platform=body.platform,
        stage_goal=body.stage_goal,
    )
    return {
        "id": evaluation.id,
        "growth_prediction_range": evaluation.growth_prediction_range,
        "controversy_prob": evaluation.controversy_prob,
        "brand_risk": evaluation.brand_risk,
        "trust_impact": evaluation.trust_impact,
        "recommendation": evaluation.recommendation,
        "trigger_factors_json": evaluation.trigger_factors_json,
        "trigger_factors": evaluation.trigger_factors,
        "rewrite": evaluation.rewrite,
        "manual_confirmation_required": evaluation.manual_confirmation_required,
    }
