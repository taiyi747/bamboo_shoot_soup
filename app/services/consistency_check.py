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
from app.services.llm_observability import generate_json_with_observability

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
你正在修复一个用于一致性检查（consistency check）的无效 JSON 对象。
请直接返回纯文本，且仅返回严格符合以下数据结构的 JSON（Return strict JSON only with this shape）：
{
  "deviation_items": ["string", "...至少 1 个元素"],
  "deviation_reasons": ["string", "...至少 1 个元素"],
  "suggestions": ["string", "...至少 1 个元素"],
  "risk_triggered": boolean,
  "risk_warning": "string"
}

强制约束条件（Hard constraints）：
- 【结构锁定】必须完全保留上述指定的 Keys，绝对禁止添加任何额外的 Keys。
- 【数组约束】所有三个数组（deviation_items, deviation_reasons, suggestions）必须包含至少 1 个非空字符串。
- 【逻辑联动】如果 `risk_triggered` 为 true，则 `risk_warning` 必须提供非空字符串。
- 【默认兜底】如果没有发现明显的偏离项（no clear deviation），必须严格使用以下默认占位符：
  - "deviation_items": ["未发现明显偏离（建议人工复核）"]
  - "deviation_reasons": ["当前草稿未发现明显偏离项，建议人工复核语境和事实边界。"]
  - "suggestions": ["按当前方向继续优化表达，发布前做一次人工校对。"]
- 【语言要求】输出的 JSON Values 文本内容必须全部使用中文。
- 【格式限制】不要输出任何 Markdown 格式符号（严禁使用 ```json 和 ``` 标签包裹内容），直接输出纯 JSON 字符串。
""".strip()

CONSISTENCY_CHECK_REPAIR_PROMPT = """
你正在执行 consistency check（一致性检查）结果的修复任务，需将无效对象转换为格式合规的 JSON。

【Output Requirement】
Return strictly RAW JSON ONLY with the exact shape below:
{
  "deviation_items": ["string", "...at least 1 item"],
  "deviation_reasons": ["string", "...at least 1 item"],
  "suggestions": ["string", "...at least 1 item"],
  "risk_triggered": boolean,
  "risk_warning": "string"
}

【Hard Constraints】
1. [Schema 锁定]：必须且仅保留上述指定的 keys，严禁添加任何额外字段 (no extra keys)。
2. [数组校验]：`deviation_items`、`deviation_reasons` 和 `suggestions` 这三个数组必须包含至少 1 个非空字符串。
3. [风险联动]：当 `risk_triggered` 为 true 时，`risk_warning` 必须为非空字符串。
4. [兜底占位符]：若未发现明显偏离 (if no clear deviation)，必须严格使用以下默认值：
   - "deviation_items": ["未发现明显偏离（建议人工复核）"]
   - "deviation_reasons": ["当前草稿未发现明显偏离项，建议人工复核语境和事实边界。"]
   - "suggestions": ["按当前方向继续优化表达，发布前做一次人工校对。"]
   - "risk_triggered": false
   - "risk_warning": ""
5. [语言要求]：JSON 中的所有文本内容 (Values) 必须全部使用中文。
6. [绝对无 Markdown]：直接输出纯粹的 JSON 字符串本体！严禁输出任何多余的解释，严禁使用 ``` 或 ```json 等代码块标签包裹。
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
    db: Session,
    user_id: str,
    llm_payload: dict[str, Any],
) -> tuple[_ConsistencyCheckOutput, bool, str | None, int]:
    response_payload = generate_json_with_observability(
        db=db,
        user_id=user_id,
        operation="check_consistency",
        system_prompt=CONSISTENCY_CHECK_PROMPT,
        user_payload=llm_payload,
        llm_client_getter=get_llm_client,
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
        repaired_payload = generate_json_with_observability(
            db=db,
            user_id=user_id,
            operation="check_consistency",
            system_prompt=CONSISTENCY_CHECK_REPAIR_PROMPT,
            user_payload=repair_payload,
            llm_client_getter=get_llm_client,
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
        db=db,
        user_id=user_id,
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
