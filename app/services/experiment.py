"""Growth experiment service."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.v1_growth import Experiment


def create_experiment(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None,
    hypothesis: str,
    variables: list[str],
    execution_cycle: str,
) -> Experiment:
    clean_variables = [item.strip() for item in variables if item.strip()]
    if not clean_variables:
        raise ValueError("variables must contain at least one item")

    experiment = Experiment(
        user_id=user_id,
        identity_model_id=identity_model_id,
        hypothesis=hypothesis.strip(),
        variables_json=json.dumps(clean_variables, ensure_ascii=False),
        execution_cycle=execution_cycle.strip(),
        status="planned",
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


def update_experiment_result(
    db: Session,
    *,
    experiment_id: str,
    result: str,
    conclusion: str,
) -> Experiment:
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise ValueError("Experiment not found")

    if not result.strip() or not conclusion.strip():
        raise ValueError("result and conclusion must be non-empty")

    experiment.result = result.strip()
    experiment.conclusion = conclusion.strip()
    experiment.status = "completed"
    db.commit()
    db.refresh(experiment)
    return experiment


def get_user_experiments(db: Session, user_id: str) -> list[Experiment]:
    return (
        db.query(Experiment)
        .filter(Experiment.user_id == user_id)
        .order_by(Experiment.created_at.desc())
        .all()
    )
