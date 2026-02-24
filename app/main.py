"""FastAPI 应用入口与启动阶段校验。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import v1_router
from app.api.v1.health import router as health_router
from app.core.config import get_settings
from app.db.migrations import upgrade_database_to_head
from app.services.llm_client import ensure_llm_ready

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Run startup checks before serving requests."""
    initialize_database()
    validate_runtime_configuration()
    yield


def initialize_database() -> None:
    """Compatibility entrypoint for startup migration checks."""
    try:
        upgrade_database_to_head()
    except Exception as exc:
        raise RuntimeError(
            f"Application startup failed due to database migration error: {exc}"
        ) from exc


def validate_runtime_configuration() -> None:
    """Compatibility entrypoint for startup LLM checks."""
    try:
        ensure_llm_ready()
    except Exception as exc:
        raise RuntimeError(
            f"Application startup failed due to invalid LLM configuration: {exc}"
        ) from exc


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(v1_router)
