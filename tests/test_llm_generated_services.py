from __future__ import annotations

import copy
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.user import User
from app.services import consistency_check as consistency_service
from app.services import identity_model as identity_service
from app.services import launch_kit as launch_kit_service
from app.services import persona as persona_service
from app.services.llm_client import LLMServiceError


class _FakeLLMClient:
    def __init__(self, payload_by_operation: dict[str, dict | list[dict]]) -> None:
        self._payload_by_operation = copy.deepcopy(payload_by_operation)
        self.calls: list[dict] = []

    def generate_json(self, *, operation: str, system_prompt: str, user_payload: dict) -> dict:
        self.calls.append(
            {
                "operation": operation,
                "system_prompt": system_prompt,
                "user_payload": copy.deepcopy(user_payload),
            }
        )
        operation_payload = self._payload_by_operation[operation]
        if isinstance(operation_payload, list):
            if not operation_payload:
                raise AssertionError(f"no payload left for operation={operation}")
            current = operation_payload.pop(0)
            return copy.deepcopy(current)
        return copy.deepcopy(operation_payload)


def _make_db_session(tmp_path) -> tuple[Session, str]:
    db_path = tmp_path / "service_tests.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    db = SessionLocal()

    user = User()
    db.add(user)
    db.commit()
    db.refresh(user)
    return db, user.id


def _close_db(db: Session) -> None:
    engine = db.bind
    db.close()
    if engine is not None:
        engine.dispose()


def _valid_launch_kit_payload() -> dict:
    return {
        "sustainable_columns": ["col1", "col2", "col3"],
        "growth_experiment_suggestion": [
            {
                "name": "exp",
                "hypothesis": "hyp",
                "variables": ["v1"],
                "duration": "7d",
                "success_metric": "metric",
            }
        ],
        "days": [
            {
                "day_no": i,
                "theme": f"theme-{i}",
                "draft_or_outline": f"draft-{i}",
                "opening_text": f"opening-{i}",
            }
            for i in range(1, 8)
        ],
    }


def _invalid_launch_kit_payload_missing_outline() -> dict:
    payload = _valid_launch_kit_payload()
    payload["days"][4].pop("draft_or_outline")
    return payload


