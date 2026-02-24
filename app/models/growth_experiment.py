"""V1 growth experiment model."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.utils.json_fields import parse_json_array


def _new_id() -> str:
    return str(uuid4())


class GrowthExperiment(Base):
    """Growth experiment with strict conclusion gate."""

    __tablename__ = "growth_experiments"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    identity_model_id: Mapped[str | None] = mapped_column(
        String(length=36),
        ForeignKey("identity_models.id"),
        nullable=True,
    )
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    variables_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    duration: Mapped[str] = mapped_column(String(length=80), nullable=False, default="")
    result: Mapped[str] = mapped_column(Text, nullable=False, default="")
    conclusion: Mapped[str] = mapped_column(Text, nullable=False, default="")
    next_iteration: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(length=30), nullable=False, default="planned")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def variables(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.variables_json)]
