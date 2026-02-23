"""
用户相关 API 端点
"""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])


class UserResponse(BaseModel):
    id: str
    created_at: str

    class Config:
        from_attributes = True


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(db: Session = Depends(get_db)) -> UserResponse:
    """创建新用户"""
    user = User()
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        created_at=user.created_at.isoformat(),
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)) -> UserResponse:
    """获取用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        created_at=user.created_at.isoformat(),
    )
