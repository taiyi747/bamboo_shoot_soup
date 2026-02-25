from __future__ import annotations

import copy

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.models.user import User
from app.models.v1_growth import LLMGenerationReplay
from app.services.llm_client import LLMServiceError
from app.services.llm_replay import generate_json_with_replay, load_latest_replay_payload


class _OkClient:
    def __init__(self, payload: dict) -> None:
        self.payload = copy.deepcopy(payload)

    def generate_json(self, *, operation: str, system_prompt: str, user_payload: dict) -> dict:
        del operation, system_prompt, user_payload
        return copy.deepcopy(self.payload)


class _FailClient:
    def generate_json(self, *, operation: str, system_prompt: str, user_payload: dict) -> dict:
        del system_prompt, user_payload
        raise LLMServiceError(
            code="LLM_UPSTREAM_UNAVAILABLE",
            message="upstream unavailable",
            operation=operation,
            retryable=True,
        )


def _make_db_session(tmp_path) -> tuple[Session, str]:
    db_path = tmp_path / "replay_tests.db"
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


def test_replay_fallback_returns_latest_payload_when_upstream_fails(tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    settings = get_settings()
    settings.demo_replay_fallback_enabled = True
    settings.demo_replay_force = False

    operation = "generate_content_matrix"
    user_payload = {"user_id": user_id}
    stored_payload = {"foo": "bar"}

    first = generate_json_with_replay(
        db,
        user_id=user_id,
        operation=operation,
        system_prompt="prompt",
        user_payload=user_payload,
        llm_client=_OkClient(stored_payload),
    )
    assert first.degraded is False
    assert first.payload == stored_payload

    second = generate_json_with_replay(
        db,
        user_id=user_id,
        operation=operation,
        system_prompt="prompt",
        user_payload=user_payload,
        llm_client=_FailClient(),
    )
    assert second.degraded is True
    assert second.degrade_reason == "replay_fallback"
    assert second.payload == stored_payload

    loaded = load_latest_replay_payload(db, user_id=user_id, operation=operation)
    assert loaded == stored_payload
    _close_db(db)


def test_replay_fallback_raises_when_no_replay_exists(tmp_path) -> None:
    db, user_id = _make_db_session(tmp_path)
    settings = get_settings()
    settings.demo_replay_fallback_enabled = True
    settings.demo_replay_force = False

    try:
        generate_json_with_replay(
            db,
            user_id=user_id,
            operation="generate_content_matrix",
            system_prompt="prompt",
            user_payload={"user_id": user_id},
            llm_client=_FailClient(),
        )
        raise AssertionError("expected LLMServiceError")
    except LLMServiceError as error:
        assert error.code == "LLM_UPSTREAM_UNAVAILABLE"

    replay_count = db.query(LLMGenerationReplay).count()
    assert replay_count == 0
    _close_db(db)
