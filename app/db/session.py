"""数据库引擎、Session 工厂与请求级依赖。"""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def ensure_sqlite_directory(database_url: str) -> None:
    """若使用文件型 SQLite，则确保数据库目录存在。"""
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite"):
        return

    database = url.database
    if not database or database == ":memory:" or database.startswith("file:"):
        return

    db_path = Path(database)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)


def _connect_args(database_url: str) -> dict[str, object]:
    """根据数据库驱动构建 connect_args。"""
    url = make_url(database_url)
    if url.drivername.startswith("sqlite"):
        # FastAPI 请求处理可能跨线程，SQLite 需关闭线程检查。
        return {"check_same_thread": False}
    return {}


settings = get_settings()
ensure_sqlite_directory(settings.database_url)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=_connect_args(settings.database_url),
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """提供请求级 Session，并在请求结束后关闭连接。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
