from __future__ import annotations

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


def _create_test_client(monkeypatch, tmp_path) -> tuple[TestClient, str, Engine]:
    monkeypatch.setattr(main_module, "ensure_llm_ready", lambda: None)

    db_path = tmp_path / "route_params.db"
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


def test_identity_route_passes_expected_parameters(monkeypatch, tmp_path) -> None:
    client, user_id, engine = _create_test_client(monkeypatch, tmp_path)
    captured: dict = {}
    try:
        def _fake_generate(**kwargs):
            captured.update(kwargs)
            return [
                SimpleNamespace(
                    id="id-1",
                    title="title",
                    target_audience_pain="pain",
                    differentiation="diff",
                    is_primary=False,
                    is_backup=False,
                )
            ]

        monkeypatch.setattr(identity_service, "generate_identity_models", _fake_generate)
        response = client.post(
            "/v1/identity-models/generate",
            json={
                "user_id": user_id,
                "session_id": None,
                "capability_profile": {"skill_stack": ["python"]},
                "count": 3,
            },
        )
        assert response.status_code == 200
        assert captured["user_id"] == user_id
        assert captured["session_id"] is None
        assert captured["count"] == 3
        assert captured["capability_profile"] == {"skill_stack": ["python"]}
    finally:
        client.close()
        main_module.app.dependency_overrides.clear()
        engine.dispose()


def test_persona_route_passes_expected_parameters(monkeypatch, tmp_path) -> None:
    client, user_id, engine = _create_test_client(monkeypatch, tmp_path)
    captured: dict = {}
    try:
        def _fake_generate(**kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                id="constitution-1",
                user_id=user_id,
                version=1,
                narrative_mainline="mainline",
            )

        monkeypatch.setattr(persona_service, "generate_constitution", _fake_generate)
        response = client.post(
            "/v1/persona-constitutions/generate",
            json={
                "user_id": user_id,
                "identity_model_id": "identity-1",
                "common_words": ["a"],
                "forbidden_words": ["b"],
            },
        )
        assert response.status_code == 200
        assert captured["user_id"] == user_id
        assert captured["identity_model_id"] == "identity-1"
        assert captured["common_words"] == ["a"]
        assert captured["forbidden_words"] == ["b"]
    finally:
        client.close()
        main_module.app.dependency_overrides.clear()
        engine.dispose()


def test_launch_kit_route_passes_expected_parameters(monkeypatch, tmp_path) -> None:
    client, user_id, engine = _create_test_client(monkeypatch, tmp_path)
    captured: dict = {}
    try:
        def _fake_generate(**kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                id="kit-1",
                user_id=user_id,
                days=[SimpleNamespace(day_no=1, theme="t", opening_text="o")],
            )

        monkeypatch.setattr(launch_kit_service, "generate_launch_kit", _fake_generate)
        response = client.post(
            "/v1/launch-kits/generate",
            json={
                "user_id": user_id,
                "identity_model_id": "identity-2",
                "constitution_id": "constitution-2",
                "sustainable_columns": ["col-1"],
                "growth_experiment_suggestion": [{"name": "exp"}],
            },
        )
        assert response.status_code == 200
        assert captured["user_id"] == user_id
        assert captured["identity_model_id"] == "identity-2"
        assert captured["constitution_id"] == "constitution-2"
        assert captured["sustainable_columns"] == ["col-1"]
        assert captured["growth_experiment_suggestion"] == [{"name": "exp"}]
    finally:
        client.close()
        main_module.app.dependency_overrides.clear()
        engine.dispose()


def test_consistency_route_passes_expected_parameters(monkeypatch, tmp_path) -> None:
    client, user_id, engine = _create_test_client(monkeypatch, tmp_path)
    captured: dict = {}
    try:
        def _fake_check(**kwargs):
            captured.update(kwargs)
            check = SimpleNamespace(
                id="check-1",
                deviation_items_json='["item-1"]',
                deviation_reasons_json='["reason-1"]',
                suggestions_json='["suggestion-1"]',
                risk_triggered=False,
                risk_warning="",
            )
            return consistency_service.ConsistencyCheckExecutionResult(
                check=check,
                degraded=True,
                degrade_reason="llm_schema_retry_exhausted",
                schema_repair_attempts=2,
            )

        monkeypatch.setattr(consistency_service, "check_consistency", _fake_check)
        response = client.post(
            "/v1/consistency-checks",
            json={
                "user_id": user_id,
                "identity_model_id": "identity-3",
                "constitution_id": "constitution-3",
                "draft_text": "draft",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["degraded"] is True
        assert body["degrade_reason"] == "llm_schema_retry_exhausted"
        assert body["schema_repair_attempts"] == 2
        assert captured["user_id"] == user_id
        assert captured["identity_model_id"] == "identity-3"
        assert captured["constitution_id"] == "constitution-3"
        assert captured["draft_text"] == "draft"
    finally:
        client.close()
        main_module.app.dependency_overrides.clear()
        engine.dispose()
