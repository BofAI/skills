"""Shared collector command construction and child-process error summaries."""

from __future__ import annotations

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


def summarize_collector_error(text: str, returncode: Optional[int] = None) -> str:
    if not text:
        return f"collector exited with code {returncode}" if returncode is not None else ""
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
