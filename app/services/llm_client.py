"""LLM 客户端封装：重试、URL 归一化与结构化错误。"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any
from urllib.parse import urlparse, urlunparse

from app.core.config import Settings, get_settings


class LLMServiceError(RuntimeError):
    """Structured error used by routes to return sanitized 502 responses."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        operation: str,
        provider_status: int | None = None,
        provider_request_id: str | None = None,
        retryable: bool = False,
        attempts: int = 1,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.operation = operation
        self.provider_status = provider_status
        self.provider_request_id = provider_request_id
        self.retryable = retryable
        self.attempts = attempts

    def to_detail(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "operation": self.operation,
            "provider_status": self.provider_status,
            "provider_request_id": self.provider_request_id,
            "retryable": self.retryable,
            "attempts": self.attempts,
        }


def llm_schema_error(operation: str, message: str) -> LLMServiceError:
    """构造统一的 schema 校验错误，供路由层转为 502。"""

    return LLMServiceError(
        code="LLM_SCHEMA_VALIDATION_FAILED",
        message=message,
        operation=operation,
        retryable=False,
    )


def normalize_openai_base_url(base_url: str) -> str:
    """
    将 OPENAI_BASE_URL 归一化为 OpenAI SDK 期望的 base_url。

    支持输入：
    - https://api.example.com
    - https://api.example.com/v1
    - https://proxy.example.com/v1/chat/completions
    """
    raw = base_url.strip()
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("OPENAI_BASE_URL must be a valid http/https URL")

    path = parsed.path.rstrip("/")
    if path.lower().endswith("/chat/completions"):
        path = path[: -len("/chat/completions")]
    if not path:
        path = "/v1"

    normalized = urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))
    return normalized.rstrip("/")


def _strip_code_fence(text: str) -> str:
    """兼容部分供应商返回 ```json 包裹文本的情况。"""
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if len(lines) >= 3 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return text


def _extract_request_id(error: Exception) -> str | None:
    """从 OpenAI SDK 异常中尽量提取上游 request id。"""
    request_id = getattr(error, "request_id", None)
    if isinstance(request_id, str) and request_id:
        return request_id

    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    if headers is None:
        return None

    for key in ("x-request-id", "X-Request-Id", "request-id"):
        value = headers.get(key)
        if value:
            return str(value)
    return None


