from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.llm_client import LLMClient, LLMServiceError


class _DummyTimeoutError(Exception):
    pass


class _DummyConnectionError(Exception):
    pass


class _DummyStatusError(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"status={status_code}")
        self.status_code = status_code
        self.response = SimpleNamespace(headers={"x-request-id": "req-from-status"})


class _Message:
    def __init__(self, content: str) -> None:
        self.content = content


class _Choice:
    def __init__(self, content: str) -> None:
        self.message = _Message(content)


class _Completion:
    def __init__(self, content: str, request_id: str = "req-from-response") -> None:
        self.choices = [_Choice(content)]
        self._request_id = request_id


def _build_client(create_func, retries: int = 0) -> LLMClient:
    client = object.__new__(LLMClient)
    client._max_retries = retries
    client._model_name = "test-model"
    client._openai = SimpleNamespace(
        APITimeoutError=_DummyTimeoutError,
        APIConnectionError=_DummyConnectionError,
        APIStatusError=_DummyStatusError,
    )
    client._client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create_func),
        )
    )
    return client


def test_generate_json_invalid_json_raises_structured_error() -> None:
    def _create(**_kwargs):
        return _Completion("this is not json")

    client = _build_client(_create, retries=0)

    with pytest.raises(LLMServiceError) as exc_info:
        client.generate_json(
            operation="test_invalid_json",
            system_prompt="prompt",
            user_payload={"foo": "bar"},
        )

    error = exc_info.value
    assert error.code == "LLM_INVALID_RESPONSE"
    assert error.operation == "test_invalid_json"
    assert error.attempts == 1


def test_generate_json_timeout_retries_exhausted() -> None:
    call_count = {"count": 0}

    def _create(**_kwargs):
        call_count["count"] += 1
        raise _DummyTimeoutError("timed out")

    client = _build_client(_create, retries=2)

    with pytest.raises(LLMServiceError) as exc_info:
        client.generate_json(
            operation="test_timeout",
            system_prompt="prompt",
            user_payload={"foo": "bar"},
        )

    error = exc_info.value
    assert error.code == "LLM_UPSTREAM_TIMEOUT"
    assert error.retryable is True
    assert error.attempts == 3
    assert call_count["count"] == 3


def test_generate_json_status_error_maps_provider_status() -> None:
    call_count = {"count": 0}

    def _create(**_kwargs):
        call_count["count"] += 1
        raise _DummyStatusError(500)

    client = _build_client(_create, retries=1)

    with pytest.raises(LLMServiceError) as exc_info:
        client.generate_json(
            operation="test_status",
            system_prompt="prompt",
            user_payload={"foo": "bar"},
        )

    error = exc_info.value
    assert error.code == "LLM_UPSTREAM_HTTP_ERROR"
    assert error.provider_status == 500
    assert error.provider_request_id == "req-from-status"
    assert error.attempts == 2
    assert call_count["count"] == 2


def test_generate_json_uses_strict_openai_chat_completions_format() -> None:
    captured: dict = {}

    def _create(**kwargs):
        captured.update(kwargs)
        return _Completion('{"ok": true}')

    client = _build_client(_create, retries=0)

    payload = client.generate_json(
        operation="test_request_format",
        system_prompt="system prompt",
        user_payload={"foo": "bar"},
    )

    assert payload == {"ok": True}
    assert captured["model"] == "test-model"
    assert captured["response_format"] == {"type": "json_object"}
    assert captured["temperature"] == 0.2
    assert isinstance(captured["messages"], list)
    assert captured["messages"][0]["role"] == "system"
    assert captured["messages"][0]["content"] == "system prompt"
    assert captured["messages"][1]["role"] == "user"
    assert '"foo": "bar"' in captured["messages"][1]["content"]


def test_generate_json_does_not_retry_on_400_status() -> None:
    call_count = {"count": 0}

    def _create(**_kwargs):
        call_count["count"] += 1
        raise _DummyStatusError(400)

    client = _build_client(_create, retries=3)

    with pytest.raises(LLMServiceError) as exc_info:
        client.generate_json(
            operation="test_400_no_retry",
            system_prompt="prompt",
            user_payload={"foo": "bar"},
        )

    error = exc_info.value
    assert error.code == "LLM_UPSTREAM_HTTP_ERROR"
    assert error.provider_status == 400
    assert error.retryable is False
    assert error.attempts == 1
    assert call_count["count"] == 1
