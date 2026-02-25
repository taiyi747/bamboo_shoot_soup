"""Identity model service."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ValidationError, model_validator
from sqlalchemy.orm import Session

from app.models.consistency_check import ConsistencyCheck
from app.models.identity_model import IdentityModel, IdentitySelection
from app.models.launch_kit import LaunchKit
from app.models.persona import PersonaConstitution, RiskBoundaryItem
from app.services.llm_client import LLMServiceError, get_llm_client, llm_schema_error
from app.services.llm_replay import generate_json_with_replay, load_latest_replay_payload


class _IdentityCandidate(BaseModel):
    """Single identity candidate returned by LLM."""

    title: str
    target_audience_pain: str
    content_pillars: list[str]
    tone_keywords: list[str]
    tone_examples: list[str]
    long_term_views: list[str]
    differentiation: str
    growth_path_0_3m: str
    growth_path_3_12m: str
    monetization_validation_order: list[str]
    risk_boundary: list[str]

    @model_validator(mode="after")
    def validate_business_rules(self) -> "_IdentityCandidate":
        if not self.title.strip():
            raise ValueError("title must be non-empty")
        if not self.target_audience_pain.strip():
            raise ValueError("target_audience_pain must be non-empty")
        if not self.differentiation.strip():
            raise ValueError("differentiation must be non-empty")
        if len(self.content_pillars) < 3 or len(self.content_pillars) > 5:
            raise ValueError("content_pillars must contain 3-5 items")
        if len(self.tone_examples) < 5:
            raise ValueError("tone_examples must contain at least 5 sentences")
        if len(self.long_term_views) < 5 or len(self.long_term_views) > 10:
            raise ValueError("long_term_views must contain 5-10 items")
        if len(self.monetization_validation_order) < 1:
            raise ValueError("monetization_validation_order must contain at least 1 step")
        return self


class _IdentityGenerationResponse(BaseModel):
    """Top-level response shape for identity generation."""

    models: list[_IdentityCandidate]


IDENTITY_MODELS_PROMPT = """
You are generating identity model cards for a creator product.
Each request should be handled independently. Do not assume access to previous or future requests.
Return strict JSON only with this shape:
{
  "models": [
    {
      "title": "string",
      "target_audience_pain": "string",
      "content_pillars": ["string", "... 3-5 items"],
      "tone_keywords": ["string", "..."],
      "tone_examples": ["string", "... at least 5 items"],
      "long_term_views": ["string", "... 5-10 items"],
      "differentiation": "string",
      "growth_path_0_3m": "string",
      "growth_path_3_12m": "string",
      "monetization_validation_order": ["string", "... at least 1 item"],
      "risk_boundary": ["string", "..."]
    }
  ]
}
Hard constraints:
- model count must exactly equal requested count.
- when requested count is 1, return exactly one model.
- differentiation must be non-empty.
- tone_examples must contain at least 5 entries.
- long_term_views must contain 5-10 entries.
- risk_boundary must be a JSON array of non-empty strings, never a plain string.
- if only one risk boundary is generated, still return it as an array with one item.
- no markdown, no prose, no extra keys.
- self-check before returning:
  - every models[i].risk_boundary is an array type
  - every item in models[i].risk_boundary is a non-empty string
