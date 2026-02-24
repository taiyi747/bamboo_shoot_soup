"""v1 API router assembly."""

from fastapi import APIRouter

from app.api.v1.consistency.routes import router as consistency_router
from app.api.v1.content_matrix.routes import router as content_matrix_router
from app.api.v1.events.routes import router as events_router
from app.api.v1.experiments.routes import router as experiments_router
from app.api.v1.identity.routes import router as identity_router
from app.api.v1.identity.routes import selection_router
from app.api.v1.identity_portfolio.routes import router as identity_portfolio_router
from app.api.v1.launch_kit.routes import router as launch_kit_router
from app.api.v1.metrics.routes import router as metrics_router
from app.api.v1.monetization.routes import router as monetization_router
from app.api.v1.onboarding.routes import router as onboarding_router
from app.api.v1.persona.routes import risk_router
from app.api.v1.persona.routes import router as persona_router
from app.api.v1.simulator.routes import router as simulator_router
from app.api.v1.users.routes import router as users_router
from app.api.v1.viewpoint_assets.routes import router as viewpoint_assets_router

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
v1_router.include_router(content_matrix_router)
v1_router.include_router(experiments_router)
v1_router.include_router(monetization_router)
v1_router.include_router(identity_portfolio_router)
v1_router.include_router(metrics_router)
v1_router.include_router(simulator_router)
v1_router.include_router(viewpoint_assets_router)
