from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError, field_validator, model_validator
from sqlalchemy.orm import Session

from app.models.identity_model import IdentityModel, IdentitySelection
from app.models.launch_kit import LaunchKit, LaunchKitDay
from app.models.onboarding import CapabilityProfile
from app.models.persona import PersonaConstitution, RiskBoundaryItem
from app.services.llm_client import LLMServiceError, get_llm_client, llm_schema_error

logger = logging.getLogger(__name__)

SCHEMA_REPAIR_MAX_RETRIES = 2
MAX_TEXT_CHARS = 120
MAX_LIST_ITEMS = 5
MAX_TONE_EXAMPLES = 3
MAX_RISK_BOUNDARIES = 6


class _LaunchKitDayOutput(BaseModel):
    """Single day output schema."""

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
    """Top-level launch kit output schema."""

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


class _LaunchKitDayArticleOutput(BaseModel):
    """Single day article output schema."""

    day_no: int
    title: str
    markdown: str

    @field_validator("day_no")
    @classmethod
    def validate_day_no(cls, value: int) -> int:
        if value < 1 or value > 7:
            raise ValueError("day_no must be between 1 and 7")
        return value

    @model_validator(mode="after")
    def validate_text(self) -> "_LaunchKitDayArticleOutput":
        if not self.title.strip():
            raise ValueError("title must be non-empty")
        if not self.markdown.strip():
            raise ValueError("markdown must be non-empty")
        return self


@dataclass
class _ContextResolutionResult:
    context_bundle: dict[str, Any]
    resolved_identity_model_id: str | None
    resolved_constitution_id: str | None
    context_sources: dict[str, str]


LAUNCH_KIT_PROMPT = """
你是一名内容增长助手，需要为创作者生成 7 天启动包（launch kit）。
Return strict JSON only.
只返回严格 JSON。不要输出 markdown、说明性文字、注释或代码块围栏。

期望 JSON 结构：
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
      "draft_or_outline": "string",// 该字段必须为非空字符串，字数大于128
      "opening_text": "string"
    }
  ]
}

硬性约束：
- days 必须且只能包含 7 条记录。
- day_no 必须唯一，并完整覆盖 1..7。
- 每个 day 条目只能包含：day_no、theme、draft_or_outline、opening_text。
- theme、draft_or_outline、opening_text 必须为非空字符串。
- sustainable_columns 至少包含 3 个非空字符串。
- growth_experiment_suggestion 至少包含 1 项。
- 不要使用 HTML 标签，例如 <br>。

Context alignment constraints:
上下文对齐约束：
- 你会在用户载荷中收到 context_bundle。
- 如果存在 context_bundle.identity_model，day 的主题与草稿/大纲要对齐其 content_pillars、differentiation、target_audience_pain。
- 如果存在 context_bundle.persona_constitution，需遵循 common_words、forbidden_words、sentence_preferences、narrative_mainline。
- 如果 context_bundle.risk_boundaries 非空，避免使用与其明显冲突的表达。
- 如果存在 context_bundle.capability_profile，实验节奏要符合 risk_tolerance 与 time_investment_hours。
- 若任何 context 块缺失，只使用已有上下文，禁止虚构缺失事实。

返回前自检：
1) days 长度为 7
2) day_no 恰好覆盖 1..7 且无重复
3) 每一天都包含非空 draft_or_outline
4) 不引入任何额外 key
""".strip()

LAUNCH_KIT_REPAIR_PROMPT = """
You are repairing an invalid 7-day launch kit JSON.
你正在修复一个不合法的 7 天 launch kit JSON。
你将收到：original_user_payload、previous_invalid_response、validation_error。
只返回严格 JSON，且必须完全符合目标 schema。
不要输出 markdown、说明性文字、注释或代码块围栏。

Schema：
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
      "draft_or_outline": "string",// 该字段必须为非空字符串，字数大于128
      "opening_text": "string"
    }
  ]
}

硬性约束：
- 必须保留且仅保留 7 天。
- day_no 必须唯一并覆盖 1..7。
- day 仅保留允许的字段 key。
- 所有必填字段必须非空。
- sustainable_columns 至少 3 项，growth_experiment_suggestion 至少 1 项。
- 必须保持与 original_user_payload 中 context_bundle 的语义对齐。
""".strip()

