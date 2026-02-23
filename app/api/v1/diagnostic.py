"""
诊断相关 API 端点

对应 product-spec MVP 功能规格 1.1 身份诊断
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Diagnostic, User

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


# === Pydantic schemas ===

class DiagnosticCreate(BaseModel):
    """创建诊断请求"""
    user_id: str
    skill_stack: str | None = None
    interest_energy_curve: str | None = None
    cognitive_style: str | None = None
    value_boundary: str | None = None
    risk_tolerance: str | None = None
    time_commitment: str | None = None
    raw_responses: str | None = None


class DiagnosticResponse(BaseModel):
    """诊断响应"""
    id: str
    user_id: str
    created_at: str
    skill_stack: str | None
    interest_energy_curve: str | None
    cognitive_style: str | None
    value_boundary: str | None
    risk_tolerance: str | None
    time_commitment: str | None
    raw_responses: str | None

    class Config:
        from_attributes = True


# === API 端点 ===

@router.post("/", response_model=DiagnosticResponse, status_code=status.HTTP_201_CREATED)
def create_diagnostic(
    data: DiagnosticCreate,
    db: Session = Depends(get_db)
) -> DiagnosticResponse:
    """
    创建诊断记录（用户完成问卷后的能力画像）

    用户填写问卷后，系统生成能力画像，包含：
    - 技能栈、兴趣能量曲线、认知风格
    - 价值边界、风险承受度、时间投入
    """
    # 验证用户存在
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {data.user_id} not found"
        )

    # 创建诊断记录
    diagnostic = Diagnostic(
        user_id=data.user_id,
        skill_stack=data.skill_stack,
        interest_energy_curve=data.interest_energy_curve,
        cognitive_style=data.cognitive_style,
        value_boundary=data.value_boundary,
        risk_tolerance=data.risk_tolerance,
        time_commitment=data.time_commitment,
        raw_responses=data.raw_responses,
    )
    db.add(diagnostic)
    db.commit()
    db.refresh(diagnostic)

    return DiagnosticResponse(
        id=diagnostic.id,
        user_id=diagnostic.user_id,
        created_at=diagnostic.created_at.isoformat(),
        skill_stack=diagnostic.skill_stack,
        interest_energy_curve=diagnostic.interest_energy_curve,
        cognitive_style=diagnostic.cognitive_style,
        value_boundary=diagnostic.value_boundary,
        risk_tolerance=diagnostic.risk_tolerance,
        time_commitment=diagnostic.time_commitment,
        raw_responses=diagnostic.raw_responses,
    )


@router.get("/{diagnostic_id}", response_model=DiagnosticResponse)
def get_diagnostic(
    diagnostic_id: str,
    db: Session = Depends(get_db)
) -> DiagnosticResponse:
    """获取诊断记录详情"""
    diagnostic = db.query(Diagnostic).filter(Diagnostic.id == diagnostic_id).first()
    if not diagnostic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic with id {diagnostic_id} not found"
        )

    return DiagnosticResponse(
        id=diagnostic.id,
        user_id=diagnostic.user_id,
        created_at=diagnostic.created_at.isoformat(),
        skill_stack=diagnostic.skill_stack,
        interest_energy_curve=diagnostic.interest_energy_curve,
        cognitive_style=diagnostic.cognitive_style,
        value_boundary=diagnostic.value_boundary,
        risk_tolerance=diagnostic.risk_tolerance,
        time_commitment=diagnostic.time_commitment,
        raw_responses=diagnostic.raw_responses,
    )


@router.get("/user/{user_id}", response_model=list[DiagnosticResponse])
def get_user_diagnostics(
    user_id: str,
    db: Session = Depends(get_db)
) -> list[DiagnosticResponse]:
    """获取用户的所有诊断记录"""
    diagnostics = db.query(Diagnostic).filter(Diagnostic.user_id == user_id).all()

    return [
        DiagnosticResponse(
            id=d.id,
            user_id=d.user_id,
            created_at=d.created_at.isoformat(),
            skill_stack=d.skill_stack,
            interest_energy_curve=d.interest_energy_curve,
            cognitive_style=d.cognitive_style,
            value_boundary=d.value_boundary,
            risk_tolerance=d.risk_tolerance,
            time_commitment=d.time_commitment,
            raw_responses=d.raw_responses,
        )
        for d in diagnostics
    ]
