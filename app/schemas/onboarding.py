"""Onboarding 相关 Schema。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OnboardingSessionCreate(BaseModel):
    """Create a new onboarding session."""
    user_id: str


class OnboardingSessionComplete(BaseModel):
    """Complete onboarding with questionnaire responses."""
    session_id: str
    questionnaire_responses: dict[str, Any] = Field(default_factory=dict)
    # 六个核心诊断维度。
    skill_stack: list[str] = Field(default_factory=list)
    interest_energy_curve: list[dict[str, Any]] = Field(default_factory=list)
    cognitive_style: str = ""
    value_boundaries: list[str] = Field(default_factory=list)
    risk_tolerance: int = Field(ge=1, le=5, default=3)
    time_investment_hours: int = Field(ge=0, default=0)


class OnboardingSessionResponse(BaseModel):
    """Onboarding session response."""
    id: str
    user_id: str
    status: str
    questionnaire_responses: str
    questionnaire: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class CapabilityProfileCreate(BaseModel):
    """Create capability profile."""
    session_id: str
    user_id: str
    skill_stack: list[str] = Field(default_factory=list)
    interest_energy_curve: list[dict[str, Any]] = Field(default_factory=list)
    cognitive_style: str = ""
    value_boundaries: list[str] = Field(default_factory=list)
    risk_tolerance: int = Field(ge=1, le=5, default=3)
    time_investment_hours: int = Field(ge=0, default=0)


class CapabilityProfileResponse(BaseModel):
    """Capability profile response."""
    id: str
    session_id: str
    user_id: str
    skill_stack_json: str
    skill_stack: list[str] = Field(default_factory=list)
    interest_energy_curve_json: str
    interest_energy_curve: list[dict[str, Any]] = Field(default_factory=list)
    cognitive_style: str
    value_boundaries_json: str
    value_boundaries: list[str] = Field(default_factory=list)
    risk_tolerance: int
    time_investment_hours: int
    created_at: datetime

    model_config = {"from_attributes": True}
