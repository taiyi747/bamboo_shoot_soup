import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _build_alembic_config(database_url: str) -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_alembic_upgrade_keeps_uvicorn_loggers_enabled(tmp_path: Path) -> None:
    db_path = tmp_path / "alembic_logging.db"
    database_url = f"sqlite:///{db_path.as_posix()}"
    config = _build_alembic_config(database_url)

    access_logger = logging.getLogger("uvicorn.access")
    error_logger = logging.getLogger("uvicorn.error")
    access_logger.disabled = False
    error_logger.disabled = False

    command.upgrade(config, "head")

    assert access_logger.disabled is False
    assert error_logger.disabled is False
