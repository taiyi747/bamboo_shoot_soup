"""Onboarding API 路由。"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.onboarding import (
    OnboardingSessionCreate,
    OnboardingSessionComplete,
    OnboardingSessionResponse,
    CapabilityProfileResponse,
)
from app.services import onboarding as onboarding_service
from app.services.event_log import log_event

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/sessions", response_model=dict)
def create_session(
    body: OnboardingSessionCreate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Create a new onboarding session."""
    # 1) 创建会话；2) 写入 onboarding_started 事件。
    session = onboarding_service.create_session(db, body.user_id)
    
    # 记录会话启动埋点。
    log_event(
        db=db,
        user_id=body.user_id,
        event_name="onboarding_started",
        stage="MVP",
    )
    
    return {"id": session.id, "user_id": session.user_id, "status": session.status}


@router.post("/sessions/{session_id}/complete")
def complete_session(
    session_id: str,
    body: OnboardingSessionComplete,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Complete onboarding session and generate capability profile."""
    try:
        # 透传六维画像输入，由 service 负责会话状态迁移与画像落库。
        session, profile = onboarding_service.complete_session(
            db=db,
            session_id=session_id,
            questionnaire_responses=body.questionnaire_responses,
            skill_stack=body.skill_stack,
            interest_energy_curve=body.interest_energy_curve,
            cognitive_style=body.cognitive_style,
            value_boundaries=body.value_boundaries,
            risk_tolerance=body.risk_tolerance,
            time_investment_hours=body.time_investment_hours,
        )
        
        # 画像生成成功后记录完成事件。
        log_event(
            db=db,
            user_id=session.user_id,
            event_name="onboarding_completed",
            stage="MVP",
        )
        
        return {
            "session_id": session.id,
            "status": session.status,
            "profile_id": profile.id,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sessions/{session_id}", response_model=OnboardingSessionResponse)
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> OnboardingSessionResponse:
    """Get onboarding session by ID."""
    session = onboarding_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions/{session_id}/profile", response_model=CapabilityProfileResponse)
def get_profile(
    session_id: str,
    db: Session = Depends(get_db),
) -> CapabilityProfileResponse:
    """Get capability profile for a session."""
    profile = onboarding_service.get_profile(db, session_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("/users/{user_id}/profiles", response_model=list[CapabilityProfileResponse])
def get_user_profiles(
    user_id: str,
    db: Session = Depends(get_db),
) -> list[CapabilityProfileResponse]:
    """Get all capability profiles for a user."""
    return onboarding_service.get_user_profiles(db, user_id)
