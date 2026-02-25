"""Growth experiment schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ExperimentCreate(BaseModel):
    user_id: str
    identity_model_id: str | None = None
    hypothesis: str
    variables: list[str] = Field(default_factory=list)
    execution_cycle: str

    @field_validator("hypothesis", "execution_cycle")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must be non-empty")
        return value

    @field_validator("variables")
    @classmethod
    def validate_variables(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("variables must contain at least one item")
        return cleaned


class ExperimentResultUpdate(BaseModel):
    result: str
    conclusion: str

    @field_validator("result", "conclusion")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must be non-empty")
        return value


class ExperimentResponse(BaseModel):
    id: str
    user_id: str
    identity_model_id: str | None = None
    hypothesis: str
    variables_json: str
    execution_cycle: str
    result: str
    conclusion: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
