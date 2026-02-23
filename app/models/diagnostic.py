"""
能力画像模型 - 诊断问卷输出

对应 product-spec 2.5 MVP 功能规格 1.1 身份诊断
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _new_id() -> str:
    return str(uuid4())


class Diagnostic(Base):
    """
    诊断记录 - 用户完成问卷后的能力画像

    包含：技能栈、兴趣能量曲线、认知风格、价值边界、风险承受度、时间投入
    """

    __tablename__ = "diagnostics"

    id: Mapped[str] = mapped_column(
        String(length=36), primary_key=True, default=_new_id
    )
    user_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # === 能力画像核心字段 ===
    skill_stack: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    interest_energy_curve: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cognitive_style: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value_boundary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_tolerance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_commitment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_responses: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # === 关系 ===
    user: Mapped["User"] = relationship("User", back_populates="diagnostics")
    identity_models: Mapped[list["IdentityModel"]] = relationship(
        "IdentityModel", back_populates="diagnostic", cascade="all, delete-orphan"
    )
