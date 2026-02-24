"""FastAPI 应用入口与启动阶段校验。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import v1_router
from app.api.v1.health import router as health_router
from app.core.config import get_settings
from app.db.migrations import upgrade_database_to_head
from app.services.llm_client import ensure_llm_ready

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",debug=True,
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


@app.on_event("startup")
def initialize_database() -> None:
    try:
        upgrade_database_to_head()
    except Exception as exc:
        raise RuntimeError(
            f"Application startup failed due to database migration error: {exc}"
        ) from exc


@app.on_event("startup")
def validate_runtime_configuration() -> None:
    # 启动即失败（fail-fast）：避免请求进来后才发现 LLM 配置缺失。
    try:
        ensure_llm_ready()
    except Exception as exc:
        raise RuntimeError(
            f"Application startup failed due to invalid LLM configuration: {exc}"
        ) from exc
