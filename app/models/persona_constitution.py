"""
人格宪法模型 - Persona Constitution

对应 product-spec 2.3 核心业务对象 Persona Constitution
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _new_id() -> str:
    return str(uuid4())


class PersonaConstitution(Base):
    """
    人格宪法 - 指导内容创作的人格一致性规则
    """

    __tablename__ = "persona_constitutions"

    id: Mapped[str] = mapped_column(
        String(length=36), primary_key=True, default=_new_id
    )
    identity_model_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("identity_models.id"), nullable=False
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

    # === 人格宪法核心字段 ===
    tone_words_used: Mapped[str] = mapped_column(Text, nullable=False)
    tone_words_forbidden: Mapped[str] = mapped_column(Text, nullable=False)
    tone_sentence_patterns: Mapped[str] = mapped_column(Text, nullable=False)
    viewpoint_fortress: Mapped[str] = mapped_column(Text, nullable=False)
    narrative_mainline: Mapped[str] = mapped_column(Text, nullable=False)
    growth_arc: Mapped[str] = mapped_column(Text, nullable=False)

    # === 版本控制 ===
    version: Mapped[int] = mapped_column(default=1)

    # === 关系 ===
    identity_model: Mapped["IdentityModel"] = relationship("IdentityModel", back_populates="persona_constitution")
    user: Mapped["User"] = relationship("User", back_populates="persona_constitutions")
    launch_kit: Mapped[Optional["LaunchKit"]] = relationship(
        "LaunchKit", back_populates="persona_constitution", uselist=False
    )
