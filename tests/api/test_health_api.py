from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

import app.main as main_module
from app.db.session import get_db


class _BrokenSession:
    def execute(self, *_args, **_kwargs):
        raise SQLAlchemyError("db down")


def test_health_returns_503_when_database_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "ensure_llm_ready", lambda: None)

    def _broken_get_db():
        yield _BrokenSession()

    main_module.app.dependency_overrides[get_db] = _broken_get_db
    try:
        with TestClient(main_module.app) as client:
            response = client.get("/health")
    finally:
        main_module.app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"detail": "database unavailable"}
