"""用户模型：作为所有业务对象的归属主体。"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _new_user_id() -> str:
    return str(uuid4())


class User(Base):
    """最小用户实体，满足本地化 MVP 关联需求。"""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(length=36), primary_key=True, default=_new_user_id)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
