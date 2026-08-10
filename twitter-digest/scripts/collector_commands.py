"""Shared collector command construction and child-process error summaries."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Optional


ERROR_MARKERS = [
    "client-not-enrolled",
    "Appropriate Level of API Access",
    "Unauthorized",
    "Forbidden",
    "HTTP 401",
    "HTTP 403",
    "HTTP 429",
    "Too Many Requests",
    "Timed out",
    "UNEXPECTED_EOF_WHILE_READING",
    "EOF occurred in violation of protocol",
    "passcode",
]
STRUCTURED_ERROR_PREFIX = "TWITTER_DIGEST_API_ERROR "
ALLOWED_ERROR_SOURCES = {"x_chat"}
ALLOWED_ERROR_ENDPOINTS = {
    "conversation_list",
    "conversation_events",
    "public_keys",
    "x_chat_other",
}


def endpoint_category(path: str) -> str:
    clean_path = path.split("?", 1)[0]
    if clean_path == "/chat/conversations":
        return "conversation_list"
    if clean_path.startswith("/chat/conversations/") and clean_path.endswith("/events"):
        return "conversation_events"
    if clean_path.startswith("/users/") and clean_path.endswith("/public_keys"):
        return "public_keys"
    return "x_chat_other"


def structured_api_error(
    source: str,
    endpoint: str,
    status: int,
    retry_after_seconds: int | None = None,
) -> str:
    payload: dict[str, object] = {
        "source": source if source in ALLOWED_ERROR_SOURCES else "x_chat",
        "endpoint": endpoint if endpoint in ALLOWED_ERROR_ENDPOINTS else "x_chat_other",
        "status": int(status),
    }
    if retry_after_seconds is not None:
        payload["retry_after_seconds"] = max(0, int(retry_after_seconds))
    return STRUCTURED_ERROR_PREFIX + json.dumps(payload, separators=(",", ":"), sort_keys=True)


def parse_structured_api_error(text: str) -> dict[str, object] | None:
    for line in text.splitlines():
        marker_at = line.find(STRUCTURED_ERROR_PREFIX)
        if marker_at < 0:
            continue
        try:
            payload = json.loads(line[marker_at + len(STRUCTURED_ERROR_PREFIX) :])
            source = str(payload.get("source") or "")
            endpoint = str(payload.get("endpoint") or "")
            status = int(payload.get("status"))
        except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
            continue
        if source not in ALLOWED_ERROR_SOURCES or endpoint not in ALLOWED_ERROR_ENDPOINTS:
            continue
        result: dict[str, object] = {"source": source, "endpoint": endpoint, "status": status}
        retry_after = payload.get("retry_after_seconds")
        if retry_after is not None:
            try:
                result["retry_after_seconds"] = max(0, int(retry_after))
            except (TypeError, ValueError):
                pass
        return result
    return None


def friendly_chat_collection_error(summary: str) -> str:
    error = parse_structured_api_error(summary)
    if not error or int(error.get("status") or 0) != 429:
        return summary
    labels = {
        "conversation_list": "X Chat 会话列表暂时受到限流",
        "conversation_events": "X Chat 消息读取暂时受到限流",
        "public_keys": "X Chat 公钥读取暂时受到限流",
        "x_chat_other": "X Chat 接口暂时受到限流",
    }
    message = labels.get(str(error.get("endpoint") or ""), labels["x_chat_other"])
    retry_after = error.get("retry_after_seconds")
    if retry_after is not None:
        minutes = max(1, math.ceil(int(retry_after) / 60))
        return f"{message}，预计约 {minutes} 分钟后恢复。请稍后再生成日报。"
    return f"{message}。请稍后再生成日报。"


def summarize_collector_error(text: str, returncode: Optional[int] = None) -> str:
    if not text:
        return f"collector exited with code {returncode}" if returncode is not None else ""
    structured = parse_structured_api_error(text)
    if structured:
        return structured_api_error(
            str(structured["source"]),
            str(structured["endpoint"]),
            int(structured["status"]),
            int(structured["retry_after_seconds"]) if "retry_after_seconds" in structured else None,
        )
    matched = [marker for marker in ERROR_MARKERS if marker in text]
    if matched:
        summary = "; ".join(dict.fromkeys(matched))
        retry_match = re.search(r"retry after about (\d+) seconds", text, re.IGNORECASE)
        if retry_match:
            summary += f"; retry after about {retry_match.group(1)} seconds"
        return summary
    # Tracebacks put the useful exception at the end. Keep the tail so the
    # actual network/API error is not replaced by an unhelpful urllib stack.
    compact = " ".join(text.split())
    return compact[-500:]


def api_collector_command(
    python_executable: str,
    scripts_dir: Path,
    out_dir: str | Path,
    *,
    keywords: str,
    max_public_items: int,
    public_window_hours: int,
    api_base: str = "",
    user_id: str = "",
    handle: str = "",
) -> list[str]:
    cmd = [
        python_executable,
        str(scripts_dir / "api_x_digest.py"),
        "--keywords",
        keywords,
        "--out",
        str(out_dir),
        "--max-public-items",
        str(max_public_items),
        "--public-window-hours",
        str(public_window_hours),
    ]
    if api_base:
        cmd.extend(["--api-base", api_base])
    if user_id:
        cmd.extend(["--user-id", user_id])
    if handle:
        cmd.extend(["--handle", handle.lstrip("@")])
    return cmd