class LLMClient:
    """OpenAI Chat Completions 封装：统一重试、解析与错误映射。"""

    def __init__(self, settings: Settings) -> None:
        settings.validate_llm_settings()

        try:
            import openai
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "openai package is required. Install dependencies before running the API."
            ) from exc

        self._openai = openai
        self._model_name = settings.model_name or ""
        self._max_retries = settings.openai_max_retries
        self._reasoning = settings.reasoning
        self._client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=normalize_openai_base_url(settings.openai_base_url or ""),
            timeout=settings.openai_timeout_seconds,
            max_retries=0,
        )

    def generate_json(
        self,
        *,
        operation: str,
        system_prompt: str,
        user_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        调用 LLM 并返回 JSON 对象。

        重试由错误映射后的 retryable 决定，而不是盲目重试。
        """
        max_attempts = self._max_retries + 1
        for attempt in range(1, max_attempts + 1):
            try:
                return self._generate_json_once(
                    operation=operation,
                    system_prompt=system_prompt,
                    user_payload=user_payload,
                )
            except LLMServiceError as error:
                error.attempts = attempt
                if error.retryable and attempt < max_attempts:
                    continue
                raise

    def _generate_json_once(
        self,
        *,
        operation: str,
        system_prompt: str,
        user_payload: dict[str, Any],
    ) -> dict[str, Any]:
        # 严格保持 OpenAI Chat Completions 请求格式。
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(user_payload, ensure_ascii=False),
            },
        ]

        completion = self._create_completion_with_reason_fallback(
            operation=operation,
            messages=messages,
        )

        request_id = getattr(completion, "_request_id", None)
        content = ""
        if completion.choices:
            content = completion.choices[0].message.content or ""
        content = _strip_code_fence(content.strip())

        if not content:
            raise LLMServiceError(
                code="LLM_INVALID_RESPONSE",
                message="LLM response content is empty.",
                operation=operation,
                provider_request_id=request_id,
                retryable=True,
            )

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMServiceError(
                code="LLM_INVALID_RESPONSE",
                message="LLM response is not valid JSON.",
                operation=operation,
                provider_request_id=request_id,
                retryable=True,
            ) from exc

        if not isinstance(payload, dict):
            raise LLMServiceError(
                code="LLM_INVALID_RESPONSE",
                message="LLM response JSON must be an object.",
                operation=operation,
                provider_request_id=request_id,
                retryable=True,
            )

        return payload

    def _build_completion_request(
        self,
        *,
        messages: list[dict[str, str]],
        include_reasoning: bool,
    ) -> dict[str, Any]:
        request: dict[str, Any] = {
            "model": self._model_name,
            "messages": messages,
            # 严格模式：始终要求上游返回 JSON 对象。
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        if include_reasoning and self._reasoning is not None:
            extra_body: dict[str, Any] = {"reasoning": self._reasoning}
            # Some OpenAI-compatible gateways require this switch to truly disable thinking.
            if self._reasoning is False:
                extra_body["enable_thinking"] = False
            request["extra_body"] = extra_body
        return request

    def _create_completion(
        self,
        *,
        operation: str,
        messages: list[dict[str, str]],
        include_reasoning: bool,
    ) -> Any:
        request = self._build_completion_request(
            messages=messages,
            include_reasoning=include_reasoning,
        )
        try:
            return self._client.chat.completions.create(**request)
        except self._openai.APITimeoutError as exc:
            raise LLMServiceError(
                code="LLM_UPSTREAM_TIMEOUT",
                message="LLM upstream request timed out.",
                operation=operation,
                provider_request_id=_extract_request_id(exc),
                retryable=True,
            ) from exc
        except self._openai.APIConnectionError as exc:
            raise LLMServiceError(
                code="LLM_UPSTREAM_UNAVAILABLE",
                message="LLM upstream connection failed.",
                operation=operation,
                provider_request_id=_extract_request_id(exc),
                retryable=True,
            ) from exc
        except self._openai.APIStatusError as exc:
            status_code = getattr(exc, "status_code", None)
            retryable = bool(
                status_code in {408, 409, 429}
                or (isinstance(status_code, int) and status_code >= 500)
            )
            raise LLMServiceError(
                code="LLM_UPSTREAM_HTTP_ERROR",
                message="LLM upstream returned an HTTP error.",
                operation=operation,
                provider_status=status_code,
                provider_request_id=_extract_request_id(exc),
                retryable=retryable,
            ) from exc
        except Exception as exc:
            raise LLMServiceError(
                code="LLM_CLIENT_ERROR",
                message="Unexpected LLM client error.",
                operation=operation,
                retryable=False,
            ) from exc

    def _create_completion_with_reason_fallback(
        self,
        *,
        operation: str,
        messages: list[dict[str, str]],
    ) -> Any:
        include_reasoning = self._reasoning is not None
        try:
            return self._create_completion(
                operation=operation,
                messages=messages,
                include_reasoning=include_reasoning,
            )
        except LLMServiceError as error:
            if (
                include_reasoning
                and error.code == "LLM_UPSTREAM_HTTP_ERROR"
                and error.provider_status in {400, 422}
            ):
                return self._create_completion(
                    operation=operation,
                    messages=messages,
                    include_reasoning=False,
                )
            raise


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    """构建并缓存进程级 LLM 客户端实例。"""
    return LLMClient(get_settings())


def reset_llm_client_cache() -> None:
    """测试辅助：清理缓存客户端，避免用例间状态污染。"""
    get_llm_client.cache_clear()


def ensure_llm_ready() -> None:
    """启动守卫：校验配置并预热初始化 OpenAI 客户端。"""
    settings = get_settings()
    settings.validate_llm_settings()
    # Validate URL format and dependency load by constructing the client once.
    get_llm_client()
