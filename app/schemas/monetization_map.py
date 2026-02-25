"""Monetization map schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MonetizationMapGenerate(BaseModel):
    user_id: str
    identity_model_id: str | None = None
    constitution_id: str | None = None
    hints: dict[str, Any] = Field(default_factory=dict)


class MonetizationMapResponse(BaseModel):
    id: str
    user_id: str
    identity_model_id: str | None = None
    constitution_id: str | None = None
    primary_path: str
    backup_path: str
    weeks_json: str
    created_at: datetime

    model_config = {"from_attributes": True}
