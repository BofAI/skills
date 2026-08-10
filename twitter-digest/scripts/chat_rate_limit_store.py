"""Owner-only, sanitized X Chat rate-limit cooldown state."""

from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path
from typing import Any

from script_utils import ensure_private_dir


CHAT_STATE_DIR = Path(__file__).resolve().parents[1] / ".state" / "chat"
RATE_LIMIT_PATH = CHAT_STATE_DIR / "rate_limits.json"
ALLOWED_ENDPOINTS = {"conversation_list", "conversation_events", "public_keys"}


def _load() -> dict[str, dict[str, Any]]:
    if not RATE_LIMIT_PATH.exists():
        return {}
    try:
        data = json.loads(RATE_LIMIT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        endpoint: record
        for endpoint, record in data.items()
        if endpoint in ALLOWED_ENDPOINTS and isinstance(record, dict)
    }


def _save(data: dict[str, dict[str, Any]]) -> None:
    if not data:
        clear_rate_limits()
        return
    ensure_private_dir(CHAT_STATE_DIR)
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp_path = RATE_LIMIT_PATH.with_name(f".{RATE_LIMIT_PATH.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(payload, encoding="utf-8")
        tmp_path.chmod(0o600)
        os.replace(tmp_path, RATE_LIMIT_PATH)
        RATE_LIMIT_PATH.chmod(0o600)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def record_rate_limit(
    endpoint: str,
    retry_after_seconds: int | None,
    now: float | None = None,
) -> None:
    if endpoint not in ALLOWED_ENDPOINTS or retry_after_seconds is None:
        return
    try:
        delay = int(retry_after_seconds)
    except (TypeError, ValueError):
        return
    if delay <= 0:
        return
    current_time = time.time() if now is None else now
    data = _load()
    data[endpoint] = {
        "endpoint": endpoint,
        "retry_after_epoch": current_time + delay,
    }
    _save(data)


def active_rate_limit(endpoint: str, now: float | None = None) -> int | None:
    if endpoint not in ALLOWED_ENDPOINTS:
        return None
    data = _load()
    record = data.get(endpoint)
    if not isinstance(record, dict):
        return None
    try:
        remaining = float(record.get("retry_after_epoch")) - (time.time() if now is None else now)
    except (TypeError, ValueError):
        data.pop(endpoint, None)
        _save(data)
        return None
    if remaining <= 0:
        data.pop(endpoint, None)
        _save(data)
        return None
    return max(1, math.ceil(remaining))


def clear_rate_limits() -> None:
    if RATE_LIMIT_PATH.exists():
        RATE_LIMIT_PATH.unlink()
