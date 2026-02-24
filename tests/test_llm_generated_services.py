from __future__ import annotations

import copy
import json
import threading

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.consistency_check import ConsistencyCheck
from app.models.identity_model import IdentityModel, IdentitySelection
from app.models.launch_kit import LaunchKit
from app.models.onboarding import CapabilityProfile, OnboardingSession
from app.models.persona import PersonaConstitution, RiskBoundaryItem
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
        self._lock = threading.Lock()

    def generate_json(self, *, operation: str, system_prompt: str, user_payload: dict) -> dict:
        with self._lock:
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


def _identity_model_payload(prefix: str, label: str) -> dict:
    return {
        "models": [
            {
                "title": f"{prefix} {label}",
                "target_audience_pain": f"Pain {label}",
                "content_pillars": ["P1", "P2", "P3"],
                "tone_keywords": ["k1", "k2"],
                "tone_examples": ["e1", "e2", "e3", "e4", "e5"],
                "long_term_views": ["v1", "v2", "v3", "v4", "v5"],
                "differentiation": f"{prefix} Diff {label}",
                "growth_path_0_3m": f"Plan {label}1",
                "growth_path_3_12m": f"Plan {label}2",
                "monetization_validation_order": ["m1"],
                "risk_boundary": ["r1"],
            },
        ]
    }


def _identity_model_payloads(prefix: str, count: int) -> list[dict]:
    labels = ["A", "B", "C", "D", "E"][:count]
    return [_identity_model_payload(prefix, label) for label in labels]


