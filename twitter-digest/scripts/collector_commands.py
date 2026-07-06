"""Shared collector command construction and child-process error summaries."""

from __future__ import annotations

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
    "passcode",
]


def summarize_collector_error(text: str, returncode: Optional[int] = None) -> str:
    if not text:
        return f"collector exited with code {returncode}" if returncode is not None else ""
    matched = [marker for marker in ERROR_MARKERS if marker in text]
    if matched:
        return "; ".join(dict.fromkeys(matched))
    return " ".join(text.split())[:500]


def api_collector_command(
    python_executable: str,
    scripts_dir: Path,
    out_dir: str | Path,
    *,
    keywords: str,
    max_public_items: int,
    public_window_hours: int,
    dm_max_events: int,
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
        "--dm-max-events",
        str(dm_max_events),
    ]
    if api_base:
        cmd.extend(["--api-base", api_base])
    if user_id:
        cmd.extend(["--user-id", user_id])
    if handle:
        cmd.extend(["--handle", handle.lstrip("@")])
    return cmd
