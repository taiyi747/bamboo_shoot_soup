"""人格宪法 API 路由。"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.persona import (
    PersonaConstitutionGenerate,
    PersonaConstitutionResponse,
    RiskBoundaryItemCreate,
    RiskBoundaryItemResponse,
)
from app.services.llm_client import LLMServiceError
from app.services import persona as persona_service

router = APIRouter(prefix="/persona-constitutions", tags=["persona"])


@router.post("/generate", response_model=dict)
def generate_constitution(
    body: PersonaConstitutionGenerate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Generate persona constitution."""
    try:
        # 透传用户输入提示词到服务层，服务层负责调用 LLM 与结构校验。
        constitution = persona_service.generate_constitution(
            db=db,
            user_id=body.user_id,
            identity_model_id=body.identity_model_id,
            common_words=body.common_words,
            forbidden_words=body.forbidden_words,
        )
    except LLMServiceError as error:
        # LLM 相关异常统一映射为结构化 502。
        raise HTTPException(status_code=502, detail=error.to_detail()) from error

    return {
        "id": constitution.id,
        "user_id": constitution.user_id,
        "version": constitution.version,
        "narrative_mainline": constitution.narrative_mainline,
    }


@router.get("/users/{user_id}", response_model=list[PersonaConstitutionResponse])
def get_user_constitutions(
    user_id: str,
    db: Session = Depends(get_db),
) -> list[PersonaConstitutionResponse]:
    """Get all persona constitutions for a user."""
    return persona_service.get_user_constitutions(db, user_id)


@router.get("/users/{user_id}/latest", response_model=PersonaConstitutionResponse)
def get_latest_constitution(
    user_id: str,
    db: Session = Depends(get_db),
) -> PersonaConstitutionResponse:
    """Get user's latest constitution."""
    constitution = persona_service.get_latest_constitution(db, user_id)
    if not constitution:
        raise HTTPException(status_code=404, detail="No constitution found")
    return constitution


@router.get("/{constitution_id}", response_model=PersonaConstitutionResponse)
def get_constitution(
    constitution_id: str,
    db: Session = Depends(get_db),
) -> PersonaConstitutionResponse:
    """Get constitution by ID."""
    constitution = persona_service.get_constitution(db, constitution_id)
    if not constitution:
        raise HTTPException(status_code=404, detail="Constitution not found")
    return constitution


# 风险边界维护路由。
risk_router = APIRouter(prefix="/risk-boundaries", tags=["risk"])


@risk_router.post("", response_model=dict)
def create_risk_boundary(
    body: RiskBoundaryItemCreate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Create a risk boundary item."""
    item = persona_service.create_risk_boundary(
        db=db,
        user_id=body.user_id,
        risk_level=body.risk_level,
        boundary_type=body.boundary_type,
        statement=body.statement,
        identity_model_id=body.identity_model_id,
        constitution_id=body.constitution_id,
        source=body.source,
    )

    return {
        "id": item.id,
        "risk_level": item.risk_level,
        "boundary_type": item.boundary_type,
        "statement": item.statement,
    }


@risk_router.get("/users/{user_id}", response_model=list[RiskBoundaryItemResponse])
def get_user_risk_boundaries(
    user_id: str,
    db: Session = Depends(get_db),
) -> list[RiskBoundaryItemResponse]:
    """Get all risk boundaries for a user."""
    return persona_service.get_user_risk_boundaries(db, user_id)
