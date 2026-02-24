from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

import app.main as main_module
import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User


@dataclass
class ApiTestContext:
    client: TestClient
    session_local: sessionmaker
    user_id: str


def _build_sqlite_engine(db_path: Path) -> Engine:
    return create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )


@pytest.fixture()
def api_context(monkeypatch, tmp_path) -> Iterator[ApiTestContext]:
    # API tests use local sqlite and bypass startup LLM preflight.
    monkeypatch.setattr(main_module, "ensure_llm_ready", lambda: None)

    db_path = tmp_path / "api_tests.db"
    engine = _build_sqlite_engine(db_path)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )

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
    try:
        yield ApiTestContext(client=client, session_local=SessionLocal, user_id=user_id)
    finally:
        client.close()
        main_module.app.dependency_overrides.clear()
        engine.dispose()


@pytest.fixture()
def client(api_context: ApiTestContext) -> TestClient:
    return api_context.client


@pytest.fixture()
def user_id(api_context: ApiTestContext) -> str:
    return api_context.user_id


@pytest.fixture()
def session_local(api_context: ApiTestContext) -> sessionmaker:
    return api_context.session_local
