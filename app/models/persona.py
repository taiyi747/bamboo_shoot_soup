"""人格宪法与风险边界模型。"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.utils.json_fields import parse_json_array


def _new_id() -> str:
    """生成 UUID 主键。"""
    return str(uuid4())


class PersonaConstitution(Base):
    """人格宪法：口吻词典、观点护城河、叙事主线、成长弧。"""

    __tablename__ = "persona_constitutions"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    identity_model_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("identity_models.id"), nullable=True
    )

    # 业务内容字段：列表类内容统一为 JSON 文本。
    common_words_json: Mapped[str] = mapped_column(Text, default="[]")
    forbidden_words_json: Mapped[str] = mapped_column(Text, default="[]")
    sentence_preferences_json: Mapped[str] = mapped_column(Text, default="[]")
    moat_positions_json: Mapped[str] = mapped_column(Text, default="[]")
    narrative_mainline: Mapped[str] = mapped_column(Text, default="")
    growth_arc_template: Mapped[str] = mapped_column(Text, default="")

    # 版本链：支持宪法迭代与回溯。
    version: Mapped[int] = mapped_column(Integer, default=1)
    previous_version_id: Mapped[str | None] = mapped_column(String(length=36), nullable=True)

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

    @property
    def common_words(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.common_words_json)]

    @property
    def forbidden_words(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.forbidden_words_json)]

    @property
    def sentence_preferences(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.sentence_preferences_json)]

    @property
    def moat_positions(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.moat_positions_json)]


class RiskBoundaryItem(Base):
    """风险边界条目：用于约束发布前后的合规边界。"""

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
    boundary_type: Mapped[str] = mapped_column(String(50), default="")  # legal/platform/reputational
    statement: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(100), default="")  # user_input/system_generated

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
