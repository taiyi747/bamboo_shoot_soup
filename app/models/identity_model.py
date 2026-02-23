"""
身份模型卡模型 - Identity Model Card

对应 product-spec 2.3 核心业务对象 Identity Model Card
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _new_id() -> str:
    return str(uuid4())


class IdentityModel(Base):
    """
    身份模型卡 - 系统生成的候选身份方案
    """

    __tablename__ = "identity_models"

    id: Mapped[str] = mapped_column(
        String(length=36), primary_key=True, default=_new_id
    )
    diagnostic_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("diagnostics.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # === 身份模型核心字段 ===
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_audience: Mapped[str] = mapped_column(Text, nullable=False)
    content_pillars: Mapped[str] = mapped_column(Text, nullable=False)
    tone_style: Mapped[str] = mapped_column(Text, nullable=False)
    viewpoint_library: Mapped[str] = mapped_column(Text, nullable=False)
    differentiation: Mapped[str] = mapped_column(Text, nullable=False)
    growth_path: Mapped[str] = mapped_column(Text, nullable=False)
    monetization_path: Mapped[str] = mapped_column(Text, nullable=False)
    risk_boundary: Mapped[str] = mapped_column(Text, nullable=False)

    # === 选择状态 ===
    is_selected_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_selected_backup: Mapped[bool] = mapped_column(Boolean, default=False)
    selected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # === 关系 ===
    diagnostic: Mapped["Diagnostic"] = relationship("Diagnostic", back_populates="identity_models")
    user: Mapped["User"] = relationship("User", back_populates="identity_models")
    persona_constitution: Mapped[Optional["PersonaConstitution"]] = relationship(
        "PersonaConstitution", back_populates="identity_model", uselist=False
    )
    launch_kit: Mapped[Optional["LaunchKit"]] = relationship(
        "LaunchKit", back_populates="identity_model", uselist=False
    )
