"""事件日志相关 Schema。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EventLogCreate(BaseModel):
    """Create event log request."""
    user_id: str
    event_name: str
    # 限制 stage 口径，避免埋点阶段值漂移。
    stage: str = Field(pattern="^(MVP|V1|V2)$")
    identity_model_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class EventLogResponse(BaseModel):
    """Event log response."""
    id: str
    user_id: str
    event_name: str
    stage: str
    identity_model_id: str | None = None
    payload_json: str
    occurred_at: datetime

    model_config = {"from_attributes": True}
