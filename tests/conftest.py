import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings


os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("OPENAI_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("MODEL_NAME", "test-model")


@pytest.fixture(autouse=True)
def _reset_config_caches() -> None:
    reset_llm = None
    try:
        from app.services.llm_client import reset_llm_client_cache

        reset_llm = reset_llm_client_cache
    except ModuleNotFoundError:
        reset_llm = None

    get_settings.cache_clear()
    if reset_llm is not None:
        reset_llm()
    yield
    get_settings.cache_clear()
    if reset_llm is not None:
        reset_llm()