""".strip()


def _parse_identity_models(payload: dict[str, Any], count: int) -> list[_IdentityCandidate]:
    """Validate LLM response schema and model count."""

    try:
        result = _IdentityGenerationResponse.model_validate(payload)
    except ValidationError as exc:
        raise llm_schema_error(
            "generate_identity_models",
            f"Identity model response schema validation failed: {exc}",
        ) from exc

    if len(result.models) != count:
        raise llm_schema_error(
            "generate_identity_models",
            f"Expected {count} models but got {len(result.models)}.",
        )
    return result.models


def _generate_identity_candidates_parallel(
    *,
    db: Session,
    user_id: str,
    count: int,
    llm_payload: dict[str, Any],
) -> list[_IdentityCandidate]:
    """Generate candidates one-by-one to keep replay fallback deterministic."""

    def _generate_one(_index: int) -> _IdentityCandidate:
        payload = dict(llm_payload)
        payload["count"] = 1
        replay_result = generate_json_with_replay(
            db,
            user_id=user_id,
            operation="generate_identity_models",
            system_prompt=IDENTITY_MODELS_PROMPT,
            user_payload=payload,
            llm_client=get_llm_client(),
        )
        try:
            candidates = _parse_identity_models(replay_result.payload, count=1)
        except LLMServiceError as error:
            if error.code != "LLM_SCHEMA_VALIDATION_FAILED":
                raise
            fallback_payload = load_latest_replay_payload(
                db,
                user_id=user_id,
                operation="generate_identity_models",
            )
            if fallback_payload is None:
                raise
            candidates = _parse_identity_models(fallback_payload, count=1)
        return candidates[0]

    return [_generate_one(index) for index in range(count)]


def _replace_user_identity_models(db: Session, user_id: str) -> None:
    """Replace all identity models for a user and unlink old downstream references."""

    existing_model_ids = [
        model_id
        for (model_id,) in db.query(IdentityModel.id).filter(IdentityModel.user_id == user_id).all()
    ]
    if not existing_model_ids:
        return

    db.query(IdentitySelection).filter(IdentitySelection.user_id == user_id).delete(
        synchronize_session=False
    )

    db.query(PersonaConstitution).filter(
        PersonaConstitution.identity_model_id.in_(existing_model_ids)
    ).update({PersonaConstitution.identity_model_id: None}, synchronize_session=False)

    db.query(RiskBoundaryItem).filter(
        RiskBoundaryItem.identity_model_id.in_(existing_model_ids)
    ).update(
        {RiskBoundaryItem.identity_model_id: None},
        synchronize_session=False,
    )

    db.query(LaunchKit).filter(LaunchKit.identity_model_id.in_(existing_model_ids)).update(
        {LaunchKit.identity_model_id: None},
        synchronize_session=False,
    )

    db.query(ConsistencyCheck).filter(
        ConsistencyCheck.identity_model_id.in_(existing_model_ids)
    ).update(
        {ConsistencyCheck.identity_model_id: None},
        synchronize_session=False,
    )

    db.query(IdentityModel).filter(IdentityModel.id.in_(existing_model_ids)).delete(
        synchronize_session=False
    )


def generate_identity_models(
    db: Session,
    user_id: str,
    session_id: str | None,
    capability_profile: dict,
    count: int = 3,
) -> list[IdentityModel]:
    """Generate identity models and replace previous batch atomically."""

    llm_payload = {
        "user_id": user_id,
        "session_id": session_id,
        "count": count,
        "capability_profile": capability_profile,
    }

    candidates = _generate_identity_candidates_parallel(
        db=db,
        user_id=user_id,
        count=count,
        llm_payload=llm_payload,
    )
    _replace_user_identity_models(db, user_id)

    models: list[IdentityModel] = []
    for candidate in candidates:
        model = IdentityModel(
            user_id=user_id,
            session_id=session_id,
            title=candidate.title,
            target_audience_pain=candidate.target_audience_pain,
            content_pillars_json=json.dumps(candidate.content_pillars, ensure_ascii=False),
            tone_keywords_json=json.dumps(candidate.tone_keywords, ensure_ascii=False),
            tone_examples_json=json.dumps(candidate.tone_examples, ensure_ascii=False),
            long_term_views_json=json.dumps(candidate.long_term_views, ensure_ascii=False),
            differentiation=candidate.differentiation,
            growth_path_0_3m=candidate.growth_path_0_3m,
            growth_path_3_12m=candidate.growth_path_3_12m,
            monetization_validation_order_json=json.dumps(
                candidate.monetization_validation_order,
                ensure_ascii=False,
            ),
            risk_boundary_json=json.dumps(candidate.risk_boundary, ensure_ascii=False),
        )
        db.add(model)
        models.append(model)

    db.commit()
    for model in models:
        db.refresh(model)
    return models


def select_identity(
    db: Session,
    user_id: str,
    primary_identity_id: str,
    backup_identity_id: str | None = None,
) -> IdentitySelection:
    """Save user's primary and backup identity selection."""

    if backup_identity_id and primary_identity_id == backup_identity_id:
        raise ValueError("backup_identity_id must be different from primary_identity_id")

    primary = db.query(IdentityModel).filter(IdentityModel.id == primary_identity_id).first()
    if not primary:
        raise ValueError(f"Identity {primary_identity_id} not found")

    if backup_identity_id:
        backup = db.query(IdentityModel).filter(IdentityModel.id == backup_identity_id).first()
        if not backup:
            raise ValueError(f"Identity {backup_identity_id} not found")

    db.query(IdentityModel).filter(
        IdentityModel.user_id == user_id,
        (IdentityModel.is_primary == True) | (IdentityModel.is_backup == True),
    ).update({"is_primary": False, "is_backup": False})

    primary.is_primary = True
    if backup_identity_id:
        backup = db.query(IdentityModel).filter(IdentityModel.id == backup_identity_id).first()
        backup.is_backup = True

    selection = IdentitySelection(
        user_id=user_id,
        primary_identity_id=primary_identity_id,
        backup_identity_id=backup_identity_id,
    )
    db.add(selection)
    db.commit()
    db.refresh(selection)
    return selection


def get_user_identity_models(db: Session, user_id: str) -> list[IdentityModel]:
    """Get all identity models for a user."""

    return (
        db.query(IdentityModel)
        .filter(IdentityModel.user_id == user_id)
        .order_by(IdentityModel.created_at.asc(), IdentityModel.id.asc())
        .all()
    )


def get_identity_model(db: Session, model_id: str) -> IdentityModel | None:
    """Get identity model by ID."""

    return db.query(IdentityModel).filter(IdentityModel.id == model_id).first()


def get_user_selection(db: Session, user_id: str) -> IdentitySelection | None:
    """Get user's current identity selection."""

    return (
        db.query(IdentitySelection)
        .filter(IdentitySelection.user_id == user_id)
        .order_by(IdentitySelection.selected_at.desc())
        .first()
    )
