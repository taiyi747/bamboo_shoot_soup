"""Monetization map generation service."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ValidationError, field_validator, model_validator
from sqlalchemy.orm import Session

from app.models.identity_model import IdentityModel, IdentitySelection
from app.models.persona import PersonaConstitution
from app.models.v1_growth import MonetizationMap
from app.services.llm_client import LLMServiceError, get_llm_client, llm_schema_error
from app.services.llm_replay import generate_json_with_replay, load_latest_replay_payload


MONETIZATION_MAP_PROMPT = """
You are generating a 12-week monetization validation map for a creator.
Return strict JSON only with this shape:
{
  "primary_path": "string",
  "backup_path": "string",
  "weeks": [
    {
      "week_no": 1,
      "goal": "string",
      "task": "string",
      "deliverable": "string",
      "validation_metric": "string"
    }
  ]
}
Hard constraints:
- weeks must contain exactly 12 entries.
- week_no must be unique and cover 1..12.
- All string fields must be non-empty.
- No markdown, no prose, no extra keys.
""".strip()


class _WeekPlan(BaseModel):
    week_no: int
    goal: str
    task: str
    deliverable: str
    validation_metric: str

    @field_validator("goal", "task", "deliverable", "validation_metric")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must be non-empty")
        return value


class _MonetizationOutput(BaseModel):
    primary_path: str
    backup_path: str
    weeks: list[_WeekPlan]

    @model_validator(mode="after")
    def validate_business_rules(self) -> "_MonetizationOutput":
        if not self.primary_path.strip() or not self.backup_path.strip():
            raise ValueError("primary_path and backup_path must be non-empty")

        if len(self.weeks) != 12:
            raise ValueError("weeks must contain exactly 12 entries")

        week_numbers = sorted(item.week_no for item in self.weeks)
        if week_numbers != list(range(1, 13)):
            raise ValueError("week_no must cover 1..12 exactly")
        return self


def _parse_monetization_map(payload: dict[str, Any]) -> _MonetizationOutput:
    try:
        return _MonetizationOutput.model_validate(payload)
    except ValidationError as exc:
        raise llm_schema_error(
            "generate_monetization_map",
            f"Monetization map schema validation failed: {exc}",
        ) from exc


def _resolve_identity(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None,
) -> IdentityModel | None:
    if identity_model_id:
        model = db.query(IdentityModel).filter(IdentityModel.id == identity_model_id).first()
        if model and model.user_id == user_id:
            return model

    selection = (
        db.query(IdentitySelection)
        .filter(IdentitySelection.user_id == user_id)
        .order_by(IdentitySelection.selected_at.desc())
        .first()
    )
    if selection and selection.primary_identity_id:
        selected = (
            db.query(IdentityModel)
            .filter(
                IdentityModel.id == selection.primary_identity_id,
                IdentityModel.user_id == user_id,
            )
            .first()
        )
        if selected:
            return selected

    return (
        db.query(IdentityModel)
        .filter(IdentityModel.user_id == user_id)
        .order_by(IdentityModel.created_at.desc(), IdentityModel.id.desc())
        .first()
    )


def _resolve_constitution(
    db: Session,
    *,
    user_id: str,
    constitution_id: str | None,
    identity: IdentityModel | None,
) -> PersonaConstitution | None:
    if constitution_id:
        constitution = (
            db.query(PersonaConstitution)
            .filter(PersonaConstitution.id == constitution_id)
            .first()
        )
        if constitution and constitution.user_id == user_id:
            return constitution

    if identity:
        by_identity = (
            db.query(PersonaConstitution)
            .filter(
                PersonaConstitution.user_id == user_id,
                PersonaConstitution.identity_model_id == identity.id,
            )
            .order_by(PersonaConstitution.version.desc(), PersonaConstitution.created_at.desc())
            .first()
        )
        if by_identity:
            return by_identity

    return (
        db.query(PersonaConstitution)
        .filter(PersonaConstitution.user_id == user_id)
        .order_by(PersonaConstitution.version.desc(), PersonaConstitution.created_at.desc())
        .first()
    )


def generate_monetization_map(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None = None,
    constitution_id: str | None = None,
    hints: dict[str, Any] | None = None,
) -> tuple[MonetizationMap, bool, str | None]:
    identity = _resolve_identity(
        db,
        user_id=user_id,
        identity_model_id=identity_model_id,
    )
    constitution = _resolve_constitution(
        db,
        user_id=user_id,
        constitution_id=constitution_id,
        identity=identity,
    )

    llm_payload = {
        "user_id": user_id,
        "identity_model_id": identity.id if identity else None,
        "constitution_id": constitution.id if constitution else None,
        "identity_title": identity.title if identity else "",
        "differentiation": identity.differentiation if identity else "",
        "narrative_mainline": constitution.narrative_mainline if constitution else "",
        "hints": hints or {},
    }

    replay_result = generate_json_with_replay(
        db,
        user_id=user_id,
        operation="generate_monetization_map",
        system_prompt=MONETIZATION_MAP_PROMPT,
        user_payload=llm_payload,
        llm_client=get_llm_client(),
    )

    try:
        output = _parse_monetization_map(replay_result.payload)
    except LLMServiceError as error:
        if error.code != "LLM_SCHEMA_VALIDATION_FAILED":
            raise
        fallback_payload = load_latest_replay_payload(
            db,
            user_id=user_id,
            operation="generate_monetization_map",
        )
        if fallback_payload is None:
            raise
        output = _parse_monetization_map(fallback_payload)
        replay_result.degraded = True
        replay_result.degrade_reason = "replay_fallback"

    map_entity = MonetizationMap(
        user_id=user_id,
        identity_model_id=identity.id if identity else None,
        constitution_id=constitution.id if constitution else None,
        primary_path=output.primary_path,
        backup_path=output.backup_path,
        weeks_json=json.dumps([item.model_dump() for item in output.weeks], ensure_ascii=False),
    )
    db.add(map_entity)
    db.commit()
    db.refresh(map_entity)
    return map_entity, replay_result.degraded, replay_result.degrade_reason


def get_user_monetization_maps(db: Session, user_id: str) -> list[MonetizationMap]:
    return (
        db.query(MonetizationMap)
        .filter(MonetizationMap.user_id == user_id)
        .order_by(MonetizationMap.created_at.desc())
        .all()
    )


def get_monetization_map(db: Session, map_id: str) -> MonetizationMap | None:
    return db.query(MonetizationMap).filter(MonetizationMap.id == map_id).first()
