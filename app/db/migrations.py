"""Helpers for bootstrapping database schema with Alembic."""

from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import get_settings
from app.db.session import ensure_sqlite_directory

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _build_alembic_config(database_url: str) -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def upgrade_database_to_head() -> None:
    settings = get_settings()
    ensure_sqlite_directory(settings.database_url)
    config = _build_alembic_config(settings.database_url)
    command.upgrade(config, "head")
