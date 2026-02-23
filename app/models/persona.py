"""Persona constitution and risk boundary models."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _new_id() -> str:
    return str(uuid4())


class PersonaConstitution(Base):
    """Persona Constitution - voice dictionary, moat positions, narrative mainline."""

    __tablename__ = "persona_constitutions"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    identity_model_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("identity_models.id"), nullable=True
    )

    # Required fields per product-spec 2.3
    common_words_json: Mapped[str] = mapped_column(Text, default="[]")  # 常用词
    forbidden_words_json: Mapped[str] = mapped_column(Text, default="[]")  # 禁用词
    sentence_preferences_json: Mapped[str] = mapped_column(Text, default="[]")  # 句式偏好
    moat_positions_json: Mapped[str] = mapped_column(Text, default="[]")  # 观点护城河 3条
    narrative_mainline: Mapped[str] = mapped_column(Text, default="")  # 叙事主线
    growth_arc_template: Mapped[str] = mapped_column(Text, default="")  # 成长Arc

    # Version management
    version: Mapped[int] = mapped_column(Integer, default=1)
    previous_version_id: Mapped[str | None] = mapped_column(
        String(length=36), nullable=True
    )  # Link to previous version

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


class RiskBoundaryItem(Base):
    """Risk and boundary items for an identity."""

    __tablename__ = "risk_boundary_items"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    identity_model_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("identity_models.id"), nullable=True
    )
    constitution_id: Mapped[str | None] = mapped_column(
        String(length=36), ForeignKey("persona_constitutions.id"), nullable=True
    )

    risk_level: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    boundary_type: Mapped[str] = mapped_column(String(50), default="")  # legal, platform, reputational
    statement: Mapped[str] = mapped_column(Text, default="")  # The boundary statement
    source: Mapped[str] = mapped_column(String(100), default="")  # user_input, system_generated

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
