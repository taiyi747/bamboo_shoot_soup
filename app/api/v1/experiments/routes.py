"""V1 growth experiment API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import experiment as experiment_service
from app.services.event_log import log_event

router = APIRouter(prefix="/experiments", tags=["experiments"])


class ExperimentCreateRequest(BaseModel):
    user_id: str
    identity_model_id: str | None = None
    hypothesis: str
    variables: list[str] = Field(default_factory=list)
    duration: str = ""
    result: str = ""
    conclusion: str = ""
    next_iteration: str = ""
    status: str = "planned"


class ExperimentPatchRequest(BaseModel):
    result: str | None = None
    conclusion: str | None = None
    next_iteration: str | None = None
    status: str | None = None


@router.post("", response_model=dict)
def create_experiment(
    body: ExperimentCreateRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        experiment = experiment_service.create_experiment(
            db=db,
            user_id=body.user_id,
            identity_model_id=body.identity_model_id,
            hypothesis=body.hypothesis,
            variables=body.variables,
            duration=body.duration,
            result=body.result,
            conclusion=body.conclusion,
            next_iteration=body.next_iteration,
            status=body.status,
        )
        log_event(
            db=db,
            user_id=body.user_id,
            event_name="experiment_created",
            stage="V1",
            identity_model_id=body.identity_model_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "id": experiment.id,
        "hypothesis": experiment.hypothesis,
        "variables_json": experiment.variables_json,
        "variables": experiment.variables,
        "duration": experiment.duration,
        "result": experiment.result,
        "conclusion": experiment.conclusion,
        "next_iteration": experiment.next_iteration,
        "status": experiment.status,
    }


@router.get("", response_model=list[dict])
def list_experiments(
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    experiments = experiment_service.list_experiments(db=db, user_id=user_id)
    return [
        {
            "id": experiment.id,
            "hypothesis": experiment.hypothesis,
            "variables_json": experiment.variables_json,
            "variables": experiment.variables,
            "duration": experiment.duration,
            "result": experiment.result,
            "conclusion": experiment.conclusion,
            "next_iteration": experiment.next_iteration,
            "status": experiment.status,
            "created_at": experiment.created_at.isoformat(),
        }
        for experiment in experiments
    ]


@router.patch("/{experiment_id}", response_model=dict)
def patch_experiment(
    experiment_id: str,
    body: ExperimentPatchRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        experiment = experiment_service.patch_experiment(
            db=db,
            experiment_id=experiment_id,
            result=body.result,
            conclusion=body.conclusion,
            next_iteration=body.next_iteration,
            status=body.status,
        )
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    return {
        "id": experiment.id,
        "result": experiment.result,
        "conclusion": experiment.conclusion,
        "next_iteration": experiment.next_iteration,
        "status": experiment.status,
    }
