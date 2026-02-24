"""V2 prepublish simulator model."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.utils.json_fields import parse_json_array


def _new_id() -> str:
    return str(uuid4())


class PrepublishEvaluation(Base):
    """Prepublish evaluation result."""

    __tablename__ = "prepublish_evaluations"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    identity_model_id: Mapped[str | None] = mapped_column(
        String(length=36),
        ForeignKey("identity_models.id"),
        nullable=True,
    )
    platform: Mapped[str] = mapped_column(String(length=50), nullable=False)
    stage_goal: Mapped[str] = mapped_column(String(length=100), nullable=False)
    draft_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    growth_prediction_range: Mapped[str] = mapped_column(String(length=50), nullable=False, default="0.00-0.00")
    controversy_prob: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    brand_risk: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    trust_impact: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recommendation: Mapped[str] = mapped_column(String(length=20), nullable=False, default="改后发")
    trigger_factors_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    rewrite: Mapped[str] = mapped_column(Text, nullable=False, default="")
    manual_confirmation_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    @property
    def trigger_factors(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.trigger_factors_json)]
