"""Private X Chat configuration and runtime paths."""

from __future__ import annotations

import base64
import binascii
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

from script_utils import ensure_private_dir

STATE_DIR = Path(__file__).resolve().parents[1] / ".state"
CHAT_STATE_DIR = STATE_DIR / "chat"
CHAT_CONFIG_PATH = CHAT_STATE_DIR / "config.json"
CHAT_SIGNING_KEY_CACHE_PATH = CHAT_STATE_DIR / "signing_keys.json"
CHAT_RUNTIME_DIR = CHAT_STATE_DIR / "runtime"
CHATXDK_VERSION = "0.4.3"
SIGNING_KEY_CACHE_TTL_SECONDS = 24 * 60 * 60


def load_chat_config() -> dict[str, Any]:
    if not CHAT_CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(CHAT_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not read X Chat config {CHAT_CONFIG_PATH}: {exc}", flush=True)
        return {}
    return data if isinstance(data, dict) else {}


def save_chat_config(config: dict[str, Any]) -> None:
    ensure_private_dir(CHAT_STATE_DIR)
    payload = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    tmp_path = CHAT_CONFIG_PATH.with_name(f".{CHAT_CONFIG_PATH.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(payload, encoding="utf-8")
        tmp_path.chmod(0o600)
        os.replace(tmp_path, CHAT_CONFIG_PATH)
        CHAT_CONFIG_PATH.chmod(0o600)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def clear_chat_config() -> None:
    if CHAT_CONFIG_PATH.exists():
        CHAT_CONFIG_PATH.unlink()
    clear_signing_key_cache()
    from chat_rate_limit_store import clear_rate_limits

    clear_rate_limits()


def load_signing_key_cache(owner_user_id: str) -> dict[str, Any]:
    if not CHAT_SIGNING_KEY_CACHE_PATH.exists():
        return {"version": 1, "owner_user_id": owner_user_id, "entries": {}}
    try:
        data = json.loads(CHAT_SIGNING_KEY_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "owner_user_id": owner_user_id, "entries": {}}
    if not isinstance(data, dict) or str(data.get("owner_user_id") or "") != owner_user_id:
        return {"version": 1, "owner_user_id": owner_user_id, "entries": {}}
    if not isinstance(data.get("entries"), dict):
        data["entries"] = {}
    return data


def save_signing_key_cache(cache: dict[str, Any]) -> None:
    ensure_private_dir(CHAT_STATE_DIR)
    payload = json.dumps(cache, ensure_ascii=False, indent=2) + "\n"
    tmp_path = CHAT_SIGNING_KEY_CACHE_PATH.with_name(f".{CHAT_SIGNING_KEY_CACHE_PATH.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(payload, encoding="utf-8")
        tmp_path.chmod(0o600)
        os.replace(tmp_path, CHAT_SIGNING_KEY_CACHE_PATH)
        CHAT_SIGNING_KEY_CACHE_PATH.chmod(0o600)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def clear_signing_key_cache() -> None:
    if CHAT_SIGNING_KEY_CACHE_PATH.exists():
        CHAT_SIGNING_KEY_CACHE_PATH.unlink()


def cached_signing_keys(
    owner_user_id: str,
    user_ids: set[str],
    fetch_user_keys: Callable[[str], list[dict[str, Any]]],
    *,
    force_refresh_ids: set[str] | None = None,
    now: float | None = None,
) -> list[dict[str, Any]]:
    current_time = time.time() if now is None else now
    forced = force_refresh_ids or set()
    cache = load_signing_key_cache(owner_user_id)
    entries = cache["entries"]
    changed = False
    result: list[dict[str, Any]] = []
    for user_id in sorted(user_ids):
        entry = entries.get(user_id) if isinstance(entries.get(user_id), dict) else {}
        records = entry.get("records") if isinstance(entry.get("records"), list) else []
        try:
            age = current_time - float(entry.get("fetched_at") or 0)
        except (TypeError, ValueError):
            age = SIGNING_KEY_CACHE_TTL_SECONDS + 1
        if user_id in forced or not records or age < 0 or age > SIGNING_KEY_CACHE_TTL_SECONDS:
            records = fetch_user_keys(user_id)
            if records:
                entries[user_id] = {"fetched_at": current_time, "records": records}
                changed = True
            elif user_id in entries:
                entries.pop(user_id, None)
                changed = True
        result.extend(record for record in records if isinstance(record, dict))
    if changed:
        save_signing_key_cache(cache)
    return result


def chat_configured() -> bool:
    config = load_chat_config()
    if not (config.get("enabled") and config.get("user_id") and config.get("private_key_blob") and config.get("key_version")):
        return False
    try:
        return bool(base64.b64decode(str(config.get("private_key_blob")), validate=True))
    except (ValueError, binascii.Error):
        return False


def chat_runtime_status() -> tuple[bool, str]:
    python = CHAT_RUNTIME_DIR / "bin" / "python"
    if not python.exists():
        return False, "X Chat runtime is missing."
    try:
        probe = subprocess.run(
            [
                str(python),
                "-c",
                (
                    "import importlib.metadata as m; import chat_xdk; "
                    f"raise SystemExit(0 if m.version('chatxdk') == '{CHATXDK_VERSION}' else 2)"
                ),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return False, f"X Chat runtime Python cannot start: {exc}"
    if probe.returncode != 0:
        detail = " ".join((probe.stderr or probe.stdout).split())[:300]
        return False, f"X Chat runtime is broken or not chatxdk {CHATXDK_VERSION}: {detail}".rstrip()
    return True, ""
