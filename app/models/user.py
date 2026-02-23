from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.diagnostic import Diagnostic
    from app.models.identity_model import IdentityModel
    from app.models.launch_kit import LaunchKit
    from app.models.persona_constitution import PersonaConstitution


def _new_user_id() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_user_id)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # === 关系 ===
    diagnostics: Mapped[list["Diagnostic"]] = relationship(
        "Diagnostic", back_populates="user", cascade="all, delete-orphan"
    )
    identity_models: Mapped[list["IdentityModel"]] = relationship(
        "IdentityModel", back_populates="user", cascade="all, delete-orphan"
    )
    persona_constitutions: Mapped[list["PersonaConstitution"]] = relationship(
        "PersonaConstitution", back_populates="user", cascade="all, delete-orphan"
    )
    launch_kits: Mapped[list["LaunchKit"]] = relationship(
        "LaunchKit", back_populates="user", cascade="all, delete-orphan"
    )