def test_generate_identity_models_persists_count(monkeypatch, tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    fake_client = _FakeLLMClient({"generate_identity_models": _identity_model_payloads("Identity", 3)})
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
    identity_calls = [c for c in fake_client.calls if c["operation"] == "generate_identity_models"]
    assert len(identity_calls) == 3
    assert all(call["user_payload"]["count"] == 1 for call in identity_calls)
    prompt = fake_client.calls[0]["system_prompt"]
    assert "risk_boundary must be a JSON array of non-empty strings, never a plain string." in prompt
    assert "every models[i].risk_boundary is an array type" in prompt
    _close_db(db)


def test_generate_identity_models_supports_count_five(monkeypatch, tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    fake_client = _FakeLLMClient({"generate_identity_models": _identity_model_payloads("Count5", 5)})
    monkeypatch.setattr(identity_service, "get_llm_client", lambda: fake_client)

    models = identity_service.generate_identity_models(
        db=db,
        user_id=user_id,
        session_id=None,
        capability_profile={"skill_stack": ["python"]},
        count=5,
    )

    assert len(models) == 5
    identity_calls = [c for c in fake_client.calls if c["operation"] == "generate_identity_models"]
    assert len(identity_calls) == 5
    assert all(call["user_payload"]["count"] == 1 for call in identity_calls)
    _close_db(db)


def test_generate_identity_models_replaces_previous_batch(monkeypatch, tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    fake_client = _FakeLLMClient(
        {
            "generate_identity_models": [
                *_identity_model_payloads("Batch1", 3),
                *_identity_model_payloads("Batch2", 3),
            ]
        }
    )
    monkeypatch.setattr(identity_service, "get_llm_client", lambda: fake_client)

    first_batch = identity_service.generate_identity_models(
        db=db,
        user_id=user_id,
        session_id=None,
        capability_profile={"skill_stack": ["python"]},
        count=3,
    )
    first_ids = {model.id for model in first_batch}
    second_batch = identity_service.generate_identity_models(
        db=db,
        user_id=user_id,
        session_id=None,
        capability_profile={"skill_stack": ["python"]},
        count=3,
    )
    current_models = identity_service.get_user_identity_models(db, user_id)

    second_ids = {model.id for model in second_batch}
    current_ids = {model.id for model in current_models}

    assert len(current_models) == 3
    assert current_ids == second_ids
    assert first_ids.isdisjoint(current_ids)
    assert all(model.title.startswith("Batch2") for model in current_models)
    _close_db(db)


def test_generate_identity_models_clears_previous_selection_and_unlinks_dependencies(
    monkeypatch,
    tmp_path,
) -> None:
    db, user_id = _make_db_session(tmp_path)
    fake_client = _FakeLLMClient(
        {
            "generate_identity_models": [
                *_identity_model_payloads("Batch1", 3),
                *_identity_model_payloads("Batch2", 3),
            ]
        }
    )
    monkeypatch.setattr(identity_service, "get_llm_client", lambda: fake_client)

    first_batch = identity_service.generate_identity_models(
        db=db,
        user_id=user_id,
        session_id=None,
        capability_profile={"skill_stack": ["python"]},
        count=3,
    )

    identity_service.select_identity(
        db=db,
        user_id=user_id,
        primary_identity_id=first_batch[0].id,
        backup_identity_id=first_batch[1].id,
    )

    constitution = PersonaConstitution(user_id=user_id, identity_model_id=first_batch[0].id)
    boundary = RiskBoundaryItem(user_id=user_id, identity_model_id=first_batch[0].id)
    launch_kit = LaunchKit(user_id=user_id, identity_model_id=first_batch[0].id)
    check = ConsistencyCheck(
        user_id=user_id,
        identity_model_id=first_batch[0].id,
        draft_text="test draft",
    )
    db.add_all([constitution, boundary, launch_kit, check])
    db.commit()

    constitution_id = constitution.id
    boundary_id = boundary.id
    launch_kit_id = launch_kit.id
    check_id = check.id
    old_ids = {model.id for model in first_batch}

    second_batch = identity_service.generate_identity_models(
        db=db,
        user_id=user_id,
        session_id=None,
        capability_profile={"skill_stack": ["python"]},
        count=3,
    )
    second_ids = {model.id for model in second_batch}

    remaining_old_count = (
        db.query(IdentityModel).filter(IdentityModel.id.in_(old_ids)).count()
    )
    selection_count = db.query(IdentitySelection).filter(IdentitySelection.user_id == user_id).count()
    refreshed_constitution = (
        db.query(PersonaConstitution).filter(PersonaConstitution.id == constitution_id).first()
    )
    refreshed_boundary = db.query(RiskBoundaryItem).filter(RiskBoundaryItem.id == boundary_id).first()
    refreshed_launch_kit = db.query(LaunchKit).filter(LaunchKit.id == launch_kit_id).first()
    refreshed_check = db.query(ConsistencyCheck).filter(ConsistencyCheck.id == check_id).first()
    current_models = identity_service.get_user_identity_models(db, user_id)

    assert len(second_batch) == 3
    assert remaining_old_count == 0
    assert selection_count == 0
    assert refreshed_constitution is not None
    assert refreshed_boundary is not None
    assert refreshed_launch_kit is not None
    assert refreshed_check is not None
    assert refreshed_constitution.identity_model_id is None
    assert refreshed_boundary.identity_model_id is None
    assert refreshed_launch_kit.identity_model_id is None
    assert refreshed_check.identity_model_id is None
    assert {model.id for model in current_models} == second_ids
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
    prompt = fake_client.calls[0]["system_prompt"]
    assert "Return strict JSON only." in prompt
    assert "Context alignment constraints:" in prompt
    _close_db(db)


def test_generate_launch_kit_injects_context_bundle_from_saved_records(monkeypatch, tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    fake_client = _FakeLLMClient({"generate_launch_kit": _valid_launch_kit_payload()})
    monkeypatch.setattr(launch_kit_service, "get_llm_client", lambda: fake_client)

    session = OnboardingSession(user_id=user_id, status="completed", questionnaire_responses="{}")
    db.add(session)
    db.flush()
    profile = CapabilityProfile(
        session_id=session.id,
        user_id=user_id,
        skill_stack_json=json.dumps(["python", "writing"], ensure_ascii=False),
        interest_energy_curve_json=json.dumps([{"topic": "growth"}], ensure_ascii=False),
        cognitive_style="structured",
        value_boundaries_json=json.dumps(["no fake claims"], ensure_ascii=False),
        risk_tolerance=2,
        time_investment_hours=6,
    )
    identity = IdentityModel(
        user_id=user_id,
        session_id=session.id,
        title="Growth Coach",
        target_audience_pain="Inconsistent publishing",
        content_pillars_json=json.dumps(["pillar-1", "pillar-2", "pillar-3"], ensure_ascii=False),
        tone_keywords_json=json.dumps(["clear", "calm"], ensure_ascii=False),
        tone_examples_json=json.dumps(["e1", "e2", "e3", "e4", "e5"], ensure_ascii=False),
        long_term_views_json=json.dumps(["v1", "v2", "v3", "v4", "v5"], ensure_ascii=False),
        differentiation="Evidence-first workflow",
        growth_path_0_3m="Publish weekly",
        growth_path_3_12m="Build products",
        monetization_validation_order_json=json.dumps(["lead", "pilot"], ensure_ascii=False),
        risk_boundary_json=json.dumps(["no guarantee claims"], ensure_ascii=False),
    )
    db.add_all([profile, identity])
    db.flush()
    selection = IdentitySelection(user_id=user_id, primary_identity_id=identity.id, backup_identity_id=None)
    constitution = PersonaConstitution(
        user_id=user_id,
        identity_model_id=identity.id,
        common_words_json=json.dumps(["clarity", "system", "evidence"], ensure_ascii=False),
        forbidden_words_json=json.dumps(["guarantee", "overnight", "secret"], ensure_ascii=False),
        sentence_preferences_json=json.dumps(["one claim", "one proof", "one action"], ensure_ascii=False),
        moat_positions_json=json.dumps(["truthful", "repeatable", "ethical"], ensure_ascii=False),
        narrative_mainline="Build repeatable growth systems.",
        growth_arc_template="Problem -> Method -> Proof",
        version=1,
    )
    db.add_all([selection, constitution])
    db.flush()
    boundary = RiskBoundaryItem(
        user_id=user_id,
        identity_model_id=identity.id,
        constitution_id=constitution.id,
        risk_level=4,
        boundary_type="platform",
        statement="Do not claim guaranteed outcomes.",
        source="user_input",
    )
    db.add(boundary)
    db.commit()

    kit = launch_kit_service.generate_launch_kit(db=db, user_id=user_id)

    assert kit.identity_model_id == identity.id
    assert kit.constitution_id == constitution.id
    payload = fake_client.calls[0]["user_payload"]
    context_bundle = payload["context_bundle"]
    resolution_meta = context_bundle["resolution_meta"]
    assert resolution_meta["identity_model_source"] == "selection"
    assert resolution_meta["persona_constitution_source"] == "identity"
    assert resolution_meta["capability_profile_source"] == "session"
    assert resolution_meta["risk_boundaries_source"] == "constitution"
    assert isinstance(context_bundle["identity_model"]["content_pillars"], list)
    assert len(context_bundle["identity_model"]["tone_examples"]) <= 3
    assert len(context_bundle["risk_boundaries"]) <= 6
    _close_db(db)


def test_generate_launch_kit_resolves_missing_constitution_id_from_identity(monkeypatch, tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    fake_client = _FakeLLMClient({"generate_launch_kit": _valid_launch_kit_payload()})
    monkeypatch.setattr(launch_kit_service, "get_llm_client", lambda: fake_client)

    identity = IdentityModel(user_id=user_id, title="Resolver Identity")
    db.add(identity)
    db.flush()
    constitution = PersonaConstitution(
        user_id=user_id,
        identity_model_id=identity.id,
        common_words_json=json.dumps(["a", "b", "c"], ensure_ascii=False),
        forbidden_words_json=json.dumps(["x", "y", "z"], ensure_ascii=False),
        sentence_preferences_json=json.dumps(["p1", "p2", "p3"], ensure_ascii=False),
        moat_positions_json=json.dumps(["m1", "m2", "m3"], ensure_ascii=False),
        narrative_mainline="Mainline",
        growth_arc_template="Arc",
        version=1,
    )
    db.add(constitution)
    db.commit()

    kit = launch_kit_service.generate_launch_kit(
        db=db,
        user_id=user_id,
        identity_model_id=identity.id,
    )

    assert kit.constitution_id == constitution.id
    resolution_meta = fake_client.calls[0]["user_payload"]["context_bundle"]["resolution_meta"]
    assert resolution_meta["persona_constitution_source"] == "identity"
    _close_db(db)


def test_generate_launch_kit_fallbacks_when_ids_invalid_or_missing(monkeypatch, tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    fake_client = _FakeLLMClient({"generate_launch_kit": _valid_launch_kit_payload()})
    monkeypatch.setattr(launch_kit_service, "get_llm_client", lambda: fake_client)

    latest_identity = IdentityModel(user_id=user_id, title="Latest Identity")
    db.add(latest_identity)
    db.flush()
    related_constitution = PersonaConstitution(
        user_id=user_id,
        identity_model_id=latest_identity.id,
        common_words_json=json.dumps(["a", "b", "c"], ensure_ascii=False),
        forbidden_words_json=json.dumps(["x", "y", "z"], ensure_ascii=False),
        sentence_preferences_json=json.dumps(["p1", "p2", "p3"], ensure_ascii=False),
        moat_positions_json=json.dumps(["m1", "m2", "m3"], ensure_ascii=False),
        narrative_mainline="Mainline",
        growth_arc_template="Arc",
        version=1,
    )
    db.add(related_constitution)
    db.commit()

    kit = launch_kit_service.generate_launch_kit(
        db=db,
        user_id=user_id,
        identity_model_id="missing-identity",
        constitution_id="missing-constitution",
    )

    assert kit.identity_model_id == latest_identity.id
    assert kit.constitution_id == related_constitution.id
    resolution_meta = fake_client.calls[0]["user_payload"]["context_bundle"]["resolution_meta"]
    assert resolution_meta["identity_model_source"] == "latest"
    assert resolution_meta["persona_constitution_source"] == "identity"
    _close_db(db)


def test_generate_launch_kit_without_any_context_still_generates_generic_output(
    monkeypatch,
    tmp_path,
) -> None:
    db, user_id = _make_db_session(tmp_path)
    fake_client = _FakeLLMClient({"generate_launch_kit": _valid_launch_kit_payload()})
    monkeypatch.setattr(launch_kit_service, "get_llm_client", lambda: fake_client)

    kit = launch_kit_service.generate_launch_kit(db=db, user_id=user_id)

    assert kit.identity_model_id is None
    assert kit.constitution_id is None
    resolution_meta = fake_client.calls[0]["user_payload"]["context_bundle"]["resolution_meta"]
    assert resolution_meta["identity_model_source"] == "none"
    assert resolution_meta["persona_constitution_source"] == "none"
    assert resolution_meta["capability_profile_source"] == "none"
    assert resolution_meta["risk_boundaries_source"] == "none"
    assert fake_client.calls[0]["user_payload"]["context_bundle"]["risk_boundaries"] == []
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
    assert "You are repairing an invalid 7-day launch kit JSON." in fake_client.calls[1]["system_prompt"]
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
    payload = _identity_model_payload("Identity", "A")
    payload["models"][0].pop("differentiation")
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


def test_generate_identity_models_fails_without_partial_persist_when_one_candidate_invalid(
    monkeypatch,
    tmp_path,
) -> None:
    db, user_id = _make_db_session(tmp_path)
    invalid_payload = _identity_model_payload("Batch", "B")
    invalid_payload["models"][0].pop("differentiation")
    fake_client = _FakeLLMClient(
        {
            "generate_identity_models": [
                _identity_model_payload("Batch", "A"),
                invalid_payload,
                _identity_model_payload("Batch", "C"),
            ]
        }
    )
    monkeypatch.setattr(identity_service, "get_llm_client", lambda: fake_client)

    with pytest.raises(LLMServiceError):
        identity_service.generate_identity_models(
            db=db,
            user_id=user_id,
            session_id=None,
            capability_profile={},
            count=3,
        )

    persisted = db.query(IdentityModel).filter(IdentityModel.user_id == user_id).count()
    assert persisted == 0
    _close_db(db)
