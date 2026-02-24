"""身份模型相关 Schema。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class IdentityModelGenerate(BaseModel):
    """Generate identity model request."""
    user_id: str
    session_id: str | None = None
    # 若提供 session_id，服务端可从画像表覆盖该输入。
    capability_profile: dict[str, Any] = Field(default_factory=dict)
    count: int = Field(ge=3, le=5, default=3)


class IdentityModelResponse(BaseModel):
    """Identity model response."""
    id: str
    user_id: str
    session_id: str | None = None
    title: str
    target_audience_pain: str
    content_pillars_json: str
    content_pillars: list[str] = Field(default_factory=list)
    tone_keywords_json: str
    tone_keywords: list[str] = Field(default_factory=list)
    tone_examples_json: str
    tone_examples: list[str] = Field(default_factory=list)
    long_term_views_json: str
    long_term_views: list[str] = Field(default_factory=list)
    differentiation: str
    growth_path_0_3m: str
    growth_path_3_12m: str
    monetization_validation_order_json: str
    monetization_validation_order: list[str] = Field(default_factory=list)
    risk_boundary_json: str
    risk_boundary: list[str] = Field(default_factory=list)
    is_primary: bool
    is_backup: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class IdentitySelectionCreate(BaseModel):
    """Create identity selection."""
    user_id: str
    primary_identity_id: str
    backup_identity_id: str | None = None

    @field_validator("backup_identity_id")
    @classmethod
    def validate_different_ids(cls, v, info):
        # 请求层提前拦截主备相同，减少无效数据库操作。
        if v is not None and "primary_identity_id" in info.data:
            if v == info.data["primary_identity_id"]:
                raise ValueError("backup_identity_id must be different from primary_identity_id")
        return v


class IdentitySelectionResponse(BaseModel):
    """Identity selection response."""
    id: str
    user_id: str
    primary_identity_id: str
    backup_identity_id: str | None = None
    selected_at: datetime

    model_config = {"from_attributes": True}
