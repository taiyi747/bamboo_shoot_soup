"""启动包相关 Schema。"""

from datetime import datetime

from pydantic import BaseModel, Field


class LaunchKitGenerate(BaseModel):
    """Generate launch kit request."""
    user_id: str
    identity_model_id: str | None = None
    constitution_id: str | None = None
    # 可选提示，不改变服务端输出结构校验规则。
    sustainable_columns: list[str] = Field(default_factory=list)
    growth_experiment_suggestion: list[dict[str, str]] = Field(default_factory=list)


class LaunchKitDayArticleGenerate(BaseModel):
    """Generate launch-kit day article request."""

    user_id: str
    identity_model_id: str | None = None
    constitution_id: str | None = None
    day_no: int = Field(ge=1, le=7)
    theme: str = Field(min_length=1)
    draft_or_outline: str = Field(min_length=1)
    opening_text: str = Field(min_length=1)


class LaunchKitDayArticleResponse(BaseModel):
    """Launch-kit day article response."""

    day_no: int
    title: str
    markdown: str


class LaunchKitDayResponse(BaseModel):
    """Launch kit day response."""
    id: str
    kit_id: str
    day_no: int
    theme: str
    draft_or_outline: str
    opening_text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LaunchKitResponse(BaseModel):
    """Launch kit response."""
    id: str
    user_id: str
    identity_model_id: str | None = None
    constitution_id: str | None = None
    sustainable_columns_json: str
    growth_experiment_suggestion_json: str
    created_at: datetime
    days: list[LaunchKitDayResponse] = []

    model_config = {"from_attributes": True}
