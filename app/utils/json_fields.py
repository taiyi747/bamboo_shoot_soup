"""Helpers for safely decoding JSON text columns."""

from __future__ import annotations

import json
from typing import Any


def parse_json_array(value: str | None) -> list[Any]:
    """Decode a JSON array string into a Python list."""
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def parse_json_object(value: str | None) -> dict[str, Any]:
    """Decode a JSON object string into a Python dict."""
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
