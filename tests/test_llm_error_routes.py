from __future__ import annotations

import json
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

import app.main as main_module
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.services import consistency_check as consistency_service
from app.services import identity_model as identity_service
from app.services import launch_kit as launch_kit_service
from app.services import persona as persona_service
from app.services.llm_client import LLMServiceError


def _create_test_client(monkeypatch, tmp_path) -> tuple[TestClient, str, Engine]:
    monkeypatch.setattr(main_module, "ensure_llm_ready", lambda: None)

    db_path = tmp_path / "route_tests.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)

    seed_db = SessionLocal()
    user = User()
    seed_db.add(user)
    seed_db.commit()
    seed_db.refresh(user)
    user_id = user.id
    seed_db.close()

    def _override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    main_module.app.dependency_overrides[get_db] = _override_get_db
    client = TestClient(main_module.app)
    return client, user_id, engine


def _assert_error_detail_fields(detail: dict) -> None:
    assert set(detail.keys()) == {
        "code",
        "message",
        "operation",
        "provider_status",
        "provider_request_id",
        "retryable",
        "attempts",
    }


def test_identity_route_returns_structured_502(monkeypatch, tmp_path) -> None:
    client, user_id, engine = _create_test_client(monkeypatch, tmp_path)
    try:
        def _raise_error(*_args, **_kwargs):
            raise LLMServiceError(
                code="LLM_INVALID_RESPONSE",
                message="response is invalid",
                operation="generate_identity_models",
                provider_status=502,
                provider_request_id="req-identity",
                retryable=True,
                attempts=2,
            )

        monkeypatch.setattr(identity_service, "generate_identity_models", _raise_error)
        response = client.post(
            "/v1/identity-models/generate",
            json={"user_id": user_id, "capability_profile": {}, "count": 3},
        )
        assert response.status_code == 502
        _assert_error_detail_fields(response.json()["detail"])
    finally:
        client.close()
        main_module.app.dependency_overrides.clear()
        engine.dispose()


def test_persona_route_returns_structured_502(monkeypatch, tmp_path) -> None:
    client, user_id, engine = _create_test_client(monkeypatch, tmp_path)
    try:
        def _raise_error(*_args, **_kwargs):
            raise LLMServiceError(
                code="LLM_SCHEMA_VALIDATION_FAILED",
                message="schema invalid",
                operation="generate_constitution",
                provider_status=502,
                provider_request_id="req-persona",
                retryable=False,
                attempts=1,
            )

        monkeypatch.setattr(persona_service, "generate_constitution", _raise_error)
        response = client.post(
            "/v1/persona-constitutions/generate",
            json={"user_id": user_id},
        )
        assert response.status_code == 502
        _assert_error_detail_fields(response.json()["detail"])
    finally:
        client.close()
        main_module.app.dependency_overrides.clear()
        engine.dispose()


def test_launch_kit_route_returns_structured_502(monkeypatch, tmp_path) -> None:
    client, user_id, engine = _create_test_client(monkeypatch, tmp_path)
    try:
        def _raise_error(*_args, **_kwargs):
            raise LLMServiceError(
                code="LLM_UPSTREAM_HTTP_ERROR",
                message="upstream failed",
                operation="generate_launch_kit",
                provider_status=503,
                provider_request_id="req-launch",
                retryable=True,
                attempts=3,
            )

        monkeypatch.setattr(launch_kit_service, "generate_launch_kit", _raise_error)
        response = client.post(
            "/v1/launch-kits/generate",
            json={"user_id": user_id},
        )
        assert response.status_code == 502
        _assert_error_detail_fields(response.json()["detail"])
    finally:
        client.close()
        main_module.app.dependency_overrides.clear()
        engine.dispose()


def test_consistency_route_returns_structured_502(monkeypatch, tmp_path) -> None:
    client, user_id, engine = _create_test_client(monkeypatch, tmp_path)
    try:
        def _raise_error(*_args, **_kwargs):
            raise LLMServiceError(
                code="LLM_UPSTREAM_TIMEOUT",
                message="timeout",
                operation="check_consistency",
                provider_status=None,
                provider_request_id="req-consistency",
                retryable=True,
                attempts=3,
            )

        monkeypatch.setattr(consistency_service, "check_consistency", _raise_error)
        response = client.post(
            "/v1/consistency-checks",
            json={"user_id": user_id, "draft_text": "test draft"},
        )
        assert response.status_code == 502
        _assert_error_detail_fields(response.json()["detail"])
    finally:
        client.close()
        main_module.app.dependency_overrides.clear()
        engine.dispose()


def test_consistency_route_returns_degraded_payload_and_event(monkeypatch, tmp_path) -> None:
    client, user_id, engine = _create_test_client(monkeypatch, tmp_path)
    try:
        def _degraded_result(*_args, **_kwargs):
            check = SimpleNamespace(
                id="check-degraded",
                deviation_items_json='["未发现明显偏离（建议人工复核）"]',
                deviation_reasons_json='["LLM 结构化输出不稳定，已使用降级结果，请人工复核。"]',
                suggestions_json='["请人工复核草稿后再发布。"]',
                risk_triggered=False,
                risk_warning="",
            )
            return consistency_service.ConsistencyCheckExecutionResult(
                check=check,
                degraded=True,
                degrade_reason="llm_schema_retry_exhausted",
                schema_repair_attempts=2,
            )

        monkeypatch.setattr(consistency_service, "check_consistency", _degraded_result)
        response = client.post(
            "/v1/consistency-checks",
            json={"user_id": user_id, "draft_text": "test draft"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["degraded"] is True
        assert body["degrade_reason"] == "llm_schema_retry_exhausted"
        assert body["schema_repair_attempts"] == 2

        events_response = client.get(f"/v1/events/users/{user_id}", params={"limit": 20})
        assert events_response.status_code == 200
        events = events_response.json()
        consistency_events = [e for e in events if e["event_name"] == "consistency_check_triggered"]
        assert consistency_events
        payload = json.loads(consistency_events[0]["payload_json"])
        assert payload["degraded"] is True
        assert payload["degrade_reason"] == "llm_schema_retry_exhausted"
        assert payload["schema_repair_attempts"] == 2
    finally:
        client.close()
        main_module.app.dependency_overrides.clear()
        engine.dispose()


def test_identity_route_strict_mode_keeps_502_for_upstream_400(monkeypatch, tmp_path) -> None:
    client, user_id, engine = _create_test_client(monkeypatch, tmp_path)
    try:
        def _raise_error(*_args, **_kwargs):
            raise LLMServiceError(
                code="LLM_UPSTREAM_HTTP_ERROR",
                message="response_format is not supported",
                operation="generate_identity_models",
                provider_status=400,
                provider_request_id="req-400",
                retryable=False,
                attempts=1,
            )

        monkeypatch.setattr(identity_service, "generate_identity_models", _raise_error)
        response = client.post(
            "/v1/identity-models/generate",
            json={"user_id": user_id, "capability_profile": {}, "count": 3},
        )
        assert response.status_code == 502
        detail = response.json()["detail"]
        _assert_error_detail_fields(detail)
        assert detail["provider_status"] == 400
        assert detail["retryable"] is False
        assert detail["attempts"] == 1
    finally:
        client.close()
        main_module.app.dependency_overrides.clear()
        engine.dispose()
