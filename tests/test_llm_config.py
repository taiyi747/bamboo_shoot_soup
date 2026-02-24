import pytest

import app.main as main_module
from app.core.config import Settings
from app.services.llm_client import normalize_openai_base_url


def test_normalize_openai_base_url_supports_root_and_chat_path() -> None:
    assert normalize_openai_base_url("https://api.openai.com") == "https://api.openai.com/v1"
    assert (
        normalize_openai_base_url("https://proxy.example.com/apis/v1/chat/completions")
        == "https://proxy.example.com/apis/v1"
    )


def test_validate_llm_settings_fails_when_missing_env_values() -> None:
    settings = Settings(
        _env_file=None,
        openai_api_key=None,
        openai_base_url=None,
        model_name=None,
    )

    with pytest.raises(ValueError, match="Missing required LLM environment variables"):
        settings.validate_llm_settings()


def test_startup_wraps_configuration_error(monkeypatch) -> None:
    def _raise_value_error():
        raise ValueError("Missing required LLM environment variables: OPENAI_API_KEY")

    monkeypatch.setattr(main_module, "ensure_llm_ready", _raise_value_error)

    with pytest.raises(RuntimeError, match="Missing required LLM environment variables"):
        main_module.validate_runtime_configuration()


def test_default_openai_timeout_is_extended() -> None:
    settings = Settings(
        _env_file=None,
        openai_api_key="test-key",
        openai_base_url="https://api.openai.com/v1",
        model_name="test-model",
    )

    assert settings.openai_timeout_seconds == 90.0


def test_cors_allow_origins_accepts_json_and_csv_formats() -> None:
    json_settings = Settings(
        _env_file=None,
        cors_allow_origins='["http://127.0.0.1:3000","http://localhost:3000"]',
    )
    csv_settings = Settings(
        _env_file=None,
        cors_allow_origins="http://127.0.0.1:3000,http://localhost:3000",
    )

    assert json_settings.cors_allow_origins == [
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]
    assert csv_settings.cors_allow_origins == [
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]


def test_debug_flag_defaults_false_and_supports_boolean_strings() -> None:
    default_settings = Settings(_env_file=None)
    enabled_settings = Settings(_env_file=None, debug="true")
    disabled_settings = Settings(_env_file=None, debug="false")

    assert default_settings.debug is False
    assert enabled_settings.debug is True
    assert disabled_settings.debug is False


def test_reasoning_flag_defaults_none_and_supports_boolean_strings() -> None:
    default_settings = Settings(_env_file=None)
    enabled_settings = Settings(_env_file=None, reasoning="true")
    disabled_settings = Settings(_env_file=None, reasoning="false")

    assert default_settings.reasoning is None
    assert enabled_settings.reasoning is True
    assert disabled_settings.reasoning is False


def test_legacy_reason_falls_back_to_reasoning() -> None:
    legacy_enabled_settings = Settings(_env_file=None, reason="true")
    legacy_disabled_settings = Settings(_env_file=None, reason="false")

    assert legacy_enabled_settings.reasoning is True
    assert legacy_disabled_settings.reasoning is False
