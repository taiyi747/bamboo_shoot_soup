"""V1 growth experiment service."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.growth_experiment import GrowthExperiment


def create_experiment(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None,
    hypothesis: str,
    variables: list[str],
    duration: str,
    result: str = "",
    conclusion: str = "",
    next_iteration: str = "",
    status: str = "planned",
) -> GrowthExperiment:
    if not hypothesis.strip():
        raise ValueError("hypothesis is required")
    if next_iteration.strip() and not conclusion.strip():
        raise ValueError("conclusion is required before next_iteration")

    experiment = GrowthExperiment(
        user_id=user_id,
        identity_model_id=identity_model_id,
        hypothesis=hypothesis,
        variables_json=json.dumps(variables, ensure_ascii=False),
        duration=duration,
        result=result,
        conclusion=conclusion,
        next_iteration=next_iteration,
        status=status,
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


def list_experiments(db: Session, *, user_id: str) -> list[GrowthExperiment]:
    return (
        db.query(GrowthExperiment)
        .filter(GrowthExperiment.user_id == user_id)
        .order_by(GrowthExperiment.created_at.desc())
        .all()
    )


def patch_experiment(
    db: Session,
    *,
    experiment_id: str,
    result: str | None = None,
    conclusion: str | None = None,
    next_iteration: str | None = None,
    status: str | None = None,
) -> GrowthExperiment:
    experiment = db.query(GrowthExperiment).filter(GrowthExperiment.id == experiment_id).first()
    if not experiment:
        raise ValueError("experiment not found")

    if result is not None:
        experiment.result = result
    if conclusion is not None:
        experiment.conclusion = conclusion
    if next_iteration is not None:
        experiment.next_iteration = next_iteration
    if status is not None:
        experiment.status = status

    if experiment.next_iteration.strip() and not experiment.conclusion.strip():
        raise ValueError("conclusion is required before next_iteration")

    db.commit()
    db.refresh(experiment)
    return experiment
