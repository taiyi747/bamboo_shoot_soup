"""
人格宪法相关 API 端点

对应 product-spec MVP 功能规格 1.3 人格宪法
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import IdentityModel, PersonaConstitution, User

router = APIRouter(prefix="/persona-constitutions", tags=["persona-constitutions"])


# === Pydantic schemas ===

class PersonaConstitutionCreate(BaseModel):
    """创建人格宪法请求"""
    user_id: str
    identity_model_id: str
    tone_words_used: str
    tone_words_forbidden: str
    tone_sentence_patterns: str
    viewpoint_fortress: str
    narrative_mainline: str
    growth_arc: str


class PersonaConstitutionUpdate(BaseModel):
    """更新人格宪法"""
    tone_words_used: str | None = None
    tone_words_forbidden: str | None = None
    tone_sentence_patterns: str | None = None
    viewpoint_fortress: str | None = None
    narrative_mainline: str | None = None
    growth_arc: str | None = None


class PersonaConstitutionResponse(BaseModel):
    """人格宪法响应"""
    id: str
    user_id: str
    identity_model_id: str
    created_at: str
    updated_at: str
    tone_words_used: str
    tone_words_forbidden: str
    tone_sentence_patterns: str
    viewpoint_fortress: str
    narrative_mainline: str
    growth_arc: str
    version: int

    class Config:
        from_attributes = True


# === API 端点 ===

@router.post("/", response_model=PersonaConstitutionResponse, status_code=status.HTTP_201_CREATED)
def create_persona_constitution(
    data: PersonaConstitutionCreate,
    db: Session = Depends(get_db)
) -> PersonaConstitutionResponse:
    """
    创建人格宪法（指导内容创作的人格一致性规则）

    用户选择主身份后，系统生成人格宪法，包含：
    - 口吻词典（常用词、禁用词、句式偏好）
    - 观点护城河（3 条不可动摇立场）
    - 叙事主线（长期动机）
    - 成长 Arc（阶段叙事模板）
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

    # 创建人格宪法
    constitution = PersonaConstitution(
        user_id=data.user_id,
        identity_model_id=data.identity_model_id,
        tone_words_used=data.tone_words_used,
        tone_words_forbidden=data.tone_words_forbidden,
        tone_sentence_patterns=data.tone_sentence_patterns,
        viewpoint_fortress=data.viewpoint_fortress,
        narrative_mainline=data.narrative_mainline,
        growth_arc=data.growth_arc,
    )
    db.add(constitution)
    db.commit()
    db.refresh(constitution)

    return PersonaConstitutionResponse(
        id=constitution.id,
        user_id=constitution.user_id,
        identity_model_id=constitution.identity_model_id,
        created_at=constitution.created_at.isoformat(),
        updated_at=constitution.updated_at.isoformat(),
        tone_words_used=constitution.tone_words_used,
        tone_words_forbidden=constitution.tone_words_forbidden,
        tone_sentence_patterns=constitution.tone_sentence_patterns,
        viewpoint_fortress=constitution.viewpoint_fortress,
        narrative_mainline=constitution.narrative_mainline,
        growth_arc=constitution.growth_arc,
        version=constitution.version,
    )


@router.get("/{constitution_id}", response_model=PersonaConstitutionResponse)
def get_persona_constitution(
    constitution_id: str,
    db: Session = Depends(get_db)
) -> PersonaConstitutionResponse:
    """获取人格宪法详情"""
    constitution = db.query(PersonaConstitution).filter(
        PersonaConstitution.id == constitution_id
    ).first()
    if not constitution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PersonaConstitution with id {constitution_id} not found"
        )

    return PersonaConstitutionResponse(
        id=constitution.id,
        user_id=constitution.user_id,
        identity_model_id=constitution.identity_model_id,
        created_at=constitution.created_at.isoformat(),
        updated_at=constitution.updated_at.isoformat(),
        tone_words_used=constitution.tone_words_used,
        tone_words_forbidden=constitution.tone_words_forbidden,
        tone_sentence_patterns=constitution.tone_sentence_patterns,
        viewpoint_fortress=constitution.viewpoint_fortress,
        narrative_mainline=constitution.narrative_mainline,
        growth_arc=constitution.growth_arc,
        version=constitution.version,
    )


@router.get("/identity/{identity_model_id}", response_model=PersonaConstitutionResponse)
def get_identity_persona_constitution(
    identity_model_id: str,
    db: Session = Depends(get_db)
) -> PersonaConstitutionResponse:
    """获取身份模型对应的人格宪法"""
    constitution = db.query(PersonaConstitution).filter(
        PersonaConstitution.identity_model_id == identity_model_id
    ).first()
    if not constitution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PersonaConstitution for identity {identity_model_id} not found"
        )

    return PersonaConstitutionResponse(
        id=constitution.id,
        user_id=constitution.user_id,
        identity_model_id=constitution.identity_model_id,
        created_at=constitution.created_at.isoformat(),
        updated_at=constitution.updated_at.isoformat(),
        tone_words_used=constitution.tone_words_used,
        tone_words_forbidden=constitution.tone_words_forbidden,
        tone_sentence_patterns=constitution.tone_sentence_patterns,
        viewpoint_fortress=constitution.viewpoint_fortress,
        narrative_mainline=constitution.narrative_mainline,
        growth_arc=constitution.growth_arc,
        version=constitution.version,
    )


@router.patch("/{constitution_id}", response_model=PersonaConstitutionResponse)
def update_persona_constitution(
    constitution_id: str,
    data: PersonaConstitutionUpdate,
    db: Session = Depends(get_db)
) -> PersonaConstitutionResponse:
    """更新人格宪法（可版本化）"""
    constitution = db.query(PersonaConstitution).filter(
        PersonaConstitution.id == constitution_id
    ).first()
    if not constitution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PersonaConstitution with id {constitution_id} not found"
        )

    # 更新字段
    if data.tone_words_used is not None:
        constitution.tone_words_used = data.tone_words_used
    if data.tone_words_forbidden is not None:
        constitution.tone_words_forbidden = data.tone_words_forbidden
    if data.tone_sentence_patterns is not None:
        constitution.tone_sentence_patterns = data.tone_sentence_patterns
    if data.viewpoint_fortress is not None:
        constitution.viewpoint_fortress = data.viewpoint_fortress
    if data.narrative_mainline is not None:
        constitution.narrative_mainline = data.narrative_mainline
    if data.growth_arc is not None:
        constitution.growth_arc = data.growth_arc

    # 增加版本号
    constitution.version += 1

    db.commit()
    db.refresh(constitution)

    return PersonaConstitutionResponse(
        id=constitution.id,
        user_id=constitution.user_id,
        identity_model_id=constitution.identity_model_id,
        created_at=constitution.created_at.isoformat(),
        updated_at=constitution.updated_at.isoformat(),
        tone_words_used=constitution.tone_words_used,
        tone_words_forbidden=constitution.tone_words_forbidden,
        tone_sentence_patterns=constitution.tone_sentence_patterns,
        viewpoint_fortress=constitution.viewpoint_fortress,
        narrative_mainline=constitution.narrative_mainline,
        growth_arc=constitution.growth_arc,
        version=constitution.version,
    )
