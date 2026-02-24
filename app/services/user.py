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


def ensure_user_exists(db: Session, user_id: str) -> User:
    """Ensure a user row exists for a provided ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return user

    user = User(id=user_id)
    db.add(user)
    # Do not commit here; caller controls transaction boundary.
    db.flush()
    return user
