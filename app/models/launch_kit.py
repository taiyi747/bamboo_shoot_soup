"""
7天启动包模型 - 7-Day Launch Kit

对应 product-spec 2.3 核心业务对象 7-Day Launch Kit
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _new_id() -> str:
    return str(uuid4())


class LaunchKit(Base):
    """
    7天启动包 - 用户选择身份后的执行指南
    """

    __tablename__ = "launch_kits"

    id: Mapped[str] = mapped_column(
        String(length=36), primary_key=True, default=_new_id
    )
    identity_model_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("identity_models.id"), nullable=False
    )
    persona_constitution_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("persona_constitutions.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("users.id"), nullable=False
    )
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

    # === 7天启动包核心字段 ===
    day_1_theme: Mapped[str] = mapped_column(String(255), nullable=False)
    day_1_content: Mapped[str] = mapped_column(Text, nullable=False)
    day_2_theme: Mapped[str] = mapped_column(String(255), nullable=False)
    day_2_content: Mapped[str] = mapped_column(Text, nullable=False)
    day_3_theme: Mapped[str] = mapped_column(String(255), nullable=False)
    day_3_content: Mapped[str] = mapped_column(Text, nullable=False)
    day_4_theme: Mapped[str] = mapped_column(String(255), nullable=False)
    day_4_content: Mapped[str] = mapped_column(Text, nullable=False)
    day_5_theme: Mapped[str] = mapped_column(String(255), nullable=False)
    day_5_content: Mapped[str] = mapped_column(Text, nullable=False)
    day_6_theme: Mapped[str] = mapped_column(String(255), nullable=False)
    day_6_content: Mapped[str] = mapped_column(Text, nullable=False)
    day_7_theme: Mapped[str] = mapped_column(String(255), nullable=False)
    day_7_content: Mapped[str] = mapped_column(Text, nullable=False)
    sustainable_columns: Mapped[str] = mapped_column(Text, nullable=False)
    growth_experiment: Mapped[str] = mapped_column(Text, nullable=False)

    # === 状态 ===
    is_used: Mapped[bool] = mapped_column(default=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # === 关系 ===
    identity_model: Mapped["IdentityModel"] = relationship("IdentityModel", back_populates="launch_kit")
    persona_constitution: Mapped["PersonaConstitution"] = relationship("PersonaConstitution", back_populates="launch_kit")
    user: Mapped["User"] = relationship("User", back_populates="launch_kits")
