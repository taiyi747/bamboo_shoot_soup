"""一致性检查 API 路由。"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.consistency_check import (
    ConsistencyCheckCreate,
    ConsistencyCheckResponse,
)
from app.services.llm_client import LLMServiceError
from app.services import consistency_check as consistency_service
from app.services.event_log import log_event

router = APIRouter(prefix="/consistency-checks", tags=["consistency"])


@router.post("", response_model=dict)
def create_consistency_check(
    body: ConsistencyCheckCreate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Check draft consistency against persona constitution.
    
    Per product-spec 2.6:
    - Output must include: deviation_items, deviation_reasons, suggestions
    - If risk_triggered is True, risk_warning is required
    """
    try:
        # 路由层仅做参数分发；一致性分析细节由 service 处理。
        result = consistency_service.check_consistency(
            db=db,
            user_id=body.user_id,
            draft_text=body.draft_text,
            identity_model_id=body.identity_model_id,
            constitution_id=body.constitution_id,
        )
        check = result.check

        # 记录检查触发事件，payload 仅保留必要信号字段。
        log_event(
            db=db,
            user_id=body.user_id,
            event_name="consistency_check_triggered",
            stage="MVP",
            identity_model_id=body.identity_model_id,
            payload={
                "risk_triggered": check.risk_triggered,
                "score": result.score,
                "degraded": result.degraded,
                "degrade_reason": result.degrade_reason,
                "schema_repair_attempts": result.schema_repair_attempts,
            },
        )

        return {
            "id": check.id,
            "deviation_items": check.deviation_items_json,
            "deviation_reasons": check.deviation_reasons_json,
            "suggestions": check.suggestions_json,
            "risk_triggered": check.risk_triggered,
            "risk_warning": check.risk_warning,
            "score": result.score,
            "degraded": result.degraded,
            "degrade_reason": result.degrade_reason,
            "schema_repair_attempts": result.schema_repair_attempts,
        }
    except LLMServiceError as error:
        # LLM 调用失败统一返回结构化 502。
        raise HTTPException(status_code=502, detail=error.to_detail()) from error
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}", response_model=list[ConsistencyCheckResponse])
def get_user_checks(
    user_id: str,
    db: Session = Depends(get_db),
) -> list[ConsistencyCheckResponse]:
    """Get all consistency checks for a user."""
    return consistency_service.get_user_checks(db, user_id)


@router.get("/{check_id}", response_model=ConsistencyCheckResponse)
def get_check(
    check_id: str,
    db: Session = Depends(get_db),
) -> ConsistencyCheckResponse:
    """Get consistency check by ID."""
    check = consistency_service.get_check(db, check_id)
    if not check:
        raise HTTPException(status_code=404, detail="Consistency check not found")
    return check