LAUNCH_KIT_DAY_ARTICLE_PROMPT = """
You are generating a single publish-ready article from one launch-kit day card.
Return strict JSON only.

Target JSON schema:
{
  "day_no": 1,
  "title": "string",
  "markdown": "string"
}

Hard constraints:
- Keep day_no unchanged from input.
- title must be non-empty and concise.
- markdown must be non-empty and ready to publish.
- No markdown code fences in markdown body.
- Do not output extra keys.
- Align style with context_bundle when provided.
""".strip()

LAUNCH_KIT_DAY_ARTICLE_REPAIR_PROMPT = """
You are repairing an invalid launch-kit day article JSON.
Return strict JSON only and satisfy the target schema exactly.

Schema:
{
  "day_no": 1,
  "title": "string",
  "markdown": "string"
}

Hard constraints:
- Keep day_no unchanged from original_user_payload.
- title and markdown must be non-empty.
- No extra keys.
""".strip()


def _parse_launch_kit(payload: dict[str, Any]) -> _LaunchKitOutput:
    """Validate launch kit payload before persistence."""
    try:
        return _LaunchKitOutput.model_validate(payload)
    except ValidationError as exc:
        raise llm_schema_error(
            "generate_launch_kit",
            f"Launch kit schema validation failed: {exc}",
        ) from exc


def _parse_launch_kit_day_article(
    payload: dict[str, Any],
    *,
    expected_day_no: int,
) -> _LaunchKitDayArticleOutput:
    """Validate day article payload."""
    try:
        output = _LaunchKitDayArticleOutput.model_validate(payload)
    except ValidationError as exc:
        raise llm_schema_error(
            "generate_launch_kit_day_article",
            f"Launch kit day article schema validation failed: {exc}",
        ) from exc

    if output.day_no != expected_day_no:
        raise llm_schema_error(
            "generate_launch_kit_day_article",
            f"Launch kit day article day_no mismatch: expected={expected_day_no} actual={output.day_no}",
        )

    return output


def _validation_error_brief(error_message: str) -> str:
    first_line = error_message.splitlines()[0] if error_message else "unknown"
    return first_line[:200]


def _truncate_text(value: Any, limit: int = MAX_TEXT_CHARS) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit]


def _safe_loads_list(raw: str) -> list[Any]:
    try:
        payload = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []
    return payload if isinstance(payload, list) else []


