"""User-related schemas."""

from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    """Created user payload."""

    id: str
    created_at: datetime

    model_config = {"from_attributes": True}
