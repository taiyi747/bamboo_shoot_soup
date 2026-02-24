from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect

import app.main as main_module
from app.core.config import get_settings


def _table_names(database_url: str) -> set[str]:
    engine = create_engine(database_url)
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_startup_runs_database_migrations(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "startup_init.db"
    database_url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setattr(main_module, "ensure_llm_ready", lambda: None)
    get_settings.cache_clear()

    with TestClient(main_module.app):
        pass

    table_names = _table_names(database_url)
    assert "users" in table_names
    assert "event_logs" in table_names
