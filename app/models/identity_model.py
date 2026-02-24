"""身份模型与主备选择模型。"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.json_fields import parse_json_array


def _new_id() -> str:
    """生成 UUID 主键。"""
    return str(uuid4())


class IdentityModel(Base):
    """用户的身份候选卡（每次可生成 3-5 条）。"""

    __tablename__ = "identity_models"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(length=36), ForeignKey("users.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("onboarding_sessions.id"), nullable=True
    )

    # 业务交付字段：列表型字段使用 JSON 文本存储，减少迁移复杂度。
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    target_audience_pain: Mapped[str] = mapped_column(Text, default="")
    content_pillars_json: Mapped[str] = mapped_column(Text, default="[]")  # 3-5 个内容支柱
    tone_keywords_json: Mapped[str] = mapped_column(Text, default="[]")  # 语气关键词
    tone_examples_json: Mapped[str] = mapped_column(Text, default="[]")  # >=5 条口吻示例
    long_term_views_json: Mapped[str] = mapped_column(Text, default="[]")  # 5-10 条长期观点
    differentiation: Mapped[str] = mapped_column(Text, default="")  # 差异化定位（必填）
    growth_path_0_3m: Mapped[str] = mapped_column(Text, default="")
    growth_path_3_12m: Mapped[str] = mapped_column(Text, default="")
    monetization_validation_order_json: Mapped[str] = mapped_column(Text, default="[]")
    risk_boundary_json: Mapped[str] = mapped_column(Text, default="[]")  # 风险边界列表

    # 当前选择状态：由 selection 流程统一维护。
    is_primary: Mapped[bool] = mapped_column(default=False)
    is_backup: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    @property
    def content_pillars(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.content_pillars_json)]

    @property
    def tone_keywords(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.tone_keywords_json)]

    @property
    def tone_examples(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.tone_examples_json)]

    @property
    def long_term_views(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.long_term_views_json)]

    @property
    def monetization_validation_order(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.monetization_validation_order_json)]

    @property
    def risk_boundary(self) -> list[str]:
        return [str(item) for item in parse_json_array(self.risk_boundary_json)]


class IdentitySelection(Base):
    """用户主身份/备身份选择记录。"""

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

    # 关系字段用于回查被选中的身份内容。
    primary_identity: Mapped["IdentityModel"] = relationship(
        "IdentityModel", foreign_keys=[primary_identity_id]
    )
    backup_identity: Mapped["IdentityModel | None"] = relationship(
        "IdentityModel", foreign_keys=[backup_identity_id]
    )
