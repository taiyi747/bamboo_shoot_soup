"""启动包服务。"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel, ValidationError, field_validator, model_validator
from sqlalchemy.orm import Session

from app.models.launch_kit import LaunchKit, LaunchKitDay
from app.services.llm_client import LLMServiceError, get_llm_client, llm_schema_error
from app.services.llm_observability import generate_json_with_observability

logger = logging.getLogger(__name__)

SCHEMA_REPAIR_MAX_RETRIES = 2


class _LaunchKitDayOutput(BaseModel):
    """启动包单日内容结构。"""

    day_no: int
    theme: str
    draft_or_outline: str
    opening_text: str

    @field_validator("day_no")
    @classmethod
    def validate_day_no(cls, value: int) -> int:
        if value < 1 or value > 7:
            raise ValueError("day_no must be between 1 and 7")
        return value

    @model_validator(mode="after")
    def validate_text(self) -> "_LaunchKitDayOutput":
        if not self.theme.strip():
            raise ValueError("theme must be non-empty")
        if not self.draft_or_outline.strip():
            raise ValueError("draft_or_outline must be non-empty")
        if not self.opening_text.strip():
            raise ValueError("opening_text must be non-empty")
        return self


class _LaunchKitOutput(BaseModel):
    """启动包顶层结构。"""

    sustainable_columns: list[str]
    growth_experiment_suggestion: list[dict[str, Any]]
    days: list[_LaunchKitDayOutput]

    @model_validator(mode="after")
    def validate_business_rules(self) -> "_LaunchKitOutput":
        if len(self.sustainable_columns) < 3:
            raise ValueError("sustainable_columns must contain at least 3 items")
        if len(self.growth_experiment_suggestion) < 1:
            raise ValueError("growth_experiment_suggestion must contain at least 1 item")
        if len(self.days) != 7:
            raise ValueError("days must contain exactly 7 entries")

        day_numbers = sorted(day.day_no for day in self.days)
        if day_numbers != [1, 2, 3, 4, 5, 6, 7]:
            raise ValueError("days must contain unique day_no values 1..7")
        return self


LAUNCH_KIT_PROMPT = """
你是一名内容增长策略助手，需要为创作者生成 7 天启动包 JSON。
只返回严格 JSON 对象，不要输出 Markdown、解释、注释或代码块。
输出必须严格符合以下结构（字段名不可修改、不可新增）：
{
  "sustainable_columns": ["string", "... 至少 3 项"],
  "growth_experiment_suggestion": [
    {
      "name": "string",
      "hypothesis": "string",
      "variables": ["string", "..."],
      "duration": "string",
      "success_metric": "string"
    }
  ],
  "days": [
    {
      "day_no": 1,
      "theme": "string",
      "draft_or_outline": "string",
      "opening_text": "string"
    }
  ]
}
硬约束：
- 必须包含且仅包含 7 条 days
- day_no 必须唯一，且完整覆盖 1..7
- 每个 day 必须且仅可包含 day_no、theme、draft_or_outline、opening_text
- theme、draft_or_outline、opening_text 必须为非空字符串
- sustainable_columns 至少 3 项，且每项为非空字符串
- growth_experiment_suggestion 至少 1 项
返回前自检：
1) days 长度是否为 7
2) day_no 是否恰好为 1..7 且无重复
3) 每个 day 是否都包含 draft_or_outline 且非空
""".strip()

LAUNCH_KIT_REPAIR_PROMPT = """
你正在修复一个不合法的 7 天启动包 JSON。
你会收到 original_user_payload、previous_invalid_response、validation_error。
只返回修复后的严格 JSON 对象，不要输出 Markdown、解释、注释或代码块。
输出必须严格符合以下结构（字段名不可修改、不可新增）：
{
  "sustainable_columns": ["string", "... 至少 3 项"],
  "growth_experiment_suggestion": [
    {
      "name": "string",
      "hypothesis": "string",
      "variables": ["string", "..."],
      "duration": "string",
      "success_metric": "string"
    }
  ],
  "days": [
    {
      "day_no": 1,
      "theme": "string",
      "draft_or_outline": "string",
      "opening_text": "string"
    }
  ]
}
硬约束：
- 必须包含且仅包含 7 条 days
- day_no 必须唯一且完整覆盖 1..7
- 每个 day 必须且仅可包含 day_no、theme、draft_or_outline、opening_text
- theme、draft_or_outline、opening_text 必须为非空字符串
- sustainable_columns 至少 3 项，且每项为非空字符串
- growth_experiment_suggestion 至少 1 项
""".strip()


def _parse_launch_kit(payload: dict[str, Any]) -> _LaunchKitOutput:
    """落库前对启动包响应进行结构化校验。"""
    try:
        return _LaunchKitOutput.model_validate(payload)
    except ValidationError as exc:
        raise llm_schema_error(
            "generate_launch_kit",
            f"Launch kit schema validation failed: {exc}",
        ) from exc


def _validation_error_brief(error_message: str) -> str:
    first_line = error_message.splitlines()[0] if error_message else "unknown"
    return first_line[:200]


def _generate_launch_kit_output(
    *,
    db: Session,
    user_id: str,
    llm_payload: dict[str, Any],
) -> _LaunchKitOutput:
    response_payload = generate_json_with_observability(
        db=db,
        user_id=user_id,
        operation="generate_launch_kit",
        system_prompt=LAUNCH_KIT_PROMPT,
        user_payload=llm_payload,
        llm_client_getter=get_llm_client,
    )

    try:
        return _parse_launch_kit(response_payload)
    except LLMServiceError as exc:
        if exc.code != "LLM_SCHEMA_VALIDATION_FAILED":
            raise
        last_error = exc

    last_payload = response_payload
    for attempt in range(1, SCHEMA_REPAIR_MAX_RETRIES + 1):
        logger.warning(
            "schema_retry operation=generate_launch_kit schema_retry_attempt=%s validation_error_brief=%s degraded=%s",
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
            operation="generate_launch_kit",
            system_prompt=LAUNCH_KIT_REPAIR_PROMPT,
            user_payload=repair_payload,
            llm_client_getter=get_llm_client,
        )
        try:
            return _parse_launch_kit(repaired_payload)
        except LLMServiceError as exc:
            if exc.code != "LLM_SCHEMA_VALIDATION_FAILED":
                raise
            last_error = exc
            last_payload = repaired_payload

    raise llm_schema_error(
        "generate_launch_kit",
        (
            "Launch kit schema validation failed after 2 schema repair retries. "
            f"Last error: {_validation_error_brief(last_error.message)}"
        ),
    )


def generate_launch_kit(
    db: Session,
    user_id: str,
    identity_model_id: str | None = None,
    constitution_id: str | None = None,
    sustainable_columns: list[str] | None = None,
    growth_experiment_suggestion: list[dict] | None = None,
) -> LaunchKit:
    """
    Generate 7-Day Launch Kit via LLM.

    Per product-spec 2.3:
    - 7日每日主题
    - 每日内容草稿或大纲（含开头）
    - 3个可持续栏目
    - 1个增长实验建议
    """
    llm_payload = {
        "user_id": user_id,
        "identity_model_id": identity_model_id,
        "constitution_id": constitution_id,
        # 提示词是可选输入，不会绕过服务端严格校验。
        "hint_sustainable_columns": sustainable_columns or [],
        "hint_growth_experiment_suggestion": growth_experiment_suggestion or [],
    }
    output = _generate_launch_kit_output(
        db=db,
        user_id=user_id,
        llm_payload=llm_payload,
    )

    # 第三步：先写入启动包主记录，再写入每日明细。
    kit = LaunchKit(
        user_id=user_id,
        identity_model_id=identity_model_id,
        constitution_id=constitution_id,
        sustainable_columns_json=json.dumps(output.sustainable_columns, ensure_ascii=False),
        growth_experiment_suggestion_json=json.dumps(
            output.growth_experiment_suggestion,
            ensure_ascii=False,
        ),
    )
    db.add(kit)
    # flush 后可拿到 kit.id，供子表外键使用。
    db.flush()

    # 按 day_no 排序写入，保证读取顺序稳定。
    for day_output in sorted(output.days, key=lambda day: day.day_no):
        day = LaunchKitDay(
            kit_id=kit.id,
            day_no=day_output.day_no,
            theme=day_output.theme,
            draft_or_outline=day_output.draft_or_outline,
            opening_text=day_output.opening_text,
        )
        db.add(day)

    # 一次提交，保证主从记录事务一致。
    db.commit()
    db.refresh(kit)
    return kit


def get_user_launch_kits(db: Session, user_id: str) -> list[LaunchKit]:
    """Get all launch kits for a user."""
    return db.query(LaunchKit).filter(LaunchKit.user_id == user_id).all()


def get_launch_kit(db: Session, kit_id: str) -> LaunchKit | None:
    """Get launch kit by ID with days."""
    return db.query(LaunchKit).filter(LaunchKit.id == kit_id).first()


def get_latest_launch_kit(db: Session, user_id: str) -> LaunchKit | None:
    """Get user's latest launch kit."""
    return (
        db.query(LaunchKit)
        .filter(LaunchKit.user_id == user_id)
        .order_by(LaunchKit.created_at.desc())
        .first()
    )
