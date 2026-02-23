from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _build_alembic_config(database_url: str) -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _table_names(database_url: str) -> list[str]:
    engine = create_engine(database_url)
    try:
        return inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_upgrade_and_downgrade(tmp_path: Path) -> None:
    db_path = tmp_path / "migration_smoke.db"
    database_url = f"sqlite:///{db_path.as_posix()}"
    config = _build_alembic_config(database_url)

    command.upgrade(config, "head")
    assert "users" in _table_names(database_url)

    command.downgrade(config, "base")
    assert "users" not in _table_names(database_url)
