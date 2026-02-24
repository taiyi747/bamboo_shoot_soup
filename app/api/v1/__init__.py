"""v1 API router assembly."""

from fastapi import APIRouter

from app.api.v1.consistency.routes import router as consistency_router
from app.api.v1.events.routes import router as events_router
from app.api.v1.identity.routes import router as identity_router
from app.api.v1.identity.routes import selection_router
from app.api.v1.launch_kit.routes import router as launch_kit_router
from app.api.v1.onboarding.routes import router as onboarding_router
from app.api.v1.persona.routes import risk_router
from app.api.v1.persona.routes import router as persona_router
from app.api.v1.users.routes import router as users_router

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(users_router)
v1_router.include_router(onboarding_router)
v1_router.include_router(identity_router)
v1_router.include_router(selection_router)
v1_router.include_router(persona_router)
v1_router.include_router(risk_router)
v1_router.include_router(launch_kit_router)
v1_router.include_router(consistency_router)
v1_router.include_router(events_router)
