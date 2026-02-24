
"""Identity API exports."""

from app.api.v1.identity.routes import router as identity_router, selection_router

__all__ = ["identity_router", "selection_router"]
