"""人格宪法服务。"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ValidationError, model_validator
from sqlalchemy.orm import Session

from app.models.persona import PersonaConstitution, RiskBoundaryItem
from app.services.llm_client import get_llm_client, llm_schema_error


class _PersonaConstitutionOutput(BaseModel):
    """LLM 人格宪法输出结构。"""

    common_words: list[str]
    forbidden_words: list[str]
    sentence_preferences: list[str]
    moat_positions: list[str]
    narrative_mainline: str
    growth_arc_template: str

    @model_validator(mode="after")
    def validate_business_rules(self) -> "_PersonaConstitutionOutput":
        if len(self.common_words) < 3:
            raise ValueError("common_words must contain at least 3 items")
        if len(self.forbidden_words) < 3:
            raise ValueError("forbidden_words must contain at least 3 items")
        if len(self.sentence_preferences) < 3:
            raise ValueError("sentence_preferences must contain at least 3 items")
        if len(self.moat_positions) < 3:
            raise ValueError("moat_positions must contain at least 3 items")
        if not self.narrative_mainline.strip():
            raise ValueError("narrative_mainline must be non-empty")
        if not self.growth_arc_template.strip():
            raise ValueError("growth_arc_template must be non-empty")
        return self


PERSONA_CONSTITUTION_PROMPT = """
You are generating a persona constitution JSON for a creator.
Return strict JSON only with this shape:
{
  "common_words": ["string", "... at least 3 items"],
  "forbidden_words": ["string", "... at least 3 items"],
  "sentence_preferences": ["string", "... at least 3 items"],
  "moat_positions": ["string", "... at least 3 items"],
  "narrative_mainline": "string",
  "growth_arc_template": "string"
}
Hard constraints:
- no markdown
- no extra keys
- all string fields must be non-empty
""".strip()


def _parse_constitution(payload: dict[str, Any]) -> _PersonaConstitutionOutput:
    """校验 LLM 响应并转换为强类型结构。"""
    try:
        return _PersonaConstitutionOutput.model_validate(payload)
    except ValidationError as exc:
        raise llm_schema_error(
            "generate_constitution",
            f"Persona constitution schema validation failed: {exc}",
        ) from exc


def generate_constitution(
    db: Session,
    user_id: str,
    identity_model_id: str | None = None,
    common_words: list[str] | None = None,
    forbidden_words: list[str] | None = None,
) -> PersonaConstitution:
    """
    Generate persona constitution based on identity model via LLM.

    Per product-spec 2.3:
    - 口吻词典（常用词、禁用词、句式偏好）
    - 观点护城河（3条不可动摇立场）
    - 叙事主线（长期动机）
    - 成长Arc（阶段叙事模板）
    """
    # 版本号基于该用户最近一次宪法递增。
    previous = (
        db.query(PersonaConstitution)
        .filter(PersonaConstitution.user_id == user_id)
        .order_by(PersonaConstitution.version.desc())
        .first()
    )
    previous_version_id = previous.id if previous else None
    new_version = (previous.version + 1) if previous else 1

    llm_payload = {
        "user_id": user_id,
        "identity_model_id": identity_model_id,
        # 可选词汇提示，由调用方传入用于引导输出风格。
        "hint_common_words": common_words or [],
        "hint_forbidden_words": forbidden_words or [],
    }
    # 先调用 LLM，再做严格解析，最后才落库。
    response_payload = get_llm_client().generate_json(
        operation="generate_constitution",
        system_prompt=PERSONA_CONSTITUTION_PROMPT,
        user_payload=llm_payload,
    )
    output = _parse_constitution(response_payload)

    constitution = PersonaConstitution(
        user_id=user_id,
        identity_model_id=identity_model_id,
        common_words_json=json.dumps(output.common_words, ensure_ascii=False),
        forbidden_words_json=json.dumps(output.forbidden_words, ensure_ascii=False),
        sentence_preferences_json=json.dumps(output.sentence_preferences, ensure_ascii=False),
        moat_positions_json=json.dumps(output.moat_positions, ensure_ascii=False),
        narrative_mainline=output.narrative_mainline,
        growth_arc_template=output.growth_arc_template,
        version=new_version,
        previous_version_id=previous_version_id,
    )
    db.add(constitution)
    # 一次提交，保证内容与版本链同时生效。
    db.commit()
    db.refresh(constitution)
    return constitution


def get_user_constitutions(db: Session, user_id: str) -> list[PersonaConstitution]:
    """Get all persona constitutions for a user."""
    return (
        db.query(PersonaConstitution)
        .filter(PersonaConstitution.user_id == user_id)
        .order_by(PersonaConstitution.version.desc())
        .all()
    )


def get_constitution(db: Session, constitution_id: str) -> PersonaConstitution | None:
    """Get constitution by ID."""
    return db.query(PersonaConstitution).filter(PersonaConstitution.id == constitution_id).first()


def get_latest_constitution(db: Session, user_id: str) -> PersonaConstitution | None:
    """Get user's latest constitution."""
    return (
        db.query(PersonaConstitution)
        .filter(PersonaConstitution.user_id == user_id)
        .order_by(PersonaConstitution.version.desc())
        .first()
    )


def create_risk_boundary(
    db: Session,
    user_id: str,
    risk_level: int,
    boundary_type: str,
    statement: str,
    identity_model_id: str | None = None,
    constitution_id: str | None = None,
    source: str = "user_input",
) -> RiskBoundaryItem:
    """Create a risk boundary item."""
    item = RiskBoundaryItem(
        user_id=user_id,
        identity_model_id=identity_model_id,
        constitution_id=constitution_id,
        risk_level=risk_level,
        boundary_type=boundary_type,
        statement=statement,
        source=source,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_user_risk_boundaries(db: Session, user_id: str) -> list[RiskBoundaryItem]:
    """Get all risk boundaries for a user."""
    return db.query(RiskBoundaryItem).filter(RiskBoundaryItem.user_id == user_id).all()
