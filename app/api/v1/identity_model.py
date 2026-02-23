"""
身份模型相关 API 端点

对应 product-spec MVP 功能规格 1.2 身份生成
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Diagnostic, IdentityModel, User

router = APIRouter(prefix="/identity-models", tags=["identity-models"])


# === Pydantic schemas ===

class IdentityModelCreate(BaseModel):
    """创建身份模型请求"""
    user_id: str
    diagnostic_id: str
    title: str
    target_audience: str
    content_pillars: str
    tone_style: str
    viewpoint_library: str
    differentiation: str
    growth_path: str
    monetization_path: str
    risk_boundary: str


class IdentityModelUpdate(BaseModel):
    """更新身份模型（选择主/备身份）"""
    is_selected_primary: Optional[bool] = None
    is_selected_backup: Optional[bool] = None


class IdentityModelResponse(BaseModel):
    """身份模型响应"""
    id: str
    user_id: str
    diagnostic_id: str
    created_at: str
    title: str
    target_audience: str
    content_pillars: str
    tone_style: str
    viewpoint_library: str
    differentiation: str
    growth_path: str
    monetization_path: str
    risk_boundary: str
    is_selected_primary: bool
    is_selected_backup: bool
    selected_at: Optional[str]

    class Config:
        from_attributes = True


# === API 端点 ===

@router.post("/", response_model=IdentityModelResponse, status_code=status.HTTP_201_CREATED)
def create_identity_model(
    data: IdentityModelCreate,
    db: Session = Depends(get_db)
) -> IdentityModelResponse:
    """
    创建身份模型（系统生成的候选身份方案）

    基于诊断结果，生成 3-5 个身份模型供用户选择。
    每个模型包含：
    - 标题、目标受众、内容支柱
    - 语气风格、观点库、差异化定位
    - 成长路径、变现路径、风险禁区
    """
    # 验证用户存在
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {data.user_id} not found"
        )

    # 验证诊断记录存在
    diagnostic = db.query(Diagnostic).filter(Diagnostic.id == data.diagnostic_id).first()
    if not diagnostic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic with id {data.diagnostic_id} not found"
        )

    # 创建身份模型
    identity = IdentityModel(
        user_id=data.user_id,
        diagnostic_id=data.diagnostic_id,
        title=data.title,
        target_audience=data.target_audience,
        content_pillars=data.content_pillars,
        tone_style=data.tone_style,
        viewpoint_library=data.viewpoint_library,
        differentiation=data.differentiation,
        growth_path=data.growth_path,
        monetization_path=data.monetization_path,
        risk_boundary=data.risk_boundary,
    )
    db.add(identity)
    db.commit()
    db.refresh(identity)

    return IdentityModelResponse(
        id=identity.id,
        user_id=identity.user_id,
        diagnostic_id=identity.diagnostic_id,
        created_at=identity.created_at.isoformat(),
        title=identity.title,
        target_audience=identity.target_audience,
        content_pillars=identity.content_pillars,
        tone_style=identity.tone_style,
        viewpoint_library=identity.viewpoint_library,
        differentiation=identity.differentiation,
        growth_path=identity.growth_path,
        monetization_path=identity.monetization_path,
        risk_boundary=identity.risk_boundary,
        is_selected_primary=identity.is_selected_primary,
        is_selected_backup=identity.is_selected_backup,
        selected_at=identity.selected_at.isoformat() if identity.selected_at else None,
    )


@router.get("/{identity_id}", response_model=IdentityModelResponse)
def get_identity_model(
    identity_id: str,
    db: Session = Depends(get_db)
) -> IdentityModelResponse:
    """获取身份模型详情"""
    identity = db.query(IdentityModel).filter(IdentityModel.id == identity_id).first()
    if not identity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IdentityModel with id {identity_id} not found"
        )

    return IdentityModelResponse(
        id=identity.id,
        user_id=identity.user_id,
        diagnostic_id=identity.diagnostic_id,
        created_at=identity.created_at.isoformat(),
        title=identity.title,
        target_audience=identity.target_audience,
        content_pillars=identity.content_pillars,
        tone_style=identity.tone_style,
        viewpoint_library=identity.viewpoint_library,
        differentiation=identity.differentiation,
        growth_path=identity.growth_path,
        monetization_path=identity.monetization_path,
        risk_boundary=identity.risk_boundary,
        is_selected_primary=identity.is_selected_primary,
        is_selected_backup=identity.is_selected_backup,
        selected_at=identity.selected_at.isoformat() if identity.selected_at else None,
    )


@router.get("/diagnostic/{diagnostic_id}", response_model=list[IdentityModelResponse])
def get_diagnostic_identity_models(
    diagnostic_id: str,
    db: Session = Depends(get_db)
) -> list[IdentityModelResponse]:
    """获取诊断记录的所有身份模型"""
    identities = db.query(IdentityModel).filter(
        IdentityModel.diagnostic_id == diagnostic_id
    ).all()

    return [
        IdentityModelResponse(
            id=i.id,
            user_id=i.user_id,
            diagnostic_id=i.diagnostic_id,
            created_at=i.created_at.isoformat(),
            title=i.title,
            target_audience=i.target_audience,
            content_pillars=i.content_pillars,
            tone_style=i.tone_style,
            viewpoint_library=i.viewpoint_library,
            differentiation=i.differentiation,
            growth_path=i.growth_path,
            monetization_path=i.monetization_path,
            risk_boundary=i.risk_boundary,
            is_selected_primary=i.is_selected_primary,
            is_selected_backup=i.is_selected_backup,
            selected_at=i.selected_at.isoformat() if i.selected_at else None,
        )
        for i in identities
    ]


@router.patch("/{identity_id}", response_model=IdentityModelResponse)
def update_identity_model(
    identity_id: str,
    data: IdentityModelUpdate,
    db: Session = Depends(get_db)
) -> IdentityModelResponse:
    """
    更新身份模型（选择主/备身份）

    用户选择 1 个主身份 + 1 个备选身份
    """
    identity = db.query(IdentityModel).filter(IdentityModel.id == identity_id).first()
    if not identity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IdentityModel with id {identity_id} not found"
        )

    # 更新选择状态
    if data.is_selected_primary is not None:
        identity.is_selected_primary = data.is_selected_primary
        if data.is_selected_primary:
            identity.selected_at = datetime.now(timezone.utc)

    if data.is_selected_backup is not None:
        identity.is_selected_backup = data.is_selected_backup

    db.commit()
    db.refresh(identity)

    return IdentityModelResponse(
        id=identity.id,
        user_id=identity.user_id,
        diagnostic_id=identity.diagnostic_id,
        created_at=identity.created_at.isoformat(),
        title=identity.title,
        target_audience=identity.target_audience,
        content_pillars=identity.content_pillars,
        tone_style=identity.tone_style,
        viewpoint_library=identity.viewpoint_library,
        differentiation=identity.differentiation,
        growth_path=identity.growth_path,
        monetization_path=identity.monetization_path,
        risk_boundary=identity.risk_boundary,
        is_selected_primary=identity.is_selected_primary,
        is_selected_backup=identity.is_selected_backup,
        selected_at=identity.selected_at.isoformat() if identity.selected_at else None,
    )
