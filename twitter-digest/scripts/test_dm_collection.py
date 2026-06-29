#!/usr/bin/env python3
"""Smoke test X Chat collection without running the full daily digest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from browser_lifecycle import ensure_logged_in, stop_browser
from browser_x_digest import collect_page


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE_DIR = ROOT / ".state" / "chrome-profile"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile-dir", default=str(DEFAULT_PROFILE_DIR))
    parser.add_argument("--login-timeout-sec", type=int, default=300)
    parser.add_argument("--dm-threads", type=int, default=5)
    parser.add_argument("--dm-list-scrolls", type=int, default=20)
    parser.add_argument("--dm-scrolls", type=int, default=200)
    parser.add_argument("--dm-max-messages", type=int, default=2000)
    parser.add_argument("--dm-window-hours", type=int, default=0)
    parser.add_argument("--headed", action="store_true", help="Open a visible browser window.")
    parser.add_argument("--non-interactive", action="store_true", help="Do not open a visible login window if the saved session is unavailable.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    proc, port, *_ = ensure_logged_in(
        Path(args.profile_dir).expanduser().resolve(),
        args.login_timeout_sec,
        args.headed,
        args.non_interactive,
    )
    try:
        result = collect_page(
            port,
            {"kind": "messages", "url": "https://x.com/messages"},
            scrolls=1,
            dm_threads=args.dm_threads,
            dm_list_scrolls=args.dm_list_scrolls,
            dm_scrolls=args.dm_scrolls,
            dm_max_messages=args.dm_max_messages,
            dm_window_hours=args.dm_window_hours,
        )
    finally:
        stop_browser(proc)

    summary = {
        "dm_status": result.get("dm_status"),
        "today_visible": result.get("dm_visible_thread_count", 0),
        "last_from_me": result.get("dm_replied_thread_count", 0),
        "waiting_reply": result.get("dm_unreplied_thread_count", 0),
        "captured_messages": result.get("dm_captured_message_count", 0),
        "list_scrolls_used": result.get("dm_list_scrolls_used", 0),
        "list_load_complete": result.get("dm_list_load_complete", False),
        "retry_attempts": result.get("dm_retry_attempts", 0),
        "loading_state": result.get("dm_loading_state", {}),
        "dm_note": result.get("dm_note", ""),
        "threads": [],
    }
    for thread in result.get("dm_threads") or []:
        messages = thread.get("messages") if isinstance(thread.get("messages"), list) else []
        summary["threads"].append(
            {
                "participant": thread.get("participant"),
                "reply_state": "last_from_me" if thread.get("replied") else "waiting_reply",
                "message_count": thread.get("message_count", 0),
                "scrolls_used": thread.get("dm_scrolls_used", 0),
                "window_exceeded": thread.get("dm_window_exceeded", False),
                "hit_message_cap": thread.get("dm_hit_message_cap", False),
                "load_complete": thread.get("dm_load_complete", False),
                "first_message": messages[0] if messages else None,
                "last_message": messages[-1] if messages else None,
            }
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
