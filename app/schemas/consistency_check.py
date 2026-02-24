"""一致性检查相关 Schema。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ConsistencyCheckCreate(BaseModel):
    """Create consistency check request."""
    user_id: str
    identity_model_id: str | None = None
    constitution_id: str | None = None
    draft_text: str = ""
    # 以下字段由服务端生成；请求方可忽略。
    deviation_items: list[str] = Field(default_factory=list)
    deviation_reasons: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    risk_triggered: bool = False
    risk_warning: str = ""

    @field_validator("risk_warning")
    @classmethod
    def validate_risk_warning(cls, v, info):
        # 当请求显式声明 risk_triggered=True 时，要求携带 risk_warning。
        if info.data.get("risk_triggered") and not v:
            raise ValueError("risk_warning is required when risk_triggered is True")
        return v


class ConsistencyCheckResponse(BaseModel):
    """Consistency check response."""
    id: str
    user_id: str
    identity_model_id: str | None = None
    constitution_id: str | None = None
    draft_text: str
    deviation_items_json: str
    deviation_items: list[str] = Field(default_factory=list)
    deviation_reasons_json: str
    deviation_reasons: list[str] = Field(default_factory=list)
    suggestions_json: str
    suggestions: list[str] = Field(default_factory=list)
    risk_triggered: bool
    risk_warning: str
    created_at: datetime

    model_config = {"from_attributes": True}
