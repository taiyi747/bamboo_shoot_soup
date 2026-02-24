"""Shared LLM call observability helpers."""

from __future__ import annotations

from time import perf_counter
from typing import Callable

from sqlalchemy.orm import Session

from app.models.llm_call_log import LLMCallLog
from app.services.llm_client import LLMServiceError, get_llm_client


def generate_json_with_observability(
    *,
    db: Session,
    user_id: str | None,
    operation: str,
    system_prompt: str,
    user_payload: dict,
    llm_client_getter: Callable = get_llm_client,
) -> dict:
    """Call LLM and persist a structured observability row."""
    started = perf_counter()
    try:
        payload = llm_client_getter().generate_json(
            operation=operation,
            system_prompt=system_prompt,
            user_payload=user_payload,
        )
        latency_ms = int((perf_counter() - started) * 1000)
        db.add(
            LLMCallLog(
                user_id=user_id,
                operation=operation,
                code="OK",
                retry=0,
                latency_ms=latency_ms,
            )
        )
        db.commit()
        return payload
    except LLMServiceError as exc:
        latency_ms = int((perf_counter() - started) * 1000)
        db.add(
            LLMCallLog(
                user_id=user_id,
                operation=operation,
                code=exc.code,
                retry=max(exc.attempts - 1, 0),
                latency_ms=latency_ms,
                request_id=exc.provider_request_id,
                provider_status=exc.provider_status,
                error_message=exc.message,
            )
        )
        db.commit()
        raise
