"""Content matrix generation service."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ValidationError, model_validator
from sqlalchemy.orm import Session

from app.models.identity_model import IdentityModel, IdentitySelection
from app.models.persona import PersonaConstitution
from app.models.v1_growth import ContentMatrix
from app.services.llm_client import LLMServiceError, get_llm_client, llm_schema_error
from app.services.llm_replay import generate_json_with_replay, load_latest_replay_payload


CONTENT_MATRIX_PROMPT = """
You are generating a creator content matrix.
Return strict JSON only with this shape:
{
  "pillars": [
    {
      "pillar": "string",
      "topics": ["string", "... 20-50 items"],
      "platform_rewrites": {
        "xiaohongshu": ["string", "..."],
        "wechat": ["string", "..."],
        "video_channel": ["string", "..."]
      }
    }
  ]
}
Hard constraints:
- Return 3-5 pillars.
- Each pillar topics length must be 20-50.
- platform_rewrites must include at least 3 platform keys.
- No markdown, no prose, no extra keys.
""".strip()


class _PillarMatrix(BaseModel):
    pillar: str
    topics: list[str]
    platform_rewrites: dict[str, list[str]]

    @model_validator(mode="after")
    def validate_business_rules(self) -> "_PillarMatrix":
        if not self.pillar.strip():
            raise ValueError("pillar must be non-empty")
        clean_topics = [item.strip() for item in self.topics if item.strip()]
        if len(clean_topics) < 20 or len(clean_topics) > 50:
            raise ValueError("topics must contain 20-50 items")

        if len(self.platform_rewrites.keys()) < 3:
            raise ValueError("platform_rewrites must contain at least 3 platforms")
        for platform, items in self.platform_rewrites.items():
            if not platform.strip():
                raise ValueError("platform key must be non-empty")
            clean_items = [item.strip() for item in items if item.strip()]
            if len(clean_items) < 1:
                raise ValueError("platform rewrite list must contain at least 1 item")
        return self


class _ContentMatrixOutput(BaseModel):
    pillars: list[_PillarMatrix]

    @model_validator(mode="after")
    def validate_business_rules(self) -> "_ContentMatrixOutput":
        if len(self.pillars) < 3 or len(self.pillars) > 5:
            raise ValueError("pillars must contain 3-5 items")
        return self


def _parse_content_matrix(payload: dict[str, Any]) -> _ContentMatrixOutput:
    try:
        return _ContentMatrixOutput.model_validate(payload)
    except ValidationError as exc:
        raise llm_schema_error(
            "generate_content_matrix",
            f"Content matrix schema validation failed: {exc}",
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
        model = (
            db.query(IdentityModel)
            .filter(
                IdentityModel.id == selection.primary_identity_id,
                IdentityModel.user_id == user_id,
            )
            .first()
        )
        if model:
            return model

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


def _to_context(identity: IdentityModel | None, constitution: PersonaConstitution | None) -> dict[str, Any]:
    context: dict[str, Any] = {
        "identity": None,
        "constitution": None,
    }
    if identity:
        try:
            pillars = json.loads(identity.content_pillars_json)
        except (TypeError, json.JSONDecodeError):
            pillars = []
        context["identity"] = {
            "id": identity.id,
            "title": identity.title,
            "target_audience_pain": identity.target_audience_pain,
            "content_pillars": pillars if isinstance(pillars, list) else [],
            "differentiation": identity.differentiation,
        }

    if constitution:
        try:
            sentence_preferences = json.loads(constitution.sentence_preferences_json)
        except (TypeError, json.JSONDecodeError):
            sentence_preferences = []
        context["constitution"] = {
            "id": constitution.id,
            "narrative_mainline": constitution.narrative_mainline,
            "sentence_preferences": (
                sentence_preferences if isinstance(sentence_preferences, list) else []
            ),
        }

    return context


def generate_content_matrix(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None = None,
    constitution_id: str | None = None,
    hints: dict[str, Any] | None = None,
) -> tuple[ContentMatrix, bool, str | None]:
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
        "context": _to_context(identity, constitution),
        "hints": hints or {},
    }

    replay_result = generate_json_with_replay(
        db,
        user_id=user_id,
        operation="generate_content_matrix",
        system_prompt=CONTENT_MATRIX_PROMPT,
        user_payload=llm_payload,
        llm_client=get_llm_client(),
    )

    try:
        output = _parse_content_matrix(replay_result.payload)
    except LLMServiceError as error:
        if error.code != "LLM_SCHEMA_VALIDATION_FAILED":
            raise
        fallback_payload = load_latest_replay_payload(
            db,
            user_id=user_id,
            operation="generate_content_matrix",
        )
        if fallback_payload is None:
            raise
        output = _parse_content_matrix(fallback_payload)
        replay_result.degraded = True
        replay_result.degrade_reason = "replay_fallback"

    pillars = [item.pillar for item in output.pillars]
    matrix = [item.model_dump() for item in output.pillars]

    entity = ContentMatrix(
        user_id=user_id,
        identity_model_id=identity.id if identity else None,
        constitution_id=constitution.id if constitution else None,
        content_pillars_json=json.dumps(pillars, ensure_ascii=False),
        matrix_json=json.dumps(matrix, ensure_ascii=False),
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity, replay_result.degraded, replay_result.degrade_reason


def get_user_content_matrices(db: Session, user_id: str) -> list[ContentMatrix]:
    return (
        db.query(ContentMatrix)
        .filter(ContentMatrix.user_id == user_id)
        .order_by(ContentMatrix.created_at.desc())
        .all()
    )


def get_content_matrix(db: Session, matrix_id: str) -> ContentMatrix | None:
    return db.query(ContentMatrix).filter(ContentMatrix.id == matrix_id).first()
