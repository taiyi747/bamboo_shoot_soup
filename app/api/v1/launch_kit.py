"""
7天启动包相关 API 端点

对应 product-spec MVP 功能规格 1.4 7天启动包
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import IdentityModel, LaunchKit, PersonaConstitution, User

router = APIRouter(prefix="/launch-kits", tags=["launch-kits"])


# === Pydantic schemas ===

class DayContent(BaseModel):
    """单日内容"""
    theme: str
    content: str


class LaunchKitCreate(BaseModel):
    """创建7天启动包请求"""
    user_id: str
    identity_model_id: str
    persona_constitution_id: str
    day_1: DayContent
    day_2: DayContent
    day_3: DayContent
    day_4: DayContent
    day_5: DayContent
    day_6: DayContent
    day_7: DayContent
    sustainable_columns: str
    growth_experiment: str


class LaunchKitUpdate(BaseModel):
    """更新7天启动包"""
    is_used: Optional[bool] = None
    started_at: Optional[str] = None


class LaunchKitResponse(BaseModel):
    """7天启动包响应"""
    id: str
    user_id: str
    identity_model_id: str
    persona_constitution_id: str
    created_at: str
    updated_at: str
    day_1_theme: str
    day_1_content: str
    day_2_theme: str
    day_2_content: str
    day_3_theme: str
    day_3_content: str
    day_4_theme: str
    day_4_content: str
    day_5_theme: str
    day_5_content: str
    day_6_theme: str
    day_6_content: str
    day_7_theme: str
    day_7_content: str
    sustainable_columns: str
    growth_experiment: str
    is_used: bool
    started_at: Optional[str]

    class Config:
        from_attributes = True


# === API 端点 ===

@router.post("/", response_model=LaunchKitResponse, status_code=status.HTTP_201_CREATED)
def create_launch_kit(
    data: LaunchKitCreate,
    db: Session = Depends(get_db)
) -> LaunchKitResponse:
    """
    创建7天启动包（用户选择身份后的执行指南）

    用户选择主身份后，系统生成 7 天启动包，包含：
    - 7 日每日主题和内容草稿
    - 3 个可持续栏目
    - 1 个增长实验
    """
    # 验证用户存在
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {data.user_id} not found"
        )

    # 验证身份模型存在
    identity = db.query(IdentityModel).filter(IdentityModel.id == data.identity_model_id).first()
    if not identity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IdentityModel with id {data.identity_model_id} not found"
        )

    # 验证人格宪法存在
    constitution = db.query(PersonaConstitution).filter(
        PersonaConstitution.id == data.persona_constitution_id
    ).first()
    if not constitution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PersonaConstitution with id {data.persona_constitution_id} not found"
        )

    # 创建7天启动包
    launch_kit = LaunchKit(
        user_id=data.user_id,
        identity_model_id=data.identity_model_id,
        persona_constitution_id=data.persona_constitution_id,
        day_1_theme=data.day_1.theme,
        day_1_content=data.day_1.content,
        day_2_theme=data.day_2.theme,
        day_2_content=data.day_2.content,
        day_3_theme=data.day_3.theme,
        day_3_content=data.day_3.content,
        day_4_theme=data.day_4.theme,
        day_4_content=data.day_4.content,
        day_5_theme=data.day_5.theme,
        day_5_content=data.day_5.content,
        day_6_theme=data.day_6.theme,
        day_6_content=data.day_6.content,
        day_7_theme=data.day_7.theme,
        day_7_content=data.day_7.content,
        sustainable_columns=data.sustainable_columns,
        growth_experiment=data.growth_experiment,
    )
    db.add(launch_kit)
    db.commit()
    db.refresh(launch_kit)

    return _to_response(launch_kit)


@router.get("/{launch_kit_id}", response_model=LaunchKitResponse)
def get_launch_kit(
    launch_kit_id: str,
    db: Session = Depends(get_db)
) -> LaunchKitResponse:
    """获取7天启动包详情"""
    launch_kit = db.query(LaunchKit).filter(LaunchKit.id == launch_kit_id).first()
    if not launch_kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LaunchKit with id {launch_kit_id} not found"
        )

    return _to_response(launch_kit)


@router.get("/identity/{identity_model_id}", response_model=LaunchKitResponse)
def get_identity_launch_kit(
    identity_model_id: str,
    db: Session = Depends(get_db)
) -> LaunchKitResponse:
    """获取身份模型对应的7天启动包"""
    launch_kit = db.query(LaunchKit).filter(
        LaunchKit.identity_model_id == identity_model_id
    ).first()
    if not launch_kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LaunchKit for identity {identity_model_id} not found"
        )

    return _to_response(launch_kit)


@router.patch("/{launch_kit_id}", response_model=LaunchKitResponse)
def update_launch_kit(
    launch_kit_id: str,
    data: LaunchKitUpdate,
    db: Session = Depends(get_db)
) -> LaunchKitResponse:
    """更新7天启动包状态"""
    launch_kit = db.query(LaunchKit).filter(LaunchKit.id == launch_kit_id).first()
    if not launch_kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LaunchKit with id {launch_kit_id} not found"
        )

    if data.is_used is not None:
        launch_kit.is_used = data.is_used
        if data.is_used and not launch_kit.started_at:
            launch_kit.started_at = datetime.now(timezone.utc)

    if data.started_at is not None:
        launch_kit.started_at = datetime.fromisoformat(data.started_at)

    db.commit()
    db.refresh(launch_kit)

    return _to_response(launch_kit)


def _to_response(launch_kit: LaunchKit) -> LaunchKitResponse:
    """转换为响应模型"""
    return LaunchKitResponse(
        id=launch_kit.id,
        user_id=launch_kit.user_id,
        identity_model_id=launch_kit.identity_model_id,
        persona_constitution_id=launch_kit.persona_constitution_id,
        created_at=launch_kit.created_at.isoformat(),
        updated_at=launch_kit.updated_at.isoformat(),
        day_1_theme=launch_kit.day_1_theme,
        day_1_content=launch_kit.day_1_content,
        day_2_theme=launch_kit.day_2_theme,
        day_2_content=launch_kit.day_2_content,
        day_3_theme=launch_kit.day_3_theme,
        day_3_content=launch_kit.day_3_content,
        day_4_theme=launch_kit.day_4_theme,
        day_4_content=launch_kit.day_4_content,
        day_5_theme=launch_kit.day_5_theme,
        day_5_content=launch_kit.day_5_content,
        day_6_theme=launch_kit.day_6_theme,
        day_6_content=launch_kit.day_6_content,
        day_7_theme=launch_kit.day_7_theme,
        day_7_content=launch_kit.day_7_content,
        sustainable_columns=launch_kit.sustainable_columns,
        growth_experiment=launch_kit.growth_experiment,
        is_used=launch_kit.is_used,
        started_at=launch_kit.started_at.isoformat() if launch_kit.started_at else None,
    )
