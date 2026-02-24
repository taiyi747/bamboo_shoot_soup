"""Users API exports."""

from app.api.v1.users.routes import router as users_router

__all__ = ["users_router"]
