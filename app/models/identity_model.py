"""Identity model and selection models."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _new_id() -> str:
    return str(uuid4())


class IdentityModel(Base):
    """Identity Model Card - generated 3-5 candidates per user."""

    __tablename__ = "identity_models"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("onboarding_sessions.id"), nullable=True
    )

    # Required fields per product-spec 2.3
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    target_audience_pain: Mapped[str] = mapped_column(Text, default="")
    content_pillars_json: Mapped[str] = mapped_column(Text, default="[]")  # 3-5 pillars
    tone_keywords_json: Mapped[str] = mapped_column(Text, default="[]")  # 关键词
    tone_examples_json: Mapped[str] = mapped_column(Text, default="[]")  # 至少5句示例口吻
    long_term_views_json: Mapped[str] = mapped_column(Text, default="[]")  # 5-10条长期观点
    differentiation: Mapped[str] = mapped_column(Text, default="")  # 差异化定位 - 必填
    growth_path_0_3m: Mapped[str] = mapped_column(Text, default="")
    growth_path_3_12m: Mapped[str] = mapped_column(Text, default="")
    monetization_validation_order_json: Mapped[str] = mapped_column(Text, default="[]")
    risk_boundary_json: Mapped[str] = mapped_column(Text, default="[]")  # 风险与禁区

    # Metadata
    is_primary: Mapped[bool] = mapped_column(default=False)
    is_backup: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class IdentitySelection(Base):
    """User's primary and backup identity selection."""

    __tablename__ = "identity_selections"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)

    primary_identity_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("identity_models.id"), nullable=False
    )
    backup_identity_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("identity_models.id"), nullable=True
    )

    selected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    primary_identity: Mapped["IdentityModel"] = relationship(
        "IdentityModel", foreign_keys=[primary_identity_id]
    )
    backup_identity: Mapped["IdentityModel | None"] = relationship(
        "IdentityModel", foreign_keys=[backup_identity_id]
    )
