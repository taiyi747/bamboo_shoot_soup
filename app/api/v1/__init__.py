"""Version 1 API routes."""

# Import routers from submodules directly to avoid circular imports
from app.api.v1.onboarding.routes import router as onboarding_router
from app.api.v1.identity.routes import router as identity_router
from app.api.v1.identity.routes import selection_router
from app.api.v1.persona.routes import router as persona_router
from app.api.v1.persona.routes import risk_router
from app.api.v1.launch_kit.routes import router as launch_kit_router
from app.api.v1.consistency.routes import router as consistency_router
from app.api.v1.events.routes import router as events_router

# Main v1 router will include all sub-routers
from fastapi import APIRouter

v1_router = APIRouter(prefix="/v1")

# Include all routers
v1_router.include_router(onboarding_router)
v1_router.include_router(identity_router)
v1_router.include_router(selection_router)
v1_router.include_router(persona_router)
v1_router.include_router(risk_router)
v1_router.include_router(launch_kit_router)
v1_router.include_router(consistency_router)
v1_router.include_router(events_router)
