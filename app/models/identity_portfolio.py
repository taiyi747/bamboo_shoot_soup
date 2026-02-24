"""V1 identity portfolio model."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _new_id() -> str:
    return str(uuid4())


class IdentityPortfolio(Base):
    """Multi-identity portfolio strategy."""

    __tablename__ = "identity_portfolios"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    primary_identity_id: Mapped[str] = mapped_column(
        String(length=36),
        ForeignKey("identity_models.id"),
        nullable=False,
    )
    backup_identity_id: Mapped[str | None] = mapped_column(
        String(length=36),
        ForeignKey("identity_models.id"),
        nullable=True,
    )
    anonymous_identity: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tool_identity: Mapped[str] = mapped_column(Text, nullable=False, default="")
    conflict_avoidance: Mapped[str] = mapped_column(Text, nullable=False, default="")
    asset_reuse_strategy: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
