#!/usr/bin/env python3
"""Collect visible X Chat/DM context through a local logged-in browser profile."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))

import browser_dm_core as browser


DEFAULT_STATE_DIR = ROOT / ".state"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_STATE_DIR / "run"), help="Output directory.")
    parser.add_argument("--profile-dir", default=str(DEFAULT_STATE_DIR / "chrome-profile"))
    parser.add_argument("--login-timeout-sec", type=int, default=300)
    parser.add_argument("--dm-threads", type=int, default=5)
    parser.add_argument("--dm-scrolls", type=int, default=200)
    parser.add_argument("--dm-max-messages", type=int, default=2000)
    parser.add_argument("--dm-window-hours", type=int, default=0)
    parser.add_argument("--headed", action="store_true", help="Open a visible browser window.")
    parser.add_argument("--non-interactive", action="store_true", help="Do not open a visible login/recovery window.")
    parser.add_argument("--keep-browser-open", action="store_true")
    return parser.parse_args()


def render_markdown(data: dict[str, Any]) -> str:
    lines = [
        "# X Browser DM Context",
        "",
        f"- generated_at: `{data.get('generated_at')}`",
        f"- source: `{data.get('source')}`",
        f"- profile_dir: `{data.get('profile_dir')}`",
        "",
        "## DM Facts",
    ]
    page = (data.get("pages") or [{}])[0]
    lines.extend(
        [
            f"- status: `{page.get('dm_status') or ''}`",
            f"- today visible: `{page.get('dm_visible_thread_count', 0)}`",
            f"- last from me: `{page.get('dm_replied_thread_count', 0)}`",
            f"- waiting reply: `{page.get('dm_unreplied_thread_count', 0)}`",
            f"- captured messages: `{page.get('dm_captured_message_count', 0)}`",
            f"- note: {page.get('dm_note') or ''}",
            "",
        ]
    )
    threads = page.get("dm_threads") if isinstance(page.get("dm_threads"), list) else []
    if not threads:
        lines.extend(["## Threads", "", "- None"])
        return "\n".join(lines) + "\n"

    lines.extend(["## Threads", ""])
    for index, thread in enumerate(threads, start=1):
        messages = thread.get("messages") if isinstance(thread.get("messages"), list) else []
        lines.extend(
            [
                f"### {index}. {thread.get('participant') or thread.get('label') or 'unknown'}",
                "",
                f"- reply_state: `{'last_from_me' if thread.get('replied') else 'waiting_reply'}`",
                f"- message_count: `{thread.get('message_count', 0)}`",
                f"- load_complete: `{thread.get('dm_load_complete')}`",
                f"- scrolls_used: `{thread.get('dm_scrolls_used', 0)}`",
                "",
            ]
        )
        for message in messages[-20:]:
            sender = message.get("sender") or "unknown"
            when = message.get("time") or ""
            text = str(message.get("text") or "").replace("\n", " ").strip()
            lines.append(f"- `{sender}` `{when}`: {text}")
        lines.append("")
    return "\n".join(lines) + "\n"


def collect_dm_page(port: int, args: argparse.Namespace) -> dict[str, Any]:
    return browser.collect_page(
        port,
        {"kind": "messages", "url": "https://x.com/messages"},
        scrolls=1,
        dm_threads=args.dm_threads,
        dm_scrolls=args.dm_scrolls,
        dm_max_messages=args.dm_max_messages,
        dm_window_hours=args.dm_window_hours,
    )


def recover_passcode_if_needed(
    page: dict[str, Any],
    proc: Any,
    port: int,
    headless: bool,
    profile_dir: Path,
    args: argparse.Namespace,
) -> tuple[dict[str, Any], Any, int, bool]:
    if page.get("dm_status") != "blocked_by_x_chat_passcode" or args.non_interactive:
        return page, proc, port, headless

    if headless:
        print("X Chat passcode/recovery is required. Opening a visible browser window...")
        browser.stop_browser(proc)
        proc, port = browser.launch_browser(profile_dir, "https://x.com/messages", headless=False)
        headless = False
    else:
        print("X Chat passcode/recovery is required in the visible browser window.")

    if browser.wait_for_dm_passcode_resolution(port, args.login_timeout_sec):
        page = collect_dm_page(port, args)
    else:
        page["collection_status"] = "partial"
        page["collection_error"] = "Timed out waiting for X Chat passcode/recovery to be completed."
        page["dm_note"] = (
            "X Chat asked for passcode/recovery and it was not completed before timeout. "
            "Rerun the collector after completing the visible X challenge."
        )
    return page, proc, port, headless


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out).expanduser().resolve()
    profile_dir = Path(args.profile_dir).expanduser().resolve()
    proc, port, headless, logged_in = browser.ensure_logged_in(
        profile_dir,
        args.login_timeout_sec,
        args.headed,
        args.non_interactive,
    )
    try:
        if not logged_in:
            page = {
                "kind": "messages",
                "url": "https://x.com/messages",
                "items": [],
                "dm_status": "login_required",
                "dm_note": "Saved X login was unavailable and non-interactive mode prevented opening a browser.",
                "dm_threads": [],
                "dm_visible_thread_count": 0,
                "dm_replied_thread_count": 0,
                "dm_unreplied_thread_count": 0,
                "dm_captured_message_count": 0,
            }
        else:
            page = collect_dm_page(port, args)
            page, proc, port, headless = recover_passcode_if_needed(page, proc, port, headless, profile_dir, args)
    finally:
        if not args.keep_browser_open:
            browser.stop_browser(proc)

    data = {
        "generated_at": browser.dt.datetime.now().astimezone().isoformat(),
        "source": "browser_dm",
        "profile_dir": str(profile_dir),
        "pages": [page],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        out_dir.chmod(0o700)
    except PermissionError:
        pass
    (out_dir / "browser-dm-context.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "browser-dm-context.md").write_text(render_markdown(data), encoding="utf-8")
    print(
        json.dumps(
            {
                "source": "browser_dm",
                "markdown": str(out_dir / "browser-dm-context.md"),
                "json": str(out_dir / "browser-dm-context.json"),
                "dm_status": page.get("dm_status"),
                "waiting_reply": page.get("dm_unreplied_thread_count", 0),
                "captured_messages": page.get("dm_captured_message_count", 0),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
