"""LLM call observability log model."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _new_id() -> str:
    return str(uuid4())


class LLMCallLog(Base):
    """Structured trace log for each LLM invocation."""

    __tablename__ = "llm_call_logs"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str | None] = mapped_column(
        String(length=36),
        ForeignKey("users.id"),
        nullable=True,
    )
    operation: Mapped[str] = mapped_column(String(length=100), nullable=False)
    code: Mapped[str] = mapped_column(String(length=80), nullable=False)
    retry: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    request_id: Mapped[str | None] = mapped_column(String(length=200), nullable=True)
    provider_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
