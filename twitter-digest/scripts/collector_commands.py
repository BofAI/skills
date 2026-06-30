"""Shared collector command construction and child-process error summaries."""

from __future__ import annotations

from pathlib import Path


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


def summarize_collector_error(text: str, returncode: int | None = None) -> str:
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


def browser_collector_command(
    python_executable: str,
    scripts_dir: Path,
    out_dir: str | Path,
    *,
    keywords: str,
    max_public_items: int,
    public_window_hours: int,
    min_public_scrolls: int,
    scrolls: int,
    dm_threads: int,
    dm_list_scrolls: int,
    dm_scrolls: int,
    dm_max_messages: int,
    dm_window_hours: int,
    handle: str = "",
    include_dms: bool = False,
    dm_only: bool = False,
    headed: bool = False,
    headless: bool = False,
    non_interactive: bool = False,
) -> list[str]:
    cmd = [
        python_executable,
        str(scripts_dir / "browser_x_digest.py"),
        "--keywords",
        keywords,
        "--out",
        str(out_dir),
        "--max-public-items",
        str(max_public_items),
        "--public-window-hours",
        str(public_window_hours),
        "--min-public-scrolls",
        str(min_public_scrolls),
        "--scrolls",
        str(scrolls),
        "--dm-threads",
        str(dm_threads),
        "--dm-list-scrolls",
        str(dm_list_scrolls),
        "--dm-scrolls",
        str(dm_scrolls),
        "--dm-max-messages",
        str(dm_max_messages),
        "--dm-window-hours",
        str(dm_window_hours),
    ]
    if handle:
        cmd.extend(["--handle", handle.lstrip("@")])
    if include_dms:
        cmd.append("--include-dms")
    if dm_only:
        cmd.append("--dm-only")
    if headed:
        cmd.append("--headed")
    if headless:
        cmd.append("--headless")
    if non_interactive:
        cmd.append("--non-interactive")
    return cmd
