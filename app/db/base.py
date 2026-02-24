"""SQLAlchemy ORM 基类定义。"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """所有模型共享该基类，便于统一导出 metadata。"""

    pass
