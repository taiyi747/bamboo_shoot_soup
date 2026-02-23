"""Persona constitution schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class PersonaConstitutionGenerate(BaseModel):
    """Generate persona constitution request."""
    user_id: str
    identity_model_id: str | None = None
    # Optional inputs to guide generation
    common_words: list[str] = Field(default_factory=list)
    forbidden_words: list[str] = Field(default_factory=list)


class PersonaConstitutionResponse(BaseModel):
    """Persona constitution response."""
    id: str
    user_id: str
    identity_model_id: str | None = None
    common_words_json: str
    forbidden_words_json: str
    sentence_preferences_json: str
    moat_positions_json: str
    narrative_mainline: str
    growth_arc_template: str
    version: int
    previous_version_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RiskBoundaryItemCreate(BaseModel):
    """Create risk boundary item."""
    user_id: str
    identity_model_id: str | None = None
    constitution_id: str | None = None
    risk_level: int = Field(ge=1, le=5, default=3)
    boundary_type: str = ""  # legal, platform, reputational
    statement: str = ""
    source: str = "user_input"  # user_input or system_generated


class RiskBoundaryItemResponse(BaseModel):
    """Risk boundary item response."""
    id: str
    user_id: str
    identity_model_id: str | None = None
    constitution_id: str | None = None
    risk_level: int
    boundary_type: str
    statement: str
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}
