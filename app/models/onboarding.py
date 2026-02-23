"""Onboarding models: session and capability profile."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _new_id() -> str:
    return str(uuid4())


class OnboardingSession(Base):
    """Questionnaire session for identity diagnosis."""

    __tablename__ = "onboarding_sessions"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="in_progress")  # in_progress, completed
    questionnaire_responses: Mapped[str] = mapped_column(Text, default="{}")  # JSON
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    capability_profile: Mapped["CapabilityProfile | None"] = relationship(
        "CapabilityProfile", back_populates="session", uselist=False
    )


class CapabilityProfile(Base):
    """User capability profile from diagnosis - six key dimensions."""

    __tablename__ = "capability_profiles"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    session_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("onboarding_sessions.id"), nullable=False, unique=True
    )
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)

    # Six key dimensions (product-spec 2.5 MVP)
    skill_stack_json: Mapped[str] = mapped_column(Text, default="[]")  # 技能栈
    interest_energy_curve_json: Mapped[str] = mapped_column(Text, default="[]")  # 兴趣能量曲线
    cognitive_style: Mapped[str] = mapped_column(String(500), default="")  # 认知风格
    value_boundaries_json: Mapped[str] = mapped_column(Text, default="[]")  # 价值边界
    risk_tolerance: Mapped[int] = mapped_column(Integer, default=3)  # 风险承受度 1-5
    time_investment_hours: Mapped[int] = mapped_column(Integer, default=0)  # 每周时间投入小时

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    session: Mapped["OnboardingSession"] = relationship(
        "OnboardingSession", back_populates="capability_profile"
    )
