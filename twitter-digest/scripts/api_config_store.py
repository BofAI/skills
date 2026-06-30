"""Shared X API credential storage for twitter-digest scripts."""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from script_utils import ensure_private_dir


STATE_DIR = Path(__file__).resolve().parents[1] / ".state"
API_CONFIG_PATH = STATE_DIR / "api_config.json"
DEFAULT_API_BASE = "https://api.x.com/2"
TOKEN_URL = "https://api.x.com/2/oauth2/token"


def normalize_api_config(data: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(data)
    user_id = str(normalized.get("user_id") or "")
    if user_id and not user_id.isdigit() and not normalized.get("handle"):
        normalized["handle"] = user_id.lstrip("@")
        normalized["user_id"] = ""
    if normalized.get("handle"):
        normalized["handle"] = str(normalized.get("handle") or "").lstrip("@")
    if normalized.get("api_base"):
        normalized["api_base"] = str(normalized.get("api_base") or "").rstrip("/") or DEFAULT_API_BASE
    return normalized


def load_api_config() -> dict[str, Any]:
    if not API_CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(API_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Could not read X API config {API_CONFIG_PATH}: {exc}", flush=True)
        return {}
    if not isinstance(data, dict):
        print(f"X API config {API_CONFIG_PATH} is not a JSON object.", flush=True)
        return {}
    return normalize_api_config(data)


def save_api_config(config: dict[str, Any]) -> None:
    ensure_private_dir(API_CONFIG_PATH.parent)
    payload = json.dumps(normalize_api_config(config), ensure_ascii=False, indent=2) + "\n"
    tmp_path = API_CONFIG_PATH.with_name(f".{API_CONFIG_PATH.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(payload, encoding="utf-8")
        try:
            tmp_path.chmod(0o600)
        except PermissionError:
            pass
        os.replace(tmp_path, API_CONFIG_PATH)
        try:
            API_CONFIG_PATH.chmod(0o600)
        except PermissionError:
            pass
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def clear_api_config() -> None:
    if API_CONFIG_PATH.exists():
        API_CONFIG_PATH.unlink()


def refresh_oauth_token_if_needed(config: dict[str, Any]) -> dict[str, Any]:
    refresh_token = str(config.get("refresh_token") or "")
    client_id = str(config.get("client_id") or "")
    if not refresh_token or not client_id:
        return config
    try:
        expires_at = int(str(config.get("expires_at") or "0"))
    except ValueError:
        expires_at = 0
    if expires_at and expires_at - int(time.time()) > 300:
        return config
    form = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }
    body = urllib.parse.urlencode(form).encode("utf-8")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    client_secret = str(config.get("client_secret") or "")
    if client_secret:
        encoded = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {encoded}"
    request = urllib.request.Request(TOKEN_URL, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            token = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        updated = dict(config)
        updated["refresh_error"] = str(exc)
        updated["refresh_error_at"] = str(int(time.time()))
        print(f"Saved OAuth token could not be refreshed: {exc}. Reauthorization may be required.", flush=True)
        try:
            save_api_config(updated)
        except Exception as save_exc:
            print(f"Could not persist X OAuth refresh error: {save_exc}", flush=True)
        return normalize_api_config(updated)
    access_token = str(token.get("access_token") or "")
    if not access_token:
        return config
    now = int(time.time())
    updated = dict(config)
    updated["bearer_token"] = access_token
    if token.get("refresh_token"):
        updated["refresh_token"] = str(token.get("refresh_token"))
    updated["token_type"] = str(token.get("token_type") or updated.get("token_type") or "bearer")
    updated["expires_in"] = str(token.get("expires_in") or "")
    updated["issued_at"] = str(now)
    updated["expires_at"] = str(now + int(token.get("expires_in") or 0)) if token.get("expires_in") else ""
    updated.pop("refresh_error", None)
    updated.pop("refresh_error_at", None)
    save_api_config(updated)
    print("Refreshed saved X OAuth access token.", flush=True)
    return updated
