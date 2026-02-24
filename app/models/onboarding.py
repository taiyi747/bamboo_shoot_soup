"""Onboarding 模型：问卷会话与能力画像。"""

import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.json_fields import parse_json_array, parse_json_object


def _new_id() -> str:
    """生成 UUID 主键。"""
    return str(uuid4())


class OnboardingSession(Base):
    """诊断问卷会话。"""

    __tablename__ = "onboarding_sessions"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="in_progress")  # in_progress/completed
    questionnaire_responses: Mapped[str] = mapped_column(Text, default="{}")  # JSON 文本
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 一对一能力画像（完成问卷后生成）。
    capability_profile: Mapped["CapabilityProfile | None"] = relationship(
        "CapabilityProfile",
        back_populates="session",
        uselist=False,
    )

    @property
    def questionnaire(self) -> dict:
        return parse_json_object(self.questionnaire_responses)


class CapabilityProfile(Base):
    """能力画像：承载六个关键维度的结构化结果。"""

    __tablename__ = "capability_profiles"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    session_id: Mapped[str] = mapped_column(
        String(length=36),
        ForeignKey("onboarding_sessions.id"),
        nullable=False,
        unique=True,
    )
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)

    # 六维画像字段：列表结构使用 JSON 文本存储。
    skill_stack_json: Mapped[str] = mapped_column(Text, default="[]")
    interest_energy_curve_json: Mapped[str] = mapped_column(Text, default="[]")
    cognitive_style: Mapped[str] = mapped_column(String(500), default="")
    value_boundaries_json: Mapped[str] = mapped_column(Text, default="[]")
    risk_tolerance: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    time_investment_hours: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    session: Mapped["OnboardingSession"] = relationship(
        "OnboardingSession",
        back_populates="capability_profile",
    )

    @property
    def skill_stack(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.skill_stack_json)]

    @property
    def interest_energy_curve(self) -> list[dict]:
        items = parse_json_array(self.interest_energy_curve_json)
        return [item for item in items if isinstance(item, dict)]

    @property
    def value_boundaries(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.value_boundaries_json)]