def test_generate_identity_models_persists_count(monkeypatch, tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    payload = {
        "models": [
            {
                "title": "Identity A",
                "target_audience_pain": "Pain A",
                "content_pillars": ["P1", "P2", "P3"],
                "tone_keywords": ["k1", "k2"],
                "tone_examples": ["e1", "e2", "e3", "e4", "e5"],
                "long_term_views": ["v1", "v2", "v3", "v4", "v5"],
                "differentiation": "Diff A",
                "growth_path_0_3m": "Plan A1",
                "growth_path_3_12m": "Plan A2",
                "monetization_validation_order": ["m1"],
                "risk_boundary": ["r1"],
            },
            {
                "title": "Identity B",
                "target_audience_pain": "Pain B",
                "content_pillars": ["P1", "P2", "P3"],
                "tone_keywords": ["k1", "k2"],
                "tone_examples": ["e1", "e2", "e3", "e4", "e5"],
                "long_term_views": ["v1", "v2", "v3", "v4", "v5"],
                "differentiation": "Diff B",
                "growth_path_0_3m": "Plan B1",
                "growth_path_3_12m": "Plan B2",
                "monetization_validation_order": ["m1"],
                "risk_boundary": ["r1"],
            },
            {
                "title": "Identity C",
                "target_audience_pain": "Pain C",
                "content_pillars": ["P1", "P2", "P3"],
                "tone_keywords": ["k1", "k2"],
                "tone_examples": ["e1", "e2", "e3", "e4", "e5"],
                "long_term_views": ["v1", "v2", "v3", "v4", "v5"],
                "differentiation": "Diff C",
                "growth_path_0_3m": "Plan C1",
                "growth_path_3_12m": "Plan C2",
                "monetization_validation_order": ["m1"],
                "risk_boundary": ["r1"],
            },
        ]
    }
    fake_client = _FakeLLMClient({"generate_identity_models": payload})
    monkeypatch.setattr(identity_service, "get_llm_client", lambda: fake_client)

    models = identity_service.generate_identity_models(
        db=db,
        user_id=user_id,
        session_id=None,
        capability_profile={"skill_stack": ["python"]},
        count=3,
    )

    assert len(models) == 3
    assert all(model.differentiation for model in models)
    prompt = fake_client.calls[0]["system_prompt"]
    assert "risk_boundary must be a JSON array of non-empty strings, never a plain string." in prompt
    assert "every models[i].risk_boundary is an array type" in prompt
    _close_db(db)


def test_generate_constitution_increments_version(monkeypatch, tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    payload = {
        "common_words": ["w1", "w2", "w3"],
        "forbidden_words": ["f1", "f2", "f3"],
        "sentence_preferences": ["s1", "s2", "s3"],
        "moat_positions": ["m1", "m2", "m3"],
        "narrative_mainline": "Narrative",
        "growth_arc_template": "Growth Arc",
    }
    fake_client = _FakeLLMClient({"generate_constitution": payload})
    monkeypatch.setattr(persona_service, "get_llm_client", lambda: fake_client)

    first = persona_service.generate_constitution(db=db, user_id=user_id)
    second = persona_service.generate_constitution(db=db, user_id=user_id)

    assert first.version == 1
    assert second.version == 2
    assert second.previous_version_id == first.id
    _close_db(db)


def test_generate_launch_kit_creates_7_days(monkeypatch, tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    payload = _valid_launch_kit_payload()
    fake_client = _FakeLLMClient({"generate_launch_kit": payload})
    monkeypatch.setattr(launch_kit_service, "get_llm_client", lambda: fake_client)

    kit = launch_kit_service.generate_launch_kit(db=db, user_id=user_id)

    assert kit.id is not None
    assert len(kit.days) == 7
    assert [day.day_no for day in kit.days] == [1, 2, 3, 4, 5, 6, 7]
    _close_db(db)


def test_check_consistency_persists_result(monkeypatch, tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    payload = {
        "deviation_items": ["item-1"],
        "deviation_reasons": ["reason-1"],
        "suggestions": ["suggestion-1"],
        "risk_triggered": True,
        "risk_warning": "warning",
    }
    fake_client = _FakeLLMClient({"check_consistency": payload})
    monkeypatch.setattr(consistency_service, "get_llm_client", lambda: fake_client)

    result = consistency_service.check_consistency(
        db=db,
        user_id=user_id,
        draft_text="a draft text",
    )
    check = result.check

    assert check.id is not None
    assert check.risk_triggered is True
    assert check.risk_warning == "warning"
    assert result.degraded is False
    assert result.degrade_reason is None
    assert result.schema_repair_attempts == 0
    _close_db(db)


def test_check_consistency_retries_schema_then_succeeds(monkeypatch, tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    invalid_payload = {
        "deviation_items": [],
        "deviation_reasons": [],
        "suggestions": [],
        "risk_triggered": False,
        "risk_warning": "",
    }
    valid_payload = {
        "deviation_items": ["item-1"],
        "deviation_reasons": ["reason-1"],
        "suggestions": ["suggestion-1"],
        "risk_triggered": False,
        "risk_warning": "",
    }
    fake_client = _FakeLLMClient({"check_consistency": [invalid_payload, valid_payload]})
    monkeypatch.setattr(consistency_service, "get_llm_client", lambda: fake_client)

    result = consistency_service.check_consistency(
        db=db,
        user_id=user_id,
        draft_text="a draft text",
    )
    check = result.check

    assert check.id is not None
    assert result.degraded is False
    assert result.degrade_reason is None
    assert result.schema_repair_attempts == 1
    assert len([c for c in fake_client.calls if c["operation"] == "check_consistency"]) == 2
    _close_db(db)


def test_check_consistency_degrades_after_schema_retry_exhaustion(monkeypatch, tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    invalid_payload = {
        "deviation_items": [],
        "deviation_reasons": [],
        "suggestions": [],
        "risk_triggered": False,
        "risk_warning": "",
    }
    fake_client = _FakeLLMClient(
        {"check_consistency": [invalid_payload, invalid_payload, invalid_payload]}
    )
    monkeypatch.setattr(consistency_service, "get_llm_client", lambda: fake_client)

    result = consistency_service.check_consistency(
        db=db,
        user_id=user_id,
        draft_text="a draft text",
    )
    check = result.check

    assert check.id is not None
    assert result.degraded is True
    assert result.degrade_reason == consistency_service.DEGRADE_REASON_SCHEMA_RETRY_EXHAUSTED
    assert result.schema_repair_attempts == 2

    deviation_items = json.loads(check.deviation_items_json)
    deviation_reasons = json.loads(check.deviation_reasons_json)
    suggestions = json.loads(check.suggestions_json)
    assert deviation_items
    assert deviation_reasons
    assert suggestions
    assert len([c for c in fake_client.calls if c["operation"] == "check_consistency"]) == 3
    _close_db(db)


def test_generate_launch_kit_retries_schema_then_succeeds(monkeypatch, tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    fake_client = _FakeLLMClient(
        {
            "generate_launch_kit": [
                _invalid_launch_kit_payload_missing_outline(),
                _valid_launch_kit_payload(),
            ]
        }
    )
    monkeypatch.setattr(launch_kit_service, "get_llm_client", lambda: fake_client)

    kit = launch_kit_service.generate_launch_kit(db=db, user_id=user_id)

    assert kit.id is not None
    assert len(kit.days) == 7
    assert len([c for c in fake_client.calls if c["operation"] == "generate_launch_kit"]) == 2
    _close_db(db)


def test_generate_launch_kit_fails_after_schema_retry_exhaustion(monkeypatch, tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    invalid = _invalid_launch_kit_payload_missing_outline()
    fake_client = _FakeLLMClient(
        {"generate_launch_kit": [invalid, invalid, invalid]}
    )
    monkeypatch.setattr(launch_kit_service, "get_llm_client", lambda: fake_client)

    with pytest.raises(LLMServiceError) as exc_info:
        launch_kit_service.generate_launch_kit(db=db, user_id=user_id)

    assert exc_info.value.code == "LLM_SCHEMA_VALIDATION_FAILED"
    assert "after 2 schema repair retries" in exc_info.value.message
    _close_db(db)


def test_identity_generation_schema_error_when_field_missing(monkeypatch, tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    payload = {
        "models": [
            {
                "title": "Identity A",
                "target_audience_pain": "Pain A",
                "content_pillars": ["P1", "P2", "P3"],
                "tone_keywords": ["k1", "k2"],
                "tone_examples": ["e1", "e2", "e3", "e4", "e5"],
                "long_term_views": ["v1", "v2", "v3", "v4", "v5"],
                "growth_path_0_3m": "Plan A1",
                "growth_path_3_12m": "Plan A2",
                "monetization_validation_order": ["m1"],
                "risk_boundary": ["r1"],
            },
            {
                "title": "Identity B",
                "target_audience_pain": "Pain B",
                "content_pillars": ["P1", "P2", "P3"],
                "tone_keywords": ["k1", "k2"],
                "tone_examples": ["e1", "e2", "e3", "e4", "e5"],
                "long_term_views": ["v1", "v2", "v3", "v4", "v5"],
                "growth_path_0_3m": "Plan B1",
                "growth_path_3_12m": "Plan B2",
                "monetization_validation_order": ["m1"],
                "risk_boundary": ["r1"],
            },
            {
                "title": "Identity C",
                "target_audience_pain": "Pain C",
                "content_pillars": ["P1", "P2", "P3"],
                "tone_keywords": ["k1", "k2"],
                "tone_examples": ["e1", "e2", "e3", "e4", "e5"],
                "long_term_views": ["v1", "v2", "v3", "v4", "v5"],
                "growth_path_0_3m": "Plan C1",
                "growth_path_3_12m": "Plan C2",
                "monetization_validation_order": ["m1"],
                "risk_boundary": ["r1"],
            },
        ]
    }
    fake_client = _FakeLLMClient({"generate_identity_models": payload})
    monkeypatch.setattr(identity_service, "get_llm_client", lambda: fake_client)

    with pytest.raises(LLMServiceError) as exc_info:
        identity_service.generate_identity_models(
            db=db,
            user_id=user_id,
            session_id=None,
            capability_profile={},
            count=3,
        )

    assert exc_info.value.code == "LLM_SCHEMA_VALIDATION_FAILED"
    _close_db(db)
