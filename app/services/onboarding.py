"""Onboarding service."""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.onboarding import OnboardingSession, CapabilityProfile


def create_session(db: Session, user_id: str) -> OnboardingSession:
    """Create a new onboarding session."""
    session = OnboardingSession(
        user_id=user_id,
        status="in_progress",
        questionnaire_responses="{}",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def complete_session(
    db: Session,
    session_id: str,
    questionnaire_responses: dict,
    skill_stack: list[str],
    interest_energy_curve: list[dict],
    cognitive_style: str,
    value_boundaries: list[str],
    risk_tolerance: int,
    time_investment_hours: int,
) -> tuple[OnboardingSession, CapabilityProfile]:
    """Complete onboarding session and create capability profile."""
    # Get session
    session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Update session
    session.status = "completed"
    session.questionnaire_responses = json.dumps(questionnaire_responses, ensure_ascii=False)
    session.completed_at = datetime.now(timezone.utc)

    # Create capability profile
    profile = CapabilityProfile(
        session_id=session_id,
        user_id=session.user_id,
        skill_stack_json=json.dumps(skill_stack, ensure_ascii=False),
        interest_energy_curve_json=json.dumps(interest_energy_curve, ensure_ascii=False),
        cognitive_style=cognitive_style,
        value_boundaries_json=json.dumps(value_boundaries, ensure_ascii=False),
        risk_tolerance=risk_tolerance,
        time_investment_hours=time_investment_hours,
    )
    db.add(profile)
    db.commit()
    db.refresh(session)
    db.refresh(profile)
    return session, profile


def get_session(db: Session, session_id: str) -> OnboardingSession | None:
    """Get onboarding session by ID."""
    return db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()


def get_profile(db: Session, session_id: str) -> CapabilityProfile | None:
    """Get capability profile by session ID."""
    return db.query(CapabilityProfile).filter(CapabilityProfile.session_id == session_id).first()


def get_user_profiles(db: Session, user_id: str) -> list[CapabilityProfile]:
    """Get all capability profiles for a user."""
    return db.query(CapabilityProfile).filter(CapabilityProfile.user_id == user_id).all()