def _to_short_text_list(
    items: list[Any],
    *,
    max_items: int = MAX_LIST_ITEMS,
    max_chars: int = MAX_TEXT_CHARS,
) -> list[str]:
    results: list[str] = []
    for item in items:
        text = ""
        if isinstance(item, str):
            text = item
        elif isinstance(item, (int, float, bool)):
            text = str(item)
        elif isinstance(item, dict):
            for key in ("interest", "topic", "name", "label", "value", "statement"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    text = value
                    break
            if not text:
                text = json.dumps(item, ensure_ascii=False)
        if not text:
            continue
        text = _truncate_text(text, limit=max_chars)
        if text:
            results.append(text)
        if len(results) >= max_items:
            break
    return results


def _identity_to_context(identity: IdentityModel) -> dict[str, Any]:
    return {
        "id": identity.id,
        "title": _truncate_text(identity.title),
        "target_audience_pain": _truncate_text(identity.target_audience_pain),
        "content_pillars": _to_short_text_list(_safe_loads_list(identity.content_pillars_json)),
        "tone_keywords": _to_short_text_list(_safe_loads_list(identity.tone_keywords_json)),
        "tone_examples": _to_short_text_list(
            _safe_loads_list(identity.tone_examples_json),
            max_items=MAX_TONE_EXAMPLES,
        ),
        "long_term_views": _to_short_text_list(_safe_loads_list(identity.long_term_views_json)),
        "differentiation": _truncate_text(identity.differentiation),
        "growth_path_0_3m": _truncate_text(identity.growth_path_0_3m),
        "growth_path_3_12m": _truncate_text(identity.growth_path_3_12m),
        "monetization_validation_order": _to_short_text_list(
            _safe_loads_list(identity.monetization_validation_order_json)
        ),
        "risk_boundary": _to_short_text_list(_safe_loads_list(identity.risk_boundary_json)),
    }


def _constitution_to_context(constitution: PersonaConstitution) -> dict[str, Any]:
    return {
        "id": constitution.id,
        "common_words": _to_short_text_list(_safe_loads_list(constitution.common_words_json)),
        "forbidden_words": _to_short_text_list(_safe_loads_list(constitution.forbidden_words_json)),
        "sentence_preferences": _to_short_text_list(
            _safe_loads_list(constitution.sentence_preferences_json)
        ),
        "moat_positions": _to_short_text_list(_safe_loads_list(constitution.moat_positions_json)),
        "narrative_mainline": _truncate_text(constitution.narrative_mainline),
        "growth_arc_template": _truncate_text(constitution.growth_arc_template),
    }


def _profile_to_context(profile: CapabilityProfile) -> dict[str, Any]:
    return {
        "id": profile.id,
        "session_id": profile.session_id,
        "skill_stack": _to_short_text_list(_safe_loads_list(profile.skill_stack_json)),
        "interest_energy_curve": _to_short_text_list(
            _safe_loads_list(profile.interest_energy_curve_json)
        ),
        "cognitive_style": _truncate_text(profile.cognitive_style),
        "value_boundaries": _to_short_text_list(_safe_loads_list(profile.value_boundaries_json)),
        "risk_tolerance": profile.risk_tolerance,
        "time_investment_hours": profile.time_investment_hours,
    }


def _risk_boundary_to_context(boundary: RiskBoundaryItem) -> dict[str, Any]:
    return {
        "risk_level": boundary.risk_level,
        "boundary_type": _truncate_text(boundary.boundary_type),
        "statement": _truncate_text(boundary.statement),
        "source": _truncate_text(boundary.source),
    }


def _resolve_identity_model(
    *,
    db: Session,
    user_id: str,
    requested_identity_model_id: str | None,
) -> tuple[IdentityModel | None, str]:
    if requested_identity_model_id:
        requested = db.query(IdentityModel).filter(IdentityModel.id == requested_identity_model_id).first()
        if requested and requested.user_id == user_id:
            return requested, "request"
        logger.warning(
            "launch_kit_context_identity_not_found user_id=%s requested_identity_model_id=%s",
            user_id,
            requested_identity_model_id,
        )

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
            return selected, "selection"
        logger.warning(
            "launch_kit_context_selection_orphaned user_id=%s primary_identity_id=%s",
            user_id,
            selection.primary_identity_id,
        )

    latest = (
        db.query(IdentityModel)
        .filter(IdentityModel.user_id == user_id)
        .order_by(IdentityModel.created_at.desc(), IdentityModel.id.desc())
        .first()
    )
    if latest:
        return latest, "latest"

    return None, "none"


def _resolve_constitution(
    *,
    db: Session,
    user_id: str,
    requested_constitution_id: str | None,
    resolved_identity: IdentityModel | None,
) -> tuple[PersonaConstitution | None, str]:
    if requested_constitution_id:
        requested = (
            db.query(PersonaConstitution)
            .filter(PersonaConstitution.id == requested_constitution_id)
            .first()
        )
        if requested and requested.user_id == user_id:
            return requested, "request"
        logger.warning(
            "launch_kit_context_constitution_not_found user_id=%s requested_constitution_id=%s",
            user_id,
            requested_constitution_id,
        )

    if resolved_identity:
        by_identity = (
            db.query(PersonaConstitution)
            .filter(
                PersonaConstitution.user_id == user_id,
                PersonaConstitution.identity_model_id == resolved_identity.id,
            )
            .order_by(PersonaConstitution.version.desc(), PersonaConstitution.created_at.desc())
            .first()
        )
        if by_identity:
            return by_identity, "identity"

    latest = (
        db.query(PersonaConstitution)
        .filter(PersonaConstitution.user_id == user_id)
        .order_by(PersonaConstitution.version.desc(), PersonaConstitution.created_at.desc())
        .first()
    )
    if latest:
        return latest, "latest"

    return None, "none"


def _resolve_capability_profile(
    *,
    db: Session,
    user_id: str,
    resolved_identity: IdentityModel | None,
) -> tuple[CapabilityProfile | None, str]:
    if resolved_identity and resolved_identity.session_id:
        by_session = (
            db.query(CapabilityProfile)
            .filter(
                CapabilityProfile.user_id == user_id,
                CapabilityProfile.session_id == resolved_identity.session_id,
            )
            .first()
        )
        if by_session:
            return by_session, "session"
        logger.warning(
            "launch_kit_context_profile_not_found user_id=%s session_id=%s",
            user_id,
            resolved_identity.session_id,
        )

    latest = (
        db.query(CapabilityProfile)
        .filter(CapabilityProfile.user_id == user_id)
        .order_by(CapabilityProfile.created_at.desc(), CapabilityProfile.id.desc())
        .first()
    )
    if latest:
        return latest, "latest"

    return None, "none"


def _query_recent_boundaries(
    *,
    db: Session,
    user_id: str,
    constitution_id: str | None = None,
    identity_model_id: str | None = None,
) -> list[RiskBoundaryItem]:
    query = db.query(RiskBoundaryItem).filter(RiskBoundaryItem.user_id == user_id)
    if constitution_id is not None:
        query = query.filter(RiskBoundaryItem.constitution_id == constitution_id)
    elif identity_model_id is not None:
        query = query.filter(RiskBoundaryItem.identity_model_id == identity_model_id)

    return (
        query.order_by(RiskBoundaryItem.created_at.desc(), RiskBoundaryItem.id.desc())
        .limit(MAX_RISK_BOUNDARIES)
        .all()
    )


def _resolve_risk_boundaries(
    *,
    db: Session,
    user_id: str,
    resolved_identity: IdentityModel | None,
    resolved_constitution: PersonaConstitution | None,
) -> tuple[list[RiskBoundaryItem], str]:
    if resolved_constitution:
        by_constitution = _query_recent_boundaries(
            db=db,
            user_id=user_id,
            constitution_id=resolved_constitution.id,
        )
        if by_constitution:
            return by_constitution, "constitution"

    if resolved_identity:
        by_identity = _query_recent_boundaries(
            db=db,
            user_id=user_id,
            identity_model_id=resolved_identity.id,
        )
        if by_identity:
            return by_identity, "identity"

    latest = _query_recent_boundaries(db=db, user_id=user_id)
    if latest:
        return latest, "latest"

    return [], "none"


def _resolve_context_bundle(
    *,
    db: Session,
    user_id: str,
    requested_identity_model_id: str | None,
    requested_constitution_id: str | None,
) -> _ContextResolutionResult:
    identity, identity_source = _resolve_identity_model(
        db=db,
        user_id=user_id,
        requested_identity_model_id=requested_identity_model_id,
    )
    constitution, constitution_source = _resolve_constitution(
        db=db,
        user_id=user_id,
        requested_constitution_id=requested_constitution_id,
        resolved_identity=identity,
    )
    profile, profile_source = _resolve_capability_profile(
        db=db,
        user_id=user_id,
        resolved_identity=identity,
    )
    boundaries, boundaries_source = _resolve_risk_boundaries(
        db=db,
        user_id=user_id,
        resolved_identity=identity,
        resolved_constitution=constitution,
    )

    context_sources = {
        "identity_model_source": identity_source,
        "persona_constitution_source": constitution_source,
        "capability_profile_source": profile_source,
        "risk_boundaries_source": boundaries_source,
    }
    context_bundle = {
        "identity_model": _identity_to_context(identity) if identity else None,
        "persona_constitution": _constitution_to_context(constitution) if constitution else None,
        "capability_profile": _profile_to_context(profile) if profile else None,
        "risk_boundaries": [_risk_boundary_to_context(item) for item in boundaries[:MAX_RISK_BOUNDARIES]],
        "resolution_meta": {
            **context_sources,
            "requested_identity_model_id": requested_identity_model_id,
            "requested_constitution_id": requested_constitution_id,
            "resolved_identity_model_id": identity.id if identity else None,
            "resolved_constitution_id": constitution.id if constitution else None,
        },
    }

    return _ContextResolutionResult(
        context_bundle=context_bundle,
        resolved_identity_model_id=identity.id if identity else None,
        resolved_constitution_id=constitution.id if constitution else None,
        context_sources=context_sources,
    )


def _generate_launch_kit_output(*, llm_payload: dict[str, Any]) -> tuple[_LaunchKitOutput, int]:
    llm_client = get_llm_client()
    response_payload = llm_client.generate_json(
        operation="generate_launch_kit",
        system_prompt=LAUNCH_KIT_PROMPT,
        user_payload=llm_payload,
    )

    try:
        return _parse_launch_kit(response_payload), 0
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
        repaired_payload = llm_client.generate_json(
            operation="generate_launch_kit",
            system_prompt=LAUNCH_KIT_REPAIR_PROMPT,
            user_payload=repair_payload,
        )
        try:
            return _parse_launch_kit(repaired_payload), attempt
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


def _generate_launch_kit_day_article_output(
    *,
    llm_payload: dict[str, Any],
    expected_day_no: int,
) -> tuple[_LaunchKitDayArticleOutput, int]:
    llm_client = get_llm_client()
    response_payload = llm_client.generate_json(
        operation="generate_launch_kit_day_article",
        system_prompt=LAUNCH_KIT_DAY_ARTICLE_PROMPT,
        user_payload=llm_payload,
    )

    try:
        return _parse_launch_kit_day_article(
            response_payload,
            expected_day_no=expected_day_no,
        ), 0
    except LLMServiceError as exc:
        if exc.code != "LLM_SCHEMA_VALIDATION_FAILED":
            raise
        last_error = exc

    last_payload = response_payload
    for attempt in range(1, SCHEMA_REPAIR_MAX_RETRIES + 1):
        logger.warning(
            "schema_retry operation=generate_launch_kit_day_article schema_retry_attempt=%s validation_error_brief=%s degraded=%s",
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
            operation="generate_launch_kit_day_article",
            system_prompt=LAUNCH_KIT_DAY_ARTICLE_REPAIR_PROMPT,
            user_payload=repair_payload,
        )
        try:
            return _parse_launch_kit_day_article(
                repaired_payload,
                expected_day_no=expected_day_no,
            ), attempt
        except LLMServiceError as exc:
            if exc.code != "LLM_SCHEMA_VALIDATION_FAILED":
                raise
            last_error = exc
            last_payload = repaired_payload

    raise llm_schema_error(
        "generate_launch_kit_day_article",
        (
            "Launch kit day article schema validation failed after 2 schema repair retries. "
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
    """Generate a 7-day launch kit via LLM."""
    total_start = time.perf_counter()
    context_resolve_ms = 0
    llm_generate_ms = 0
    schema_repair_attempts = 0
    context_sources = {
        "identity_model_source": "none",
        "persona_constitution_source": "none",
        "capability_profile_source": "none",
        "risk_boundaries_source": "none",
    }

    try:
        context_start = time.perf_counter()
        context_resolution = _resolve_context_bundle(
            db=db,
            user_id=user_id,
            requested_identity_model_id=identity_model_id,
            requested_constitution_id=constitution_id,
        )
        context_resolve_ms = int((time.perf_counter() - context_start) * 1000)
        context_sources = context_resolution.context_sources

        llm_payload = {
            "user_id": user_id,
            "identity_model_id": context_resolution.resolved_identity_model_id,
            "constitution_id": context_resolution.resolved_constitution_id,
            "hint_sustainable_columns": sustainable_columns or [],
            "hint_growth_experiment_suggestion": growth_experiment_suggestion or [],
            "context_bundle": context_resolution.context_bundle,
        }

        llm_start = time.perf_counter()
        output, schema_repair_attempts = _generate_launch_kit_output(llm_payload=llm_payload)
        llm_generate_ms = int((time.perf_counter() - llm_start) * 1000)

        kit = LaunchKit(
            user_id=user_id,
            identity_model_id=context_resolution.resolved_identity_model_id,
            constitution_id=context_resolution.resolved_constitution_id,
            sustainable_columns_json=json.dumps(output.sustainable_columns, ensure_ascii=False),
            growth_experiment_suggestion_json=json.dumps(
                output.growth_experiment_suggestion,
                ensure_ascii=False,
            ),
        )
        db.add(kit)
        db.flush()

        for day_output in sorted(output.days, key=lambda day: day.day_no):
            day = LaunchKitDay(
                kit_id=kit.id,
                day_no=day_output.day_no,
                theme=day_output.theme,
                draft_or_outline=day_output.draft_or_outline,
                opening_text=day_output.opening_text,
            )
            db.add(day)

        db.commit()
        db.refresh(kit)
        return kit
    finally:
        total_ms = int((time.perf_counter() - total_start) * 1000)
        logger.info(
            "launch_kit_generation_metrics user_id=%s context_resolve_ms=%s llm_generate_ms=%s schema_repair_attempts=%s total_ms=%s context_sources=%s",
            user_id,
            context_resolve_ms,
            llm_generate_ms,
            schema_repair_attempts,
            total_ms,
            json.dumps(context_sources, ensure_ascii=False, sort_keys=True),
        )


def generate_launch_kit_day_article(
    db: Session,
    user_id: str,
    day_no: int,
    theme: str,
    draft_or_outline: str,
    opening_text: str,
    identity_model_id: str | None = None,
    constitution_id: str | None = None,
) -> _LaunchKitDayArticleOutput:
    """Generate a single launch-kit day article via LLM without persistence."""
    total_start = time.perf_counter()
    context_resolve_ms = 0
    llm_generate_ms = 0
    schema_repair_attempts = 0
    context_sources = {
        "identity_model_source": "none",
        "persona_constitution_source": "none",
        "capability_profile_source": "none",
        "risk_boundaries_source": "none",
    }

    try:
        context_start = time.perf_counter()
        context_resolution = _resolve_context_bundle(
            db=db,
            user_id=user_id,
            requested_identity_model_id=identity_model_id,
            requested_constitution_id=constitution_id,
        )
        context_resolve_ms = int((time.perf_counter() - context_start) * 1000)
        context_sources = context_resolution.context_sources

        llm_payload = {
            "user_id": user_id,
            "identity_model_id": context_resolution.resolved_identity_model_id,
            "constitution_id": context_resolution.resolved_constitution_id,
            "day_no": day_no,
            "theme": theme,
            "draft_or_outline": draft_or_outline,
            "opening_text": opening_text,
            "context_bundle": context_resolution.context_bundle,
        }

        llm_start = time.perf_counter()
        output, schema_repair_attempts = _generate_launch_kit_day_article_output(
            llm_payload=llm_payload,
            expected_day_no=day_no,
        )
        llm_generate_ms = int((time.perf_counter() - llm_start) * 1000)
        return output
    finally:
        total_ms = int((time.perf_counter() - total_start) * 1000)
        logger.info(
            "launch_kit_day_article_generation_metrics user_id=%s day_no=%s context_resolve_ms=%s llm_generate_ms=%s schema_repair_attempts=%s total_ms=%s context_sources=%s",
            user_id,
            day_no,
            context_resolve_ms,
            llm_generate_ms,
            schema_repair_attempts,
            total_ms,
            json.dumps(context_sources, ensure_ascii=False, sort_keys=True),
        )


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
