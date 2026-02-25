"""Experiment API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.experiment import ExperimentCreate, ExperimentResponse, ExperimentResultUpdate
from app.services import experiment as experiment_service
from app.services.event_log import log_event

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=dict)
def create_experiment(
    body: ExperimentCreate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        experiment = experiment_service.create_experiment(
            db,
            user_id=body.user_id,
            identity_model_id=body.identity_model_id,
            hypothesis=body.hypothesis,
            variables=body.variables,
            execution_cycle=body.execution_cycle,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    log_event(
        db,
        user_id=body.user_id,
        event_name="experiment_created",
        stage="V1",
        identity_model_id=body.identity_model_id,
        payload={"experiment_id": experiment.id},
    )

    return {
        "id": experiment.id,
        "status": experiment.status,
        "created_at": experiment.created_at.isoformat(),
    }


@router.patch("/{experiment_id}/result", response_model=dict)
def update_experiment_result(
    experiment_id: str,
    body: ExperimentResultUpdate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        experiment = experiment_service.update_experiment_result(
            db,
            experiment_id=experiment_id,
            result=body.result,
            conclusion=body.conclusion,
        )
    except ValueError as error:
        status_code = 404 if "not found" in str(error).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(error)) from error

    return {
        "id": experiment.id,
        "status": experiment.status,
        "result": experiment.result,
        "conclusion": experiment.conclusion,
    }


@router.get("/users/{user_id}", response_model=list[ExperimentResponse])
def get_user_experiments(
    user_id: str,
    db: Session = Depends(get_db),
) -> list[ExperimentResponse]:
    return experiment_service.get_user_experiments(db, user_id)
