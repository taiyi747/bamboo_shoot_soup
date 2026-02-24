"""User API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserResponse
from app.services import user as user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse)
def create_user(db: Session = Depends(get_db)) -> UserResponse:
    """Create a user for API testing and local flows."""
    return user_service.create_user(db)
