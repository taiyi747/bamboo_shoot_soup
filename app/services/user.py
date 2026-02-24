"""User service."""

from sqlalchemy.orm import Session

from app.models.user import User


def create_user(db: Session) -> User:
    """Create a user and persist it."""
    user = User()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
