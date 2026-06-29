"""Public X page scraping helpers."""

from __future__ import annotations

import datetime as dt
import time
from typing import Any

from cdp_client import cdp_call, cdp_eval, wait_for_cdp_page_ws
from dom_script_loader import load_dom_script


def wait_for_public_page_ready(ws_url: str, timeout_sec: int = 20) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if extract_articles(ws_url):
            return
        if len(extract_main_text(ws_url)) > 80:
            return
        time.sleep(0.5)

def collect_public_items(ws_url: str, max_scrolls: int, max_items: int, window_hours: int, min_scrolls: int = 5) -> dict[str, Any]:
    posts: list[dict[str, Any]] = []
    scroll_limit = max(1, int(max_scrolls))
    item_limit = max(1, int(max_items))
    window = max(1, int(window_hours))
    minimum_scrolls = min(scroll_limit, max(0, int(min_scrolls)))
    stagnant_rounds = 0
    previous_count = 0
    window_exceeded = False
    scrolls_used = 0

    for scroll_index in range(scroll_limit):
        scrolls_used = scroll_index + 1
        posts = dedupe_items([*posts, *extract_articles(ws_url)])
        if len(posts) >= item_limit:
            break
        window_exceeded = public_posts_beyond_window(posts, window)
        if window_exceeded and scrolls_used >= minimum_scrolls:
            break
        if len(posts) <= previous_count:
            stagnant_rounds += 1
        else:
            stagnant_rounds = 0
        if stagnant_rounds >= 6 and scrolls_used >= minimum_scrolls:
            break
        previous_count = len(posts)
        cdp_eval(ws_url, "window.scrollBy(0, Math.max(900, window.innerHeight * 0.9));")
        wait_for_public_growth(ws_url, previous_count, timeout_sec=6 if scroll_index < 3 else 4)

    posts = dedupe_items([*posts, *extract_articles(ws_url)])
    if len(posts) > item_limit:
        posts = posts[:item_limit]
    return {
        "items": posts,
        "public_scrolls_used": min(scroll_limit, scrolls_used),
        "public_window_exceeded": window_exceeded,
        "public_max_items": item_limit,
        "public_window_hours": window,
        "public_min_scrolls": minimum_scrolls,
        "public_stagnant_rounds": stagnant_rounds,
    }

def wait_for_public_growth(ws_url: str, previous_count: int, timeout_sec: int = 4) -> None:
    deadline = time.time() + max(1, timeout_sec)
    last_count = 0
    stable_ticks = 0
    while time.time() < deadline:
        current_count = len(extract_articles(ws_url))
        if current_count > previous_count:
            time.sleep(0.4)
            return
        if current_count == last_count:
            stable_ticks += 1
        else:
            stable_ticks = 0
        if stable_ticks >= 3 and current_count > 0:
            return
        last_count = current_count
        time.sleep(0.5)

def public_posts_beyond_window(posts: list[dict[str, Any]], window_hours: int) -> bool:
    now = dt.datetime.now(dt.timezone.utc)
    oldest_age = 0.0
    for post in posts:
        timestamp = str(post.get("time") or "")
        if not timestamp:
            continue
        try:
            parsed = dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        age = (now - parsed.astimezone(dt.timezone.utc)).total_seconds() / 3600
        oldest_age = max(oldest_age, age)
    return oldest_age > max(1, int(window_hours))

def extract_articles(ws_url: str) -> list[dict[str, Any]]:
    script = load_dom_script("extract_articles.js")
    value = cdp_eval(ws_url, script)
    return value if isinstance(value, list) else []

def extract_main_text(ws_url: str) -> str:
    script = load_dom_script("extract_main_text.js")
    value = cdp_eval(ws_url, script)
    return str(value or "")

def detect_handle(port: int) -> str | None:
    try:
        ws_url = wait_for_cdp_page_ws(port)
        cdp_call(ws_url, "Page.enable")
        cdp_call(ws_url, "Runtime.enable")
        cdp_call(ws_url, "Page.navigate", {"url": "https://x.com/home"})
        time.sleep(5)
        script = load_dom_script("detect_handle.js")
        value = cdp_eval(ws_url, script)
        return str(value).lstrip("@") if value else None
    except Exception as exc:
        print(f"Could not auto-detect X handle: {exc}")
        return None

def dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = str(item.get("url") or item.get("text") or "")[:500]
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
