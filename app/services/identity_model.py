"""身份模型服务。"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ValidationError, model_validator
from sqlalchemy.orm import Session

from app.models.identity_model import IdentityModel, IdentitySelection
from app.services.llm_client import get_llm_client, llm_schema_error


class _IdentityCandidate(BaseModel):
    """LLM 返回的单个身份候选结构。"""

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
    """身份生成服务期望的顶层响应结构。"""

    models: list[_IdentityCandidate]


IDENTITY_MODELS_PROMPT = """
You are generating identity model cards for a creator product.
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
    """校验 LLM 响应并强制候选数量与请求一致。"""
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


def generate_identity_models(
    db: Session,
    user_id: str,
    session_id: str | None,
    capability_profile: dict,
    count: int = 3,
) -> list[IdentityModel]:
    """
    # 任务：生成人格模型

    **任务目标：**
    请生成 3-5 个不同的**人格模型（Identity Models）**。

    **输出要求：**
    所有生成的内容必须使用**中文**，且每个模型必须严格遵守产品说明书 2.6 的业务规则：

    1. **差异化定位 (Differentiation)**：必须提供明确的定位说明，内容不得为空。
    2. **语气示例 (Tone Examples)**：必须提供至少 5 句代表该人格说话风格的例句。
    3. **长期愿景 (Long-term Views)**：必须列出 5-10 项具体的长期观点或发展目标。
    4. **变现验证流程 (Monetization Validation Order)**：必须包含至少 1 个具体的变现验证步骤。

    **输出格式：**
    请使用清晰的 Markdown 结构（标题、列表等）输出每一个模型的信息。
    """
    llm_payload = {
        "user_id": user_id,
        "session_id": session_id,
        "count": count,
        "capability_profile": capability_profile,
    }

    # 第一步：向 LLM 请求严格 JSON 输出。
    response_payload = get_llm_client().generate_json(
        operation="generate_identity_models",
        system_prompt=IDENTITY_MODELS_PROMPT,
        user_payload=llm_payload,
    )
    # 第二步：先做 schema/业务规则校验，再进入落库。
    candidates = _parse_identity_models(response_payload, count=count)

    # 第三步：将校验后的结构映射到 ORM 模型。
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

    # 所有候选都通过校验后再一次性提交事务。
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
    # 业务约束：主备身份不能相同。
    if backup_identity_id and primary_identity_id == backup_identity_id:
        raise ValueError("backup_identity_id must be different from primary_identity_id")

    # 先确保被选身份存在，再执行状态更新。
    primary = db.query(IdentityModel).filter(IdentityModel.id == primary_identity_id).first()
    if not primary:
        raise ValueError(f"Identity {primary_identity_id} not found")

    if backup_identity_id:
        backup = db.query(IdentityModel).filter(IdentityModel.id == backup_identity_id).first()
        if not backup:
            raise ValueError(f"Identity {backup_identity_id} not found")

    # 清理旧标记，保证每个用户仅有一组主备标识。
    db.query(IdentityModel).filter(
        IdentityModel.user_id == user_id,
        (IdentityModel.is_primary == True) | (IdentityModel.is_backup == True),
    ).update({"is_primary": False, "is_backup": False})

    primary.is_primary = True
    if backup_identity_id:
        backup = db.query(IdentityModel).filter(IdentityModel.id == backup_identity_id).first()
        backup.is_backup = True

    # 除字段标记外，保留一条选择历史记录用于追踪。
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
    return db.query(IdentityModel).filter(IdentityModel.user_id == user_id).all()


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
