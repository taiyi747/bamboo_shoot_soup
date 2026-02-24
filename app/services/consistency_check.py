"""一致性检查服务。"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ValidationError, model_validator
from sqlalchemy.orm import Session

from app.models.consistency_check import ConsistencyCheck
from app.services.llm_client import get_llm_client, llm_schema_error


class _ConsistencyCheckOutput(BaseModel):
    """一致性检查的 LLM 输出结构。"""

    deviation_items: list[str]
    deviation_reasons: list[str]
    suggestions: list[str]
    risk_triggered: bool
    risk_warning: str = ""

    @model_validator(mode="after")
    def validate_business_rules(self) -> "_ConsistencyCheckOutput":
        if len(self.deviation_items) < 1:
            raise ValueError("deviation_items must contain at least 1 item")
        if len(self.deviation_reasons) < 1:
            raise ValueError("deviation_reasons must contain at least 1 item")
        if len(self.suggestions) < 1:
            raise ValueError("suggestions must contain at least 1 item")
        if self.risk_triggered and not self.risk_warning.strip():
            raise ValueError("risk_warning is required when risk_triggered is true")
        return self


CONSISTENCY_CHECK_PROMPT = """

You are evaluating content consistency against persona and identity constraints.
Return strict JSON only with this shape:
{
  "deviation_items": ["string", "... at least 1 item"],
  "deviation_reasons": ["string", "... at least 1 item"],
  "suggestions": ["string", "... at least 1 item"],
  "risk_triggered": true,
  "risk_warning": "string"
}
Hard constraints:
- if risk_triggered is true, risk_warning must be non-empty
- no markdown
- no extra keys
- use chinese for all text
""".strip()


def _parse_consistency_output(payload: dict[str, Any]) -> _ConsistencyCheckOutput:
    """落库前校验一致性检查输出。"""
    try:
        return _ConsistencyCheckOutput.model_validate(payload)
    except ValidationError as exc:
        raise llm_schema_error(
            "check_consistency",
            f"Consistency check schema validation failed: {exc}",
        ) from exc


def check_consistency(
    db: Session,
    user_id: str,
    draft_text: str,
    identity_model_id: str | None = None,
    constitution_id: str | None = None,
) -> ConsistencyCheck:
    """
    Check draft consistency against persona constitution via LLM.
    Per product-spec 2.6:
    - 输出必须包含：偏离项、偏离原因、修改建议
    - 若触发风险边界，必须给出明确提醒
    """
    llm_payload = {
        "user_id": user_id,
        "identity_model_id": identity_model_id,
        "constitution_id": constitution_id,
        "draft_text": draft_text,
    }
    # 先生成并校验，再进入数据库写入。
    response_payload = get_llm_client().generate_json(
        operation="check_consistency",
        system_prompt=CONSISTENCY_CHECK_PROMPT,
        user_payload=llm_payload,
    )
    output = _parse_consistency_output(response_payload)

    check = ConsistencyCheck(
        user_id=user_id,
        identity_model_id=identity_model_id,
        constitution_id=constitution_id,
        draft_text=draft_text,
        deviation_items_json=json.dumps(output.deviation_items, ensure_ascii=False),
        deviation_reasons_json=json.dumps(output.deviation_reasons, ensure_ascii=False),
        suggestions_json=json.dumps(output.suggestions, ensure_ascii=False),
        risk_triggered=output.risk_triggered,
        risk_warning=output.risk_warning,
    )
    db.add(check)
    # 以单事务写入检查结果，避免部分成功。
    db.commit()
    db.refresh(check)
    return check


def get_user_checks(db: Session, user_id: str) -> list[ConsistencyCheck]:
    """Get all consistency checks for a user."""
    return (
        db.query(ConsistencyCheck)
        .filter(ConsistencyCheck.user_id == user_id)
        .order_by(ConsistencyCheck.created_at.desc())
        .all()
    )


def get_check(db: Session, check_id: str) -> ConsistencyCheck | None:
    """Get consistency check by ID."""
    return db.query(ConsistencyCheck).filter(ConsistencyCheck.id == check_id).first()
