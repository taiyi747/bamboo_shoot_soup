"""集中导出 Pydantic Schema，供路由与测试统一引用。"""

from app.schemas.onboarding import (
    OnboardingSessionCreate,
    OnboardingSessionComplete,
    OnboardingSessionResponse,
    CapabilityProfileCreate,
    CapabilityProfileResponse,
)
from app.schemas.identity_model import (
    IdentityModelGenerate,
    IdentityModelResponse,
    IdentitySelectionCreate,
    IdentitySelectionResponse,
)
from app.schemas.persona import (
    PersonaConstitutionGenerate,
    PersonaConstitutionResponse,
    RiskBoundaryItemCreate,
    RiskBoundaryItemResponse,
)
from app.schemas.launch_kit import (
    LaunchKitGenerate,
    LaunchKitResponse,
    LaunchKitDayResponse,
)
from app.schemas.consistency_check import (
    ConsistencyCheckCreate,
    ConsistencyCheckResponse,
)
from app.schemas.event_log import (
    EventLogCreate,
    EventLogResponse,
)
from app.schemas.user import UserResponse

__all__ = [
    "OnboardingSessionCreate",
    "OnboardingSessionComplete",
    "OnboardingSessionResponse",
    "CapabilityProfileCreate",
    "CapabilityProfileResponse",
    "IdentityModelGenerate",
    "IdentityModelResponse",
    "IdentitySelectionCreate",
    "IdentitySelectionResponse",
    "PersonaConstitutionGenerate",
    "PersonaConstitutionResponse",
    "RiskBoundaryItemCreate",
    "RiskBoundaryItemResponse",
    "LaunchKitGenerate",
    "LaunchKitResponse",
    "LaunchKitDayResponse",
    "ConsistencyCheckCreate",
    "ConsistencyCheckResponse",
    "EventLogCreate",
    "EventLogResponse",
    "UserResponse",
]
