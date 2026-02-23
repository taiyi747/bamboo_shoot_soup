from fastapi import FastAPI

from app.api.v1 import diagnostic, identity_model, launch_kit, persona_constitution, user
from app.api.v1.health import router as health_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

# 注册路由
app.include_router(health_router)
app.include_router(user.router)
app.include_router(diagnostic.router)
app.include_router(identity_model.router)
app.include_router(persona_constitution.router)
app.include_router(launch_kit.router)
