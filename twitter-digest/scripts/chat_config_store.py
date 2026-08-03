"""Private X Chat configuration and runtime paths."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from script_utils import ensure_private_dir

STATE_DIR = Path(__file__).resolve().parents[1] / ".state"
CHAT_STATE_DIR = STATE_DIR / "chat"
CHAT_CONFIG_PATH = CHAT_STATE_DIR / "config.json"
CHAT_RUNTIME_DIR = CHAT_STATE_DIR / "runtime"


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


def chat_configured() -> bool:
    config = load_chat_config()
    return bool(config.get("enabled") and config.get("private_key_blob") and config.get("key_version"))
