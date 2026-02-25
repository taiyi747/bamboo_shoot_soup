"""Replay fallback helpers for LLM generation operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.v1_growth import LLMGenerationReplay
from app.services.llm_client import LLMServiceError, get_llm_client


DEGRADE_REASON_REPLAY_FALLBACK = "replay_fallback"
DEGRADE_REASON_REPLAY_FORCE = "replay_force"


@dataclass
class ReplayGenerationResult:
    payload: dict[str, Any]
    degraded: bool
    degrade_reason: str | None


def _fingerprint(payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def store_replay_payload(
    db: Session,
    *,
    user_id: str,
    operation: str,
    request_payload: dict[str, Any],
    response_payload: dict[str, Any],
) -> None:
    replay = LLMGenerationReplay(
        user_id=user_id,
        operation=operation,
        request_fingerprint=_fingerprint(request_payload),
        payload_json=json.dumps(
            {
                "request_payload": request_payload,
                "response_payload": response_payload,
                "stored_at": datetime.now(timezone.utc).isoformat(),
            },
            ensure_ascii=False,
        ),
    )
    db.add(replay)
    db.commit()


def load_latest_replay_payload(
    db: Session,
    *,
    user_id: str,
    operation: str,
) -> dict[str, Any] | None:
    replay = (
        db.query(LLMGenerationReplay)
        .filter(
            LLMGenerationReplay.user_id == user_id,
            LLMGenerationReplay.operation == operation,
        )
        .order_by(LLMGenerationReplay.created_at.desc(), LLMGenerationReplay.id.desc())
        .first()
    )
    if not replay:
        return None

    try:
        payload = json.loads(replay.payload_json)
    except (TypeError, json.JSONDecodeError):
        return None

    if isinstance(payload, dict) and isinstance(payload.get("response_payload"), dict):
        return payload["response_payload"]
    if isinstance(payload, dict):
        return payload
    return None


def generate_json_with_replay(
    db: Session,
    *,
    user_id: str,
    operation: str,
    system_prompt: str,
    user_payload: dict[str, Any],
    llm_client: Any | None = None,
) -> ReplayGenerationResult:
    settings = get_settings()

    if settings.demo_replay_force:
        replay_payload = load_latest_replay_payload(db, user_id=user_id, operation=operation)
        if replay_payload is None:
            raise LLMServiceError(
                code="LLM_REPLAY_NOT_FOUND",
                message="Replay fallback is forced but no replay payload was found.",
                operation=operation,
                retryable=False,
            )
        return ReplayGenerationResult(
            payload=replay_payload,
            degraded=True,
            degrade_reason=DEGRADE_REASON_REPLAY_FORCE,
        )

    try:
        client = llm_client or get_llm_client()
        payload = client.generate_json(
            operation=operation,
            system_prompt=system_prompt,
            user_payload=user_payload,
        )
        store_replay_payload(
            db,
            user_id=user_id,
            operation=operation,
            request_payload=user_payload,
            response_payload=payload,
        )
        return ReplayGenerationResult(payload=payload, degraded=False, degrade_reason=None)
    except LLMServiceError:
        if not settings.demo_replay_fallback_enabled:
            raise

        replay_payload = load_latest_replay_payload(db, user_id=user_id, operation=operation)
        if replay_payload is None:
            raise

        return ReplayGenerationResult(
            payload=replay_payload,
            degraded=True,
            degrade_reason=DEGRADE_REASON_REPLAY_FALLBACK,
        )
