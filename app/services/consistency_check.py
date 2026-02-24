"""一致性检查服务。"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import Any

from pydantic import BaseModel, ValidationError, model_validator
from sqlalchemy.orm import Session

from app.models.consistency_check import ConsistencyCheck
from app.services.llm_client import LLMServiceError, get_llm_client, llm_schema_error

logger = logging.getLogger(__name__)

SCHEMA_REPAIR_MAX_RETRIES = 2
DEGRADE_REASON_SCHEMA_RETRY_EXHAUSTED = "llm_schema_retry_exhausted"


@dataclass
class ConsistencyCheckExecutionResult:
    check: ConsistencyCheck
    degraded: bool
    degrade_reason: str | None
    schema_repair_attempts: int


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
- deviation_items must contain at least 1 non-empty string
- deviation_reasons must contain at least 1 non-empty string
- suggestions must contain at least 1 non-empty string
- if risk_triggered is true, risk_warning must be non-empty
- if there is no clear deviation, still return one placeholder item:
  - deviation_items: ["未发现明显偏离（建议人工复核）"]
  - deviation_reasons: ["当前草稿未发现明显偏离项，建议人工复核语境和事实边界。"]
  - suggestions: ["按当前方向继续优化表达，发布前做一次人工校对。"]
- no markdown
- no extra keys
- use chinese for all text
""".strip()

CONSISTENCY_CHECK_REPAIR_PROMPT = """
You are repairing an invalid JSON object for consistency check output.
Return strict JSON only with this shape:
{
  "deviation_items": ["string", "... at least 1 item"],
  "deviation_reasons": ["string", "... at least 1 item"],
  "suggestions": ["string", "... at least 1 item"],
  "risk_triggered": true,
  "risk_warning": "string"
}
Hard constraints:
- must keep exactly these keys and no extra keys
- all three arrays must contain at least 1 non-empty string
- if risk_triggered is true, risk_warning must be non-empty
- if no clear deviation, use placeholder values:
  - deviation_items: ["未发现明显偏离（建议人工复核）"]
  - deviation_reasons: ["当前草稿未发现明显偏离项，建议人工复核语境和事实边界。"]
  - suggestions: ["按当前方向继续优化表达，发布前做一次人工校对。"]
- use chinese for all text
- no markdown
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


def _validation_error_brief(error_message: str) -> str:
    first_line = error_message.splitlines()[0] if error_message else "unknown"
    return first_line[:200]


def _build_degraded_output() -> _ConsistencyCheckOutput:
    return _ConsistencyCheckOutput(
        deviation_items=["未发现明显偏离（建议人工复核）"],
        deviation_reasons=["LLM 结构化输出不稳定，已使用降级结果，请人工复核。"],
        suggestions=["请人工复核草稿后再发布。"],
        risk_triggered=False,
        risk_warning="",
    )


def _generate_consistency_output(
    *,
    llm_payload: dict[str, Any],
) -> tuple[_ConsistencyCheckOutput, bool, str | None, int]:
    llm_client = get_llm_client()
    response_payload = llm_client.generate_json(
        operation="check_consistency",
        system_prompt=CONSISTENCY_CHECK_PROMPT,
        user_payload=llm_payload,
    )

    try:
        return _parse_consistency_output(response_payload), False, None, 0
    except LLMServiceError as exc:
        if exc.code != "LLM_SCHEMA_VALIDATION_FAILED":
            raise
        last_error = exc

    last_payload = response_payload
    for attempt in range(1, SCHEMA_REPAIR_MAX_RETRIES + 1):
        logger.warning(
            "schema_retry operation=check_consistency schema_retry_attempt=%s validation_error_brief=%s degraded=%s",
            attempt,
            _validation_error_brief(last_error.message),
            False,
        )

        repair_payload = {
            "original_user_payload": llm_payload,
            "previous_invalid_response": last_payload,
            "validation_error": last_error.message,
        }
        repaired_payload = llm_client.generate_json(
            operation="check_consistency",
            system_prompt=CONSISTENCY_CHECK_REPAIR_PROMPT,
            user_payload=repair_payload,
        )
        try:
            output = _parse_consistency_output(repaired_payload)
            return output, False, None, attempt
        except LLMServiceError as exc:
            if exc.code != "LLM_SCHEMA_VALIDATION_FAILED":
                raise
            last_error = exc
            last_payload = repaired_payload

    logger.warning(
        "schema_retry operation=check_consistency schema_retry_attempt=%s validation_error_brief=%s degraded=%s",
        SCHEMA_REPAIR_MAX_RETRIES,
        _validation_error_brief(last_error.message),
        True,
    )
    return (
        _build_degraded_output(),
        True,
        DEGRADE_REASON_SCHEMA_RETRY_EXHAUSTED,
        SCHEMA_REPAIR_MAX_RETRIES,
    )


def check_consistency(
    db: Session,
    user_id: str,
    draft_text: str,
    identity_model_id: str | None = None,
    constitution_id: str | None = None,
) -> ConsistencyCheckExecutionResult:
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
    output, degraded, degrade_reason, schema_repair_attempts = _generate_consistency_output(
        llm_payload=llm_payload
    )

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
    return ConsistencyCheckExecutionResult(
        check=check,
        degraded=degraded,
        degrade_reason=degrade_reason,
        schema_repair_attempts=schema_repair_attempts,
    )


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
