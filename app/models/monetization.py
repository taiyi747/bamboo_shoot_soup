"""V1 monetization map models."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _new_id() -> str:
    return str(uuid4())


class MonetizationMap(Base):
    """Monetization route map."""

    __tablename__ = "monetization_maps"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    identity_model_id: Mapped[str | None] = mapped_column(
        String(length=36),
        ForeignKey("identity_models.id"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(length=200), nullable=False)
    status: Mapped[str] = mapped_column(String(length=30), nullable=False, default="generated")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    week_nodes: Mapped[list["MonetizationWeekNode"]] = relationship(
        "MonetizationWeekNode",
        back_populates="map",
        order_by="MonetizationWeekNode.week_no.asc()",
    )


class MonetizationWeekNode(Base):
    """Weekly task node in a monetization map."""

    __tablename__ = "monetization_week_nodes"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    map_id: Mapped[str] = mapped_column(
        String(length=36),
        ForeignKey("monetization_maps.id"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    week_no: Mapped[int] = mapped_column(Integer, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False, default="")
    expected_output: Mapped[str] = mapped_column(Text, nullable=False, default="")
    validation_goal: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(length=30), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    map: Mapped["MonetizationMap"] = relationship("MonetizationMap", back_populates="week_nodes")
