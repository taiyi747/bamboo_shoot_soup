"""V1 content matrix models."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.json_fields import parse_json_array


def _new_id() -> str:
    return str(uuid4())


class ContentMatrix(Base):
    """Content matrix generation batch."""

    __tablename__ = "content_matrixes"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    identity_model_id: Mapped[str | None] = mapped_column(
        String(length=36),
        ForeignKey("identity_models.id"),
        nullable=True,
    )
    pillar: Mapped[str] = mapped_column(String(length=120), nullable=False)
    platform: Mapped[str] = mapped_column(String(length=50), nullable=False)
    format: Mapped[str] = mapped_column(String(length=50), nullable=False)
    status: Mapped[str] = mapped_column(String(length=30), nullable=False, default="generated")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    topics: Mapped[list["ContentTopic"]] = relationship(
        "ContentTopic",
        back_populates="matrix",
        order_by="ContentTopic.created_at.asc()",
    )


class ContentTopic(Base):
    """Single topic item under a matrix."""

    __tablename__ = "content_topics"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    matrix_id: Mapped[str] = mapped_column(
        String(length=36),
        ForeignKey("content_matrixes.id"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    identity_model_id: Mapped[str | None] = mapped_column(
        String(length=36),
        ForeignKey("identity_models.id"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    angle: Mapped[str] = mapped_column(Text, nullable=False, default="")
    platform: Mapped[str] = mapped_column(String(length=50), nullable=False)
    format: Mapped[str] = mapped_column(String(length=50), nullable=False)
    status: Mapped[str] = mapped_column(String(length=30), nullable=False, default="draft")
    rewrite_variants_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    matrix: Mapped["ContentMatrix"] = relationship("ContentMatrix", back_populates="topics")

    @property
    def rewrite_variants(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.rewrite_variants_json)]
