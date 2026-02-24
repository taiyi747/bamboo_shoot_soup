"""一致性检查与事件日志模型。"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _new_id() -> str:
    """生成 UUID 主键。"""
    return str(uuid4())


class ConsistencyCheck(Base):
    """草稿一致性检查结果。"""

    __tablename__ = "consistency_checks"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    identity_model_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("identity_models.id"), nullable=True
    )
    constitution_id: Mapped[str | None] = mapped_column(
        String(length=36), ForeignKey("persona_constitutions.id"), nullable=True
    )

    # 输入草稿
    draft_text: Mapped[str] = mapped_column(Text, default="")

    # 输出结果（列表结构使用 JSON 文本）。
    deviation_items_json: Mapped[str] = mapped_column(Text, default="[]")
    deviation_reasons_json: Mapped[str] = mapped_column(Text, default="[]")
    suggestions_json: Mapped[str] = mapped_column(Text, default="[]")

    # 风险信号
    risk_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_warning: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class EventLog(Base):
    """关键事件日志（埋点）。"""

    __tablename__ = "event_logs"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)

    event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    stage: Mapped[str] = mapped_column(String(10), nullable=False)  # MVP/V1/V2
    identity_model_id: Mapped[str | None] = mapped_column(String(length=36), nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
