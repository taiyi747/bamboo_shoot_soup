"""Content matrix schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContentMatrixGenerate(BaseModel):
    user_id: str
    identity_model_id: str | None = None
    constitution_id: str | None = None
    hints: dict[str, Any] = Field(default_factory=dict)


class ContentMatrixResponse(BaseModel):
    id: str
    user_id: str
    identity_model_id: str | None = None
    constitution_id: str | None = None
    content_pillars_json: str
    matrix_json: str
    created_at: datetime

    model_config = {"from_attributes": True}
