"""V2 viewpoint asset library models."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.json_fields import parse_json_array


def _new_id() -> str:
    return str(uuid4())


class ViewpointAsset(Base):
    """Core viewpoint asset."""

    __tablename__ = "viewpoint_assets"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    identity_model_id: Mapped[str | None] = mapped_column(
        String(length=36),
        ForeignKey("identity_models.id"),
        nullable=True,
    )
    topic: Mapped[str] = mapped_column(String(length=120), nullable=False)
    platform: Mapped[str] = mapped_column(String(length=50), nullable=False, default="")
    stance: Mapped[str] = mapped_column(Text, nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    cases: Mapped[list["AssetCase"]] = relationship("AssetCase", back_populates="asset")
    frameworks: Mapped[list["AssetFramework"]] = relationship(
        "AssetFramework",
        back_populates="asset",
    )
    faq_items: Mapped[list["FaqItem"]] = relationship("FaqItem", back_populates="asset")

    @property
    def tags(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.tags_json)]


class AssetCase(Base):
    """Case linked to an asset."""

    __tablename__ = "asset_cases"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    asset_id: Mapped[str] = mapped_column(
        String(length=36),
        ForeignKey("viewpoint_assets.id"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(length=200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    asset: Mapped["ViewpointAsset"] = relationship("ViewpointAsset", back_populates="cases")


class AssetFramework(Base):
    """Framework linked to an asset."""

    __tablename__ = "asset_frameworks"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    asset_id: Mapped[str] = mapped_column(
        String(length=36),
        ForeignKey("viewpoint_assets.id"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(length=200), nullable=False)
    steps_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    asset: Mapped["ViewpointAsset"] = relationship("ViewpointAsset", back_populates="frameworks")

    @property
    def steps(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.steps_json)]


class FaqItem(Base):
    """FAQ item linked to an asset."""

    __tablename__ = "faq_items"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    asset_id: Mapped[str] = mapped_column(
        String(length=36),
        ForeignKey("viewpoint_assets.id"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    asset: Mapped["ViewpointAsset"] = relationship("ViewpointAsset", back_populates="faq_items")
