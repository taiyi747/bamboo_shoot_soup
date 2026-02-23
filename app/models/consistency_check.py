"""Consistency check and event log models."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _new_id() -> str:
    return str(uuid4())


class ConsistencyCheck(Base):
    """Draft consistency check results."""

    __tablename__ = "consistency_checks"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    identity_model_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("identity_models.id"), nullable=True
    )
    constitution_id: Mapped[str | None] = mapped_column(
        String(length=36), ForeignKey("persona_constitutions.id"), nullable=True
    )

    # Input
    draft_text: Mapped[str] = mapped_column(Text, default="")

    # Output per product-spec 2.6
    deviation_items_json: Mapped[str] = mapped_column(Text, default="[]")  # 偏离项
    deviation_reasons_json: Mapped[str] = mapped_column(Text, default="[]")  # 偏离原因
    suggestions_json: Mapped[str] = mapped_column(Text, default="[]")  # 修改建议

    # Risk handling per product-spec 2.6
    risk_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_warning: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class EventLog(Base):
    """Event log for analytics and tracking (product-spec 2.8)."""

    __tablename__ = "event_logs"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)

    # Event fields per product-spec 2.8
    event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    stage: Mapped[str] = mapped_column(String(10), nullable=False)  # MVP/V1/V2
    identity_model_id: Mapped[str | None] = mapped_column(
        String(length=36), nullable=True
    )
    payload_json: Mapped[str] = mapped_column(Text, default="{}")

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
