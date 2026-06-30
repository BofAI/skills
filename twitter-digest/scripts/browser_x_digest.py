#!/usr/bin/env python3
"""Collect X/Twitter digest input through a persistent local browser session.

Module map:
- CLI options: translate chat-facing requests into collector settings.
- Page routing: decide whether a page uses public scraping or DM scraping.
- Message retries: recover from X Messages loading/skeleton states.
- Main orchestration: browser lifecycle, passcode recovery, incremental output.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import urllib.parse
from pathlib import Path
from typing import Any

from browser_lifecycle import ensure_logged_in, launch_browser, stop_browser, wait_for_login
from cdp_client import cdp_call, cdp_error, wait_for_cdp_page_ws
from digest_io import write_digest_output
from dm_scraper import collect_messages_page, dm_collection_looks_premature, wait_for_dm_passcode_resolution, wait_for_dm_ready
from public_scraper import collect_public_items, detect_handle, wait_for_public_page_ready


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    default_state_dir = Path(__file__).resolve().parents[1] / ".state"
    parser.add_argument("--handle", help="Your X handle, with or without @. If omitted, the script tries to detect it from the logged-in page.")
    parser.add_argument("--keywords", default="", help="Comma-separated keywords or queries for hotspot search.")
    parser.add_argument("--out", default=str(default_state_dir / "run"), help="Output directory.")
    parser.add_argument("--profile-dir", default=str(default_state_dir / "chrome-profile"), help="Dedicated browser profile directory used to persist X login/session state.")
    parser.add_argument("--scrolls", type=int, default=40, help="Maximum scroll rounds per public page.")
    parser.add_argument("--min-public-scrolls", type=int, default=5, help="Minimum public-page scroll rounds before early stop rules can end collection.")
    parser.add_argument("--max-public-items", type=int, default=100, help="Maximum public post items kept per browser run.")
    parser.add_argument("--public-window-hours", type=int, default=24, help="Stop loading older public timeline items once posts beyond this window are detected.")
    parser.add_argument("--login-timeout-sec", type=int, default=300)
    parser.add_argument("--include-dms", action="store_true", help="Also visit X messages and capture visible conversation text.")
    parser.add_argument("--dm-only", action="store_true", help="Debug mode: collect only X messages.")
    parser.add_argument("--dm-threads", type=int, default=5, help="Maximum recent DM threads to open when DM collection is enabled.")
    parser.add_argument("--dm-list-scrolls", type=int, default=20, help="Maximum downward scroll rounds used to scan today's DM conversation list.")
    parser.add_argument("--dm-scrolls", type=int, default=200, help="Maximum upward scroll rounds per opened DM thread.")
    parser.add_argument("--dm-max-messages", type=int, default=2000, help="Maximum message bubbles kept per opened DM thread.")
    parser.add_argument("--dm-window-hours", type=int, default=0, help="Stop loading older DM history once messages beyond this window are detected. 0 means load the full thread available in the browser.")
    parser.add_argument("--headless", action="store_true", help="Run without a visible browser window. This is the default after first login.")
    parser.add_argument("--headed", action="store_true", help="Force a visible browser window for debugging or manual login.")
    parser.add_argument("--non-interactive", action="store_true", help="Do not open a visible browser for DM passcode recovery; record a data gap instead.")
    parser.add_argument("--keep-browser-open", action="store_true", help="Leave the launched browser process running after collection for manual debugging.")
    return parser.parse_args()


def build_pages(handle: str | None, keywords: str, include_dms: bool, dm_only: bool = False) -> list[dict[str, str]]:
    if dm_only:
        return [{"kind": "messages", "url": "https://x.com/messages"}] if include_dms else []
    pages = [{"kind": "home", "url": "https://x.com/home"}]
    if handle:
        clean = handle.lstrip("@")
        query = urllib.parse.quote(f"@{clean}")
        pages.append({"kind": "own_profile", "url": f"https://x.com/{clean}"})
        pages.append({"kind": "mentions_search", "url": f"https://x.com/search?q={query}&src=typed_query&f=live"})
        pages.append({"kind": "mentions_notifications", "url": "https://x.com/notifications/mentions"})
    for index, keyword in enumerate([k.strip() for k in keywords.split(",") if k.strip()], start=1):
        pages.append(
            {
                "kind": f"keyword_{index}",
                "url": f"https://x.com/search?q={urllib.parse.quote(keyword)}&src=typed_query&f=live",
            }
        )
    if include_dms:
        pages.append({"kind": "messages", "url": "https://x.com/messages"})
    return pages


def collect_page(
    port: int,
    page: dict[str, str],
    scrolls: int,
    dm_threads: int = 5,
    dm_list_scrolls: int = 20,
    dm_scrolls: int = 200,
    dm_max_messages: int = 2000,
    dm_window_hours: int = 0,
    max_public_items: int = 100,
    public_window_hours: int = 24,
    min_public_scrolls: int = 5,
) -> dict[str, Any]:
    ws_url = wait_for_cdp_page_ws(port)
    cdp_call(ws_url, "Page.enable")
    cdp_call(ws_url, "Runtime.enable")
    navigate_result = cdp_call(ws_url, "Page.navigate", {"url": page["url"]})
    if cdp_error(navigate_result):
        return {
            "kind": page["kind"],
            "url": page["url"],
            "items": [],
            "collection_status": "error",
            "collection_error": navigate_result["_cdp_error"],
        }
    if page["kind"] == "messages":
        extra = collect_messages_with_retries(
            ws_url,
            page["url"],
            dm_threads,
            dm_list_scrolls,
            dm_scrolls,
            dm_max_messages,
            dm_window_hours,
        )
        return {"kind": page["kind"], "url": page["url"], "items": [], **extra}
    wait_for_public_page_ready(ws_url, timeout_sec=20)
    extra = collect_public_items(ws_url, max_scrolls=scrolls, max_items=max_public_items, window_hours=public_window_hours, min_scrolls=min_public_scrolls)
    return {"kind": page["kind"], "url": page["url"], **extra}


def collect_messages_with_retries(
    ws_url: str,
    url: str,
    dm_threads: int,
    dm_list_scrolls: int,
    dm_scrolls: int,
    dm_max_messages: int,
    dm_window_hours: int,
    max_attempts: int = 3,
) -> dict[str, Any]:
    extra: dict[str, Any] = {}
    for attempt in range(1, max_attempts + 1):
        wait_for_dm_ready(ws_url, timeout_sec=25)
        extra = collect_messages_page(ws_url, dm_threads, dm_scrolls, dm_max_messages, dm_window_hours, dm_list_scrolls)
        if not dm_collection_looks_premature(extra):
            break
        extra["dm_retry_attempts"] = attempt
        if attempt < max_attempts:
            print(f"X Messages still appears to be loading or incomplete. Reloading messages page (attempt {attempt + 1}/{max_attempts})...", flush=True)
            cdp_call(ws_url, "Page.navigate", {"url": url})
            wait_for_dm_ready(ws_url, timeout_sec=25)
    if dm_collection_looks_premature(extra):
        original_status = str(extra.get("dm_status") or "unknown")
        extra["dm_original_status"] = original_status
        extra["dm_status"] = "dm_page_loading_timeout"
        extra["collection_status"] = "partial"
        extra["collection_error"] = "X Messages did not finish loading before retry budget was exhausted."
        extra["dm_note"] = (
            f"X Messages page stayed in a loading/skeleton state after {max_attempts} attempts. "
            "DM content was not treated as empty; rerun later or use --headed to inspect the page."
        )
    return extra


def error_page(page: dict[str, str], exc: BaseException) -> dict[str, Any]:
    return {
        "kind": page.get("kind") or "unknown",
        "url": page.get("url") or "",
        "items": [],
        "collection_status": "error",
        "collection_error": str(exc) or exc.__class__.__name__,
    }


def main() -> None:
    args = parse_args()
    if args.dm_only:
        args.include_dms = True
    profile_dir = Path(args.profile_dir).expanduser().resolve()
    force_headed = bool(args.headed and not args.headless)
    proc, port, headless, logged_in = ensure_logged_in(profile_dir, args.login_timeout_sec, force_headed, args.non_interactive)
    try:
        out_dir = Path(args.out).expanduser().resolve()
        if not logged_in:
            data = {
                "generated_at": dt.datetime.now().astimezone().isoformat(),
                "profile_dir": str(profile_dir),
                "handle": args.handle.lstrip("@") if args.handle else None,
                "keywords": [k.strip() for k in args.keywords.split(",") if k.strip()],
                "pages": [
                    {
                        "kind": "login",
                        "url": "https://x.com/home",
                        "items": [],
                        "collection_status": "skipped",
                        "collection_error": "Saved X login unavailable in non-interactive mode.",
                    }
                ],
            }
            write_digest_output(out_dir, data)
            print(json.dumps({"out_dir": str(out_dir), "pages": len(data["pages"]), "headless": headless, "login": "unavailable"}, indent=2))
            return
        handle = args.handle.lstrip("@") if args.handle else detect_handle(port)
        if handle:
            print(f"Using X handle: @{handle}")
        else:
            print("Could not auto-detect X handle. Mention search will be skipped unless --handle is provided.")
        pages = build_pages(handle, args.keywords, args.include_dms, args.dm_only)
        data = {
            "generated_at": dt.datetime.now().astimezone().isoformat(),
            "profile_dir": str(profile_dir),
            "handle": handle,
            "keywords": [k.strip() for k in args.keywords.split(",") if k.strip()],
            "pages": [],
        }
        for page in pages:
            print(f"Collecting {page['kind']}: {page['url']}")
            try:
                if page["kind"] == "messages" and headless:
                    stop_browser(proc)
                    proc, port = launch_browser(profile_dir, "https://x.com/messages", headless=True)
                    wait_for_login(port, args.login_timeout_sec, interactive=False)
                result = collect_page(
                    port,
                    page,
                    args.scrolls,
                    args.dm_threads,
                    args.dm_list_scrolls,
                    args.dm_scrolls,
                    args.dm_max_messages,
                    args.dm_window_hours,
                    args.max_public_items,
                    args.public_window_hours,
                    args.min_public_scrolls,
                )
                if page["kind"] == "messages" and result.get("dm_status") == "blocked_by_x_chat_passcode":
                    if args.non_interactive:
                        result["dm_note"] = "X Chat passcode is required. Non-interactive mode skipped DM recovery for this run."
                        data["pages"].append(result)
                        write_digest_output(out_dir, data)
                        continue
                    resume_headless_after_passcode = bool(headless)
                    if headless:
                        print("DM passcode screen detected in headless mode. Reopening X Messages in a visible browser window...")
                        stop_browser(proc)
                        proc, port = launch_browser(profile_dir, "https://x.com/messages", headless=False)
                        headless = False
                        wait_for_login(port, args.login_timeout_sec, interactive=True)
                    if wait_for_dm_passcode_resolution(port, args.login_timeout_sec):
                        if resume_headless_after_passcode:
                            print("X Chat passcode was completed. Returning to headless mode before DM collection...")
                            stop_browser(proc)
                            proc, port = launch_browser(profile_dir, "https://x.com/messages", headless=True)
                            headless = True
                            wait_for_login(port, args.login_timeout_sec, interactive=False)
                        result = collect_page(
                            port,
                            page,
                            args.scrolls,
                            args.dm_threads,
                            args.dm_list_scrolls,
                            args.dm_scrolls,
                            args.dm_max_messages,
                            args.dm_window_hours,
                            args.max_public_items,
                            args.public_window_hours,
                            args.min_public_scrolls,
                        )
                    else:
                        result["dm_note"] = (
                            "Timed out waiting for X Messages to become readable after passcode handling. "
                            "Keep the visible browser window open, complete passcode setup or entry until the inbox is visible, then rerun the digest."
                        )
            except SystemExit as exc:
                result = error_page(page, exc)
                print(f"Collection failed for {page['kind']}: {result['collection_error']}", flush=True)
            except Exception as exc:
                result = error_page(page, exc)
                print(f"Collection failed for {page['kind']}: {result['collection_error']}", flush=True)
            data["pages"].append(result)
            write_digest_output(out_dir, data)
        write_digest_output(out_dir, data)
        print(json.dumps({"out_dir": str(out_dir), "pages": len(data["pages"]), "headless": headless}, indent=2))
    finally:
        if not args.keep_browser_open:
            stop_browser(proc)


if __name__ == "__main__":
    main()
