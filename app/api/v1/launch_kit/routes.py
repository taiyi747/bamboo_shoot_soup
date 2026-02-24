"""启动包 API 路由。"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.launch_kit import LaunchKitGenerate, LaunchKitResponse
from app.services.llm_client import LLMServiceError
from app.services import launch_kit as launch_kit_service
from app.services.event_log import log_event

router = APIRouter(prefix="/launch-kits", tags=["launch_kit"])


@router.post("/generate", response_model=dict)
def generate_launch_kit(
    body: LaunchKitGenerate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Generate 7-Day Launch Kit."""
    try:
        # 请求体参数按原样传入 service，服务层负责 LLM 调用与落库。
        kit = launch_kit_service.generate_launch_kit(
            db=db,
            user_id=body.user_id,
            identity_model_id=body.identity_model_id,
            constitution_id=body.constitution_id,
            sustainable_columns=body.sustainable_columns,
            growth_experiment_suggestion=body.growth_experiment_suggestion,
        )
    except LLMServiceError as error:
        # 对外统一返回可观测的 502 结构，不透传上游原始响应。
        raise HTTPException(status_code=502, detail=error.to_detail()) from error

    # 生成成功后记录 launch_kit_generated 事件。
    log_event(
        db=db,
        user_id=body.user_id,
        event_name="launch_kit_generated",
        stage="MVP",
        identity_model_id=body.identity_model_id,
    )

    return {
        "id": kit.id,
        "user_id": kit.user_id,
        "days": [
            {
                "day_no": d.day_no,
                "theme": d.theme,
                "opening_text": d.opening_text,
            }
            for d in kit.days
        ],
    }


@router.get("/users/{user_id}", response_model=list[LaunchKitResponse])
def get_user_launch_kits(
    user_id: str,
    db: Session = Depends(get_db),
) -> list[LaunchKitResponse]:
    """Get all launch kits for a user."""
    return launch_kit_service.get_user_launch_kits(db, user_id)


@router.get("/users/{user_id}/latest", response_model=LaunchKitResponse)
def get_latest_launch_kit(
    user_id: str,
    db: Session = Depends(get_db),
) -> LaunchKitResponse:
    """Get user's latest launch kit."""
    kit = launch_kit_service.get_latest_launch_kit(db, user_id)
    if not kit:
        raise HTTPException(status_code=404, detail="No launch kit found")
    return kit


@router.get("/{kit_id}", response_model=LaunchKitResponse)
def get_launch_kit(
    kit_id: str,
    db: Session = Depends(get_db),
) -> LaunchKitResponse:
    """Get launch kit by ID."""
    kit = launch_kit_service.get_launch_kit(db, kit_id)
    if not kit:
        raise HTTPException(status_code=404, detail="Launch kit not found")
    return kit
