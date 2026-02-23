"""Launch kit models - 7 day launch package."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _new_id() -> str:
    return str(uuid4())


class LaunchKit(Base):
    """7-Day Launch Kit container."""

    __tablename__ = "launch_kits"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    identity_model_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("identity_models.id"), nullable=True
    )
    constitution_id: Mapped[str | None] = mapped_column(
        String(length=36), ForeignKey("persona_constitutions.id"), nullable=True
    )

    # Kit metadata
    sustainable_columns_json: Mapped[str] = mapped_column(Text, default="[]")  # 3个可持续栏目
    growth_experiment_suggestion_json: Mapped[str] = mapped_column(Text, default="[]")  # 增长实验建议

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    days: Mapped[list["LaunchKitDay"]] = relationship(
        "LaunchKitDay", back_populates="kit", order_by="LaunchKitDay.day_no"
    )


class LaunchKitDay(Base):
    """Single day in 7-Day Launch Kit."""

    __tablename__ = "launch_kit_days"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    kit_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("launch_kits.id"), nullable=False
    )

    day_no: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-7
    theme: Mapped[str] = mapped_column(String(200), default="")  # 每日主题
    draft_or_outline: Mapped[str] = mapped_column(Text, default="")  # 草稿或大纲
    opening_text: Mapped[str] = mapped_column(Text, default="")  # 开头文本

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    kit: Mapped["LaunchKit"] = relationship("LaunchKit", back_populates="days")
