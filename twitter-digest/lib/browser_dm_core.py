#!/usr/bin/env python3
"""Internal browser/CDP helpers for collecting visible X Chat/DM context."""

from __future__ import annotations

import base64
import datetime as dt
import json
import os
import re
import shutil
import socket
import struct
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any


def find_chrome() -> str:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "microsoft-edge",
        "brave-browser",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.is_absolute() and path.exists():
            return candidate
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise SystemExit("No supported Chromium browser found. Install Chrome, Chromium, Edge, or Brave.")


def get_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def launch_browser(profile_dir: Path, start_url: str, headless: bool) -> tuple[subprocess.Popen[bytes], int]:
    profile_dir.mkdir(parents=True, exist_ok=True)
    port = get_free_port()
    command = [
        find_chrome(),
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        start_url,
    ]
    if headless:
        command.extend(["--headless=new", "--disable-gpu", "--window-size=1440,1200"])
    proc = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_for_cdp(port)
    except BaseException:
        stop_browser(proc)
        raise
    return proc, port


def ensure_logged_in(profile_dir: Path, timeout_sec: int, force_headed: bool, non_interactive: bool) -> tuple[subprocess.Popen[bytes], int, bool, bool]:
    if force_headed:
        proc, port = launch_browser(profile_dir, "https://x.com/home", headless=False)
        wait_for_login(port, timeout_sec, interactive=True)
        return proc, port, False, True

    proc, port = launch_browser(profile_dir, "https://x.com/home", headless=True)
    if is_logged_in(port):
        print("X login detected in saved browser session. Continuing headless collection...")
        return proc, port, True, True

    if non_interactive:
        print("Saved X login was not available. Non-interactive mode will record a login data gap without opening a browser.")
        return proc, port, True, False

    print("Saved X login was not available. Opening a visible browser window for one-time login...")
    stop_browser(proc)
    proc, port = launch_browser(profile_dir, "https://x.com/home", headless=False)
    wait_for_login(port, timeout_sec, interactive=True)
    return proc, port, False, True


def is_logged_in(port: int) -> bool:
    try:
        ws_url = wait_for_cdp_page_ws(port)
        return has_x_login_cookie(ws_url)
    except Exception:
        return False


def wait_for_login(port: int, timeout_sec: int, interactive: bool) -> None:
    if interactive:
        print("Waiting for X login in the opened browser window...")
    else:
        print("Waiting for X login...")
    deadline = time.time() + timeout_sec
    last_notice = 0.0
    while time.time() < deadline:
        try:
            ws_url = wait_for_cdp_page_ws(port)
            if has_x_login_cookie(ws_url):
                print("X login detected. Continuing with browser collection...")
                return
        except Exception:
            pass
        if time.time() - last_notice > 15:
            if interactive:
                print("Still waiting for X login. Log in once in the opened browser window.")
            else:
                print("Still waiting for X login.")
            last_notice = time.time()
        time.sleep(2)
    raise SystemExit("Timed out waiting for X login.")


def stop_browser(proc: subprocess.Popen[bytes]) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def has_x_login_cookie(ws_url: str) -> bool:
    for cookie in cdp_get_all_cookies(ws_url):
        if cookie.get("name") == "auth_token" and domain_matches_x(str(cookie.get("domain") or "")):
            return True
    return False


def domain_matches_x(domain: str) -> bool:
    domain = domain.lstrip(".").lower()
    return domain == "x.com" or domain.endswith(".x.com") or domain == "twitter.com" or domain.endswith(".twitter.com")


def collect_page(
    port: int,
    page: dict[str, str],
    scrolls: int,
    dm_threads: int = 5,
    dm_scrolls: int = 200,
    dm_max_messages: int = 2000,
    dm_window_hours: int = 0,
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
    time.sleep(5)
    if page["kind"] != "messages":
        return {
            "kind": page["kind"],
            "url": page["url"],
            "items": [],
            "collection_status": "skipped",
            "collection_error": "browser_dm_core only collects X Messages.",
        }
    extra = collect_messages_page(ws_url, dm_threads, dm_scrolls, dm_max_messages, dm_window_hours)
    if dm_collection_looks_premature(extra):
        cdp_call(ws_url, "Page.navigate", {"url": page["url"]})
        time.sleep(8)
        extra = collect_messages_page(ws_url, dm_threads, dm_scrolls, dm_max_messages, dm_window_hours)
        if dm_collection_looks_premature(extra):
            mark_dm_loading_gap(extra)
    return {"kind": page["kind"], "url": page["url"], "items": [], **extra}


def collect_messages_page(ws_url: str, dm_threads: int, dm_scrolls: int, dm_max_messages: int, dm_window_hours: int) -> dict[str, Any]:
    extra: dict[str, Any] = {}
    extra["visible_text"] = extract_main_text(ws_url)
    extra.update(
        collect_dm_threads(
            ws_url,
            max_threads=dm_threads,
            dm_scrolls=dm_scrolls,
            dm_max_messages=dm_max_messages,
            dm_window_hours=dm_window_hours,
        )
    )
    return extra


def dm_collection_looks_premature(extra: dict[str, Any]) -> bool:
    status = str(extra.get("dm_status") or "")
    text = " ".join(str(extra.get("visible_text") or "").lower().split())
    if status not in {"no_today_threads", "no_visible_threads", "visible_threads_unopened"}:
        return False
    if "start conversation" not in text:
        return False
    conversation_markers = [
        r"\byou\s*:",
        r"\byou sent\b",
        r"\bnow\b",
        r"\b\d+\s*(m|min|mins|minute|minutes|h|hr|hrs|hour|hours)\b",
        r"\btoday\b",
        r"今天",
    ]
    return not any(re.search(marker, text, re.IGNORECASE) for marker in conversation_markers)


def mark_dm_loading_gap(extra: dict[str, Any]) -> None:
    original_status = str(extra.get("dm_status") or "unknown")
    extra["dm_original_status"] = original_status
    extra["dm_status"] = "dm_page_loading_timeout"
    extra["dm_note"] = (
        "X Messages still looked like a loading skeleton after retry. "
        f"The provisional status was `{original_status}`, but this should be treated as a DM loading gap, not as an empty inbox."
    )
    extra["collection_status"] = "partial"
    extra["collection_error"] = "X Messages page did not finish loading; DM conversation counts may be incomplete."


def collect_dm_threads(ws_url: str, max_threads: int, dm_scrolls: int, dm_max_messages: int, dm_window_hours: int) -> dict[str, Any]:
    main_text = wait_for_dm_ready(ws_url)
    if is_dm_passcode_screen(main_text):
        return {
            "dm_status": "blocked_by_x_chat_passcode",
            "dm_note": "X Chat is asking for an encryption passcode before message content is visible.",
            "dm_threads": [],
            **dm_counts([]),
        }

    all_targets = extract_dm_thread_targets(ws_url)
    today_targets = today_dm_targets(all_targets)
    thread_targets = unreplied_dm_targets(today_targets)
    counts = dm_counts(today_targets)
    if not thread_targets:
        if today_targets:
            return {
                "dm_status": "no_unreplied_threads",
                "dm_note": (
                    f"DM conversation list was visible with {counts['dm_visible_thread_count']} today thread target(s), "
                    "but every latest preview appears to be from you."
                ),
                "dm_threads": [],
                **counts,
            }
        if all_targets:
            return {
                "dm_status": "no_today_threads",
                "dm_note": f"DM conversation list was visible with {len(all_targets)} older thread target(s), but no today conversation targets were found.",
                "dm_threads": [],
                **counts,
            }
        if looks_like_dm_list_text(main_text):
            return {
                "dm_status": "visible_threads_unopened",
                "dm_note": "DM conversation list text was visible, but no unreplied openable conversation link or row target could be detected.",
                "dm_threads": [],
                **counts,
            }
        return {
            "dm_status": "no_visible_threads",
            "dm_note": "No DM conversation links or clickable conversation rows were visible after waiting for the messages page.",
            "dm_threads": [],
            **counts,
        }

    threads: list[dict[str, Any]] = []
    seen_targets: set[str] = set()
    for _ in range(max(max_threads, 0)):
        thread_targets = [target for target in unreplied_dm_targets(today_dm_targets(extract_dm_thread_targets(ws_url))) if dm_target_key(target) not in seen_targets]
        if not thread_targets:
            break
        target = thread_targets[0]
        seen_targets.add(dm_target_key(target))
        if float(target.get("x") or 0) > 0 and float(target.get("y") or 0) > 0:
            click_point(ws_url, float(target.get("x") or 0), float(target.get("y") or 0))
        elif target.get("url"):
            cdp_call(ws_url, "Page.navigate", {"url": str(target["url"])})
        time.sleep(4)
        load_info = load_dm_thread_history(ws_url, max_scrolls=dm_scrolls, target_messages=dm_max_messages, window_hours=dm_window_hours)
        messages = extract_dm_messages(ws_url, max_messages=dm_max_messages)
        thread_text = render_dm_messages(messages) or extract_dm_conversation_text(ws_url)
        message_count = len(messages) if messages else count_dm_messages(ws_url)
        threads.append(
            {
                "url": str(target.get("url") or ""),
                "label": str(target.get("label") or ""),
                "participant": dm_participant(target),
                "target_type": str(target.get("target_type") or ""),
                "replied": bool(target.get("replied")),
                "reply_reason": str(target.get("reply_reason") or ""),
                "today": bool(target.get("today")),
                "message_count": message_count,
                "dm_scrolls_used": load_info.get("scrolls_used", 0),
                "dm_load_complete": load_info.get("load_complete", False),
                "dm_window_exceeded": load_info.get("window_exceeded", False),
                "dm_hit_message_cap": load_info.get("hit_message_cap", False),
                "messages": messages,
                "text": thread_text,
            }
        )
        cdp_call(ws_url, "Page.navigate", {"url": "https://x.com/messages"})
        wait_for_dm_ready(ws_url, timeout_sec=8)

    return {
        "dm_status": "captured_unreplied_threads" if threads else "no_unreplied_threads",
        "dm_note": (
            f"Today visible DM threads: {counts['dm_visible_thread_count']}; latest from you: {counts['dm_replied_thread_count']}; "
            f"waiting for your reply: {counts['dm_unreplied_thread_count']}. Opened up to {max_threads} waiting-reply thread(s); "
            f"loaded up to {dm_max_messages} message bubbles per thread with {dm_scrolls} upward scroll round(s); "
            f"captured message bubbles: {sum(int(thread.get('message_count') or 0) for thread in threads)}."
        ),
        "dm_threads": threads,
        "dm_captured_message_count": sum(int(thread.get("message_count") or 0) for thread in threads),
        **counts,
    }


def dm_target_key(target: dict[str, Any]) -> str:
    return str(target.get("url") or target.get("label") or f"{target.get('x')}:{target.get('y')}")


def dm_participant(target: dict[str, Any]) -> str:
    label = " ".join(str(target.get("label") or "").split())
    handle = re.search(r"@([A-Za-z0-9_]{1,15})", label)
    if handle:
        return "@" + handle.group(1)
    first_chunk = re.split(
        r"(?:\s+You:|\s+You sent|\s+You replied|\s+sent you|\s+你[:：]|\s+你已发送|\s+你发送|\s+您[:：]|\s+\d+\s*(?:m|h|d|min|hour|day)\b)",
        label,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return first_chunk.strip(" -·•|")[:80] or label[:80]


def unreplied_dm_targets(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [target for target in targets if not bool(target.get("replied"))]


def today_dm_targets(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [target for target in targets if bool(target.get("today"))]


def dm_counts(targets: list[dict[str, Any]]) -> dict[str, int]:
    replied_count = len([target for target in targets if bool(target.get("replied"))])
    visible_count = len(targets)
    return {
        "dm_visible_thread_count": visible_count,
        "dm_replied_thread_count": replied_count,
        "dm_unreplied_thread_count": max(visible_count - replied_count, 0),
    }


def dm_target_has_self_reply(label: str) -> bool:
    normalized = " ".join(label.split())
    return bool(re.search(r"\byou\s*[:：]|\byou sent\b|\byou replied\b|\byou responded\b|你\s*[:：]|你已发送|你发送|您\s*[:：]", normalized, re.IGNORECASE))


def load_dm_thread_history(ws_url: str, max_scrolls: int, target_messages: int, window_hours: int) -> dict[str, Any]:
    scroll_limit = max(0, int(max_scrolls))
    target = max(1, int(target_messages))
    state = get_dm_history_state(ws_url)
    last_count = int(state.get("count") or 0)
    last_top_signature = str(state.get("top_signature") or "")
    stable_top_rounds = 0
    scrolls_used = 0
    reached_top = bool(state.get("at_top"))
    hit_message_cap = last_count >= target
    window_exceeded = dm_loaded_beyond_window(ws_url, window_hours) if int(window_hours) > 0 else False

    while scrolls_used < scroll_limit and not reached_top and not window_exceeded and not hit_message_cap:
        info = scroll_dm_messages_up(ws_url)
        scrolls_used += 1
        time.sleep(0.8)
        state = get_dm_history_state(ws_url)
        current_count = int(state.get("count") or 0)
        current_top_signature = str(state.get("top_signature") or "")
        window_exceeded = dm_loaded_beyond_window(ws_url, window_hours) if int(window_hours) > 0 else False
        reached_top = bool(info.get("at_top")) or bool(state.get("at_top"))
        hit_message_cap = current_count >= target
        if current_count <= last_count:
            if current_top_signature and current_top_signature == last_top_signature:
                stable_top_rounds += 1
            else:
                stable_top_rounds = 0
        else:
            stable_top_rounds = 0
        last_count = max(last_count, current_count)
        last_top_signature = current_top_signature or last_top_signature
        if reached_top and stable_top_rounds >= 1:
            break

    return {
        "scrolls_used": scrolls_used,
        "loaded_messages": last_count,
        "load_complete": reached_top and not hit_message_cap,
        "window_exceeded": window_exceeded,
        "hit_message_cap": hit_message_cap,
        "top_signature": last_top_signature,
        "target_messages": target,
        "window_hours": max(0, int(window_hours)),
    }


def get_dm_history_state(ws_url: str) -> dict[str, Any]:
    script = r"""
(() => {
  const panel = document.querySelector('[data-testid="dm-conversation-panel"]')
    || document.querySelector('[data-testid="dm-conversation-content"]')
    || document.querySelector('main')
    || document.body;
  const scroller = findScroller(panel);
  const roots = Array.from(panel.querySelectorAll('div[data-testid^="message-"]'))
    .filter((node) => !String(node.getAttribute('data-testid') || '').startsWith('message-text-'));
  const first = roots[0];
  return {
    count: roots.length,
    at_top: scroller ? scroller.scrollTop <= 2 : window.scrollY <= 0,
    scroll_top: scroller ? scroller.scrollTop : window.scrollY,
    top_signature: first ? signature(first) : '',
  };

  function findScroller(root) {
    const candidates = [root, ...Array.from(root.querySelectorAll('*'))].filter((el) => {
      const rect = el.getBoundingClientRect();
      return rect.width > 200 && rect.height > 200 && el.scrollHeight > el.clientHeight + 40;
    });
    return candidates.sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight))[0] || null;
  }
  function signature(node) {
    const text = (node.innerText || '').replace(/\s+/g, ' ').trim();
    const testid = node.getAttribute('data-testid') || '';
    const rect = node.getBoundingClientRect();
    return `${testid}:${Math.round(rect.top)}:${text.slice(0, 160)}`;
  }
})()
"""
    value = cdp_eval(ws_url, script)
    return value if isinstance(value, dict) else {}


def scroll_dm_messages_up(ws_url: str) -> dict[str, Any]:
    script = r"""
(() => {
  const panel = document.querySelector('[data-testid="dm-conversation-panel"]')
    || document.querySelector('[data-testid="dm-conversation-content"]')
    || document.querySelector('main')
    || document.body;
  const candidates = [panel, ...Array.from(panel.querySelectorAll('*'))].filter((el) => {
    const rect = el.getBoundingClientRect();
    return rect.width > 200 && rect.height > 200 && el.scrollHeight > el.clientHeight + 40;
  });
  const scroller = candidates.sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight))[0];
  if (!scroller) {
    window.scrollBy(0, -Math.max(900, window.innerHeight * 0.9));
    return {found: false, at_top: window.scrollY <= 0, scroll_top: window.scrollY};
  }
  const before = scroller.scrollTop;
  scroller.scrollTop = Math.max(0, before - Math.max(900, scroller.clientHeight * 0.9));
  scroller.dispatchEvent(new Event('scroll', {bubbles: true}));
  return {found: true, at_top: scroller.scrollTop <= 0, scroll_top: scroller.scrollTop, before};
})()
"""
    value = cdp_eval(ws_url, script)
    return value if isinstance(value, dict) else {}


def dm_loaded_beyond_window(ws_url: str, window_hours: int) -> bool:
    script = r"""
(() => {
  const windowHours = Math.max(1, %d);
  const oldest = oldestLoadedMessageAgeHours();
  return Number.isFinite(oldest) && oldest > windowHours;

  function oldestLoadedMessageAgeHours() {
    const panel = document.querySelector('[data-testid="dm-conversation-panel"]')
      || document.querySelector('[data-testid="dm-conversation-content"]')
      || document.querySelector('main')
      || document.body;
    const list = panel.querySelector('[data-testid="dm-message-list"]') || panel;
    const items = Array.from(list.querySelectorAll('li'));
    let currentDay = '';
    let oldest = -Infinity;
    for (const item of items) {
      const text = clean(item.innerText || '');
      if (!text) continue;
      if (!item.querySelector('div[data-testid^="message-"]')) {
        const day = dayLabel(text);
        if (day) currentDay = day;
        continue;
      }
      for (const root of Array.from(item.querySelectorAll('div[data-testid^="message-"]'))) {
        if (String(root.getAttribute('data-testid') || '').startsWith('message-text-')) continue;
        const timeText = firstTimeText(root);
        const when = parseMessageDate(currentDay, timeText);
        if (!when) continue;
        const age = (Date.now() - when.getTime()) / 36e5;
        if (age > oldest) oldest = age;
      }
    }
    return oldest;
  }
  function dayLabel(text) {
    const value = clean(text);
    if (/^(today|yesterday|今天|昨天)$/i.test(value)) return value;
    if (/^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}/i.test(value)) return value;
    if (/^\d{4}[\/-]\d{1,2}[\/-]\d{1,2}$/.test(value)) return value;
    if (/^\d{1,2}[\/-]\d{1,2}(?:[\/-]\d{2,4})?$/.test(value)) return value;
    return '';
  }
  function parseMessageDate(day, timeText) {
    const time = parseTime(timeText);
    if (!time) return null;
    const base = parseDay(day);
    if (!base) return null;
    base.setHours(time.hours, time.minutes, 0, 0);
    return base;
  }
  function parseDay(day) {
    const now = new Date();
    const value = clean(day).toLowerCase();
    if (!value || value === 'today' || value === '今天') return new Date(now.getFullYear(), now.getMonth(), now.getDate());
    if (value === 'yesterday' || value === '昨天') return new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
    const parsed = new Date(day);
    if (!Number.isNaN(parsed.getTime())) return new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate());
    return null;
  }
  function firstTimeText(node) {
    for (const child of Array.from(node.querySelectorAll('span, div'))) {
      const text = clean(child.innerText || '');
      if (isTimeText(text)) return text;
    }
    const match = clean(node.innerText || '').match(/(\d{1,2}:\d{2}\s?(?:AM|PM)?|上午\s*\d{1,2}:\d{2}|下午\s*\d{1,2}:\d{2})/i);
    return match ? match[1] : '';
  }
  function parseTime(text) {
    const value = clean(text);
    let match = value.match(/^(\d{1,2}):(\d{2})\s?(AM|PM)$/i);
    if (match) {
      let hours = Number(match[1]);
      const minutes = Number(match[2]);
      const suffix = match[3].toUpperCase();
      if (suffix === 'PM' && hours < 12) hours += 12;
      if (suffix === 'AM' && hours === 12) hours = 0;
      return {hours, minutes};
    }
    match = value.match(/^(上午|下午)\s*(\d{1,2}):(\d{2})$/);
    if (match) {
      let hours = Number(match[2]);
      const minutes = Number(match[3]);
      if (match[1] === '下午' && hours < 12) hours += 12;
      if (match[1] === '上午' && hours === 12) hours = 0;
      return {hours, minutes};
    }
    match = value.match(/^(\d{1,2}):(\d{2})$/);
    if (match) return {hours: Number(match[1]), minutes: Number(match[2])};
    return null;
  }
  function clean(text) { return (text || '').replace(/\s+/g, ' ').trim(); }
  function isTimeText(text) { return /^(\d{1,2}:\d{2}\s?(AM|PM)?|\d{1,2}:\d{2}|上午\s*\d{1,2}:\d{2}|下午\s*\d{1,2}:\d{2})$/i.test(text); }
})()
""" % max(1, int(window_hours))
    return bool(cdp_eval(ws_url, script))


def count_dm_messages(ws_url: str) -> int:
    script = r"""
(() => {
  const panel = document.querySelector('[data-testid="dm-conversation-panel"]')
    || document.querySelector('[data-testid="dm-conversation-content"]')
    || document.querySelector('main')
    || document.body;
  const roots = Array.from(panel.querySelectorAll('div[data-testid^="message-"]'))
    .filter((node) => !String(node.getAttribute('data-testid') || '').startsWith('message-text-'));
  return roots.filter((node) => {
    const bubble = node.querySelector('[data-testid^="message-text-"]');
    const text = bubbleText(bubble || node);
    const rect = node.getBoundingClientRect();
    return Boolean(text) && rect.width > 20 && rect.height > 12;
  }).length;

  function bubbleText(node) {
    if (!node) return '';
    const parts = [];
    for (const child of Array.from(node.querySelectorAll('span, div[dir="auto"]'))) {
      const text = clean(child.innerText || '');
      if (!text || isTimeText(text)) continue;
      const style = getComputedStyle(child);
      if (style.opacity === '0' || style.visibility === 'hidden' || style.display === 'none') continue;
      parts.push(text);
    }
    return Array.from(new Set(parts)).join(' ').trim();
  }
  function clean(text) { return (text || '').replace(/\s+/g, ' ').trim(); }
  function isTimeText(text) { return /^(\d{1,2}:\d{2}\s?(AM|PM)?|\d{1,2}:\d{2}|上午\s*\d{1,2}:\d{2}|下午\s*\d{1,2}:\d{2})$/i.test(text); }
})()
"""
    value = cdp_eval(ws_url, script)
    return int(value) if isinstance(value, (int, float)) else 0


def extract_dm_messages(ws_url: str, max_messages: int = 300) -> list[dict[str, Any]]:
    script = r"""
(() => {
  const panel = document.querySelector('[data-testid="dm-conversation-panel"]')
    || document.querySelector('[data-testid="dm-conversation-content"]')
    || document.querySelector('main')
    || document.body;
  const roots = Array.from(panel.querySelectorAll('div[data-testid^="message-"]'))
    .filter((node) => !String(node.getAttribute('data-testid') || '').startsWith('message-text-'));
  const out = [];
  const seen = new Set();
  for (const node of roots) {
    const bubble = node.querySelector('[data-testid^="message-text-"]');
    const text = bubbleText(bubble || node);
    if (!text) continue;
    const rect = node.getBoundingClientRect();
    if (rect.width < 20 || rect.height < 12) continue;
    const key = `${Math.round(rect.top)}:${text.slice(0, 120)}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const time = firstTimeText(bubble || node);
    const classText = String(node.className || '');
    const assets = messageAssets(node);
    out.push({
      sender: classText.includes('justify-end') ? 'me' : 'other',
      time,
      text,
      links: assets.links,
      media: assets.media,
    });
  }
  return out.slice(-Math.max(1, %d));

  function bubbleText(node) {
    if (!node) return '';
    const leafParts = [];
    for (const child of Array.from(node.querySelectorAll('span'))) {
      const text = clean(child.innerText || '');
      if (!text || isTimeText(text)) continue;
      const style = getComputedStyle(child);
      if (style.opacity === '0' || style.visibility === 'hidden' || style.display === 'none') continue;
      leafParts.push(text);
    }
    if (leafParts.length) return Array.from(new Set(leafParts)).join(' ').trim();
    const text = clean(node.innerText || '');
    return stripTrailingTimes(text);
  }
  function firstTimeText(node) {
    if (!node) return '';
    for (const child of Array.from(node.querySelectorAll('span, div'))) {
      const text = clean(child.innerText || '');
      if (isTimeText(text)) return text;
    }
    const match = clean(node.innerText || '').match(/(\d{1,2}:\d{2}\s?(?:AM|PM)?|上午\s*\d{1,2}:\d{2}|下午\s*\d{1,2}:\d{2})/i);
    return match ? match[1] : '';
  }
  function stripTrailingTimes(text) {
    let value = clean(text);
    for (let i = 0; i < 3; i += 1) {
      value = value.replace(/\s+(\d{1,2}:\d{2}\s?(?:AM|PM)?|上午\s*\d{1,2}:\d{2}|下午\s*\d{1,2}:\d{2})$/i, '').trim();
    }
    return value;
  }
  function clean(text) { return (text || '').replace(/\s+/g, ' ').trim(); }
  function isTimeText(text) { return /^(\d{1,2}:\d{2}\s?(AM|PM)?|\d{1,2}:\d{2}|上午\s*\d{1,2}:\d{2}|下午\s*\d{1,2}:\d{2})$/i.test(text); }
  function messageAssets(node) {
    const links = [];
    for (const a of Array.from(node.querySelectorAll('a[href]'))) {
      const href = normalizeUrl(a.getAttribute('href'));
      if (!href) continue;
      const label = clean(a.innerText || a.getAttribute('aria-label') || '');
      if (!links.some((item) => item.url === href)) links.push({url: href, label});
    }
    const media = [];
    for (const img of Array.from(node.querySelectorAll('img[src]'))) {
      const src = normalizeUrl(img.getAttribute('src'));
      if (!src) continue;
      const alt = clean(img.getAttribute('alt') || img.getAttribute('aria-label') || '');
      if (!media.some((item) => item.url === src)) media.push({type: 'image', url: src, alt});
    }
    for (const video of Array.from(node.querySelectorAll('video'))) {
      const src = normalizeUrl(video.currentSrc || video.getAttribute('src'));
      const poster = normalizeUrl(video.getAttribute('poster'));
      if (src || poster) media.push({type: 'video', url: src || '', poster: poster || '', alt: clean(video.getAttribute('aria-label') || '')});
    }
    return {links: links.slice(0, 10), media: media.slice(0, 8)};
  }
  function normalizeUrl(value) {
    if (!value || value.startsWith('data:') || value.startsWith('blob:')) return '';
    try {
      const url = new URL(value, location.href);
      url.hash = '';
      return url.href;
    } catch {
      return '';
    }
  }
})()
""" % max(1, int(max_messages))
    value = cdp_eval(ws_url, script)
    if not isinstance(value, list):
        return []
    messages: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        messages.append(
            {
                "sender": "me" if str(item.get("sender") or "") == "me" else "other",
                "time": str(item.get("time") or ""),
                "text": text[:1000],
                "links": normalize_assets(item.get("links"), kind="links"),
                "media": normalize_assets(item.get("media"), kind="media"),
            }
        )
    return messages


def normalize_assets(value: Any, kind: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        if not url:
            continue
        normalized: dict[str, str] = {"url": url[:1200]}
        if kind == "media":
            normalized["type"] = str(item.get("type") or "media")[:40]
            if item.get("poster"):
                normalized["poster"] = str(item.get("poster") or "")[:1200]
            if item.get("alt"):
                normalized["alt"] = str(item.get("alt") or "")[:500]
        else:
            if item.get("label"):
                normalized["label"] = str(item.get("label") or "")[:500]
        out.append(normalized)
    return out[:10]


def render_dm_messages(messages: list[dict[str, Any]]) -> str:
    lines = []
    for message in messages:
        sender = "me" if message.get("sender") == "me" else "other"
        timestamp = f" {message.get('time')}" if message.get("time") else ""
        suffixes = []
        if message.get("links"):
            suffixes.append("links=" + ", ".join(asset.get("url", "") for asset in message.get("links", [])[:3]))
        if message.get("media"):
            suffixes.append("media=" + ", ".join(asset.get("url", "") for asset in message.get("media", [])[:3]))
        suffix = f" [{' ; '.join(suffixes)}]" if suffixes else ""
        lines.append(f"{sender}{timestamp}: {message.get('text') or ''}{suffix}")
    return "\n".join(lines)


def extract_dm_conversation_text(ws_url: str) -> str:
    script = r"""
(() => {
  const panel = document.querySelector('[data-testid="dm-conversation-panel"]') || document.querySelector('[data-testid="conversationPanel"]') || document.querySelector('main') || document.body;
  return (panel.innerText || '').trim().slice(0, 12000);
})()
"""
    value = cdp_eval(ws_url, script)
    return str(value or "")


def wait_for_dm_ready(ws_url: str, timeout_sec: int = 20) -> str:
    deadline = time.time() + timeout_sec
    last_text = ""
    while time.time() < deadline:
        text = extract_main_text(ws_url)
        last_text = text or last_text
        if is_dm_passcode_screen(text):
            return text
        if extract_dm_thread_targets(ws_url):
            return text
        normalized = " ".join(text.lower().split())
        empty_markers = ["no messages", "welcome to your inbox"]
        if any(marker in normalized for marker in empty_markers):
            return text
        time.sleep(1)
    return last_text


def looks_like_dm_list_text(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 4:
        return False
    joined = " ".join(lines).lower()
    if not any(marker in joined for marker in ("chat", "messages", "search", "inbox")):
        return False
    conversation_markers = ("@", "you sent", "you:", "sent you", "min", "m", "h", "d")
    return any(marker in joined for marker in conversation_markers)


def is_dm_passcode_screen(text: str) -> bool:
    normalized = " ".join(text.lower().split())
    if "passcode" not in normalized:
        return False
    passcode_phrases = [
        "create passcode",
        "set passcode",
        "enter passcode",
        "your passcode is required",
        "recover your encryption keys",
        "encryption keys",
    ]
    return any(phrase in normalized for phrase in passcode_phrases)


def wait_for_dm_passcode_resolution(port: int, timeout_sec: int) -> bool:
    ws_url = wait_for_cdp_page_ws(port)
    cdp_call(ws_url, "Page.enable")
    cdp_call(ws_url, "Runtime.enable")
    cdp_call(ws_url, "Page.navigate", {"url": "https://x.com/messages"})
    print("Complete the X Chat passcode/recovery step in the visible browser window.")
    deadline = time.time() + timeout_sec
    last_notice = 0.0
    while time.time() < deadline:
        time.sleep(3)
        main_text = extract_main_text(ws_url)
        if is_dm_passcode_screen(main_text):
            if time.time() - last_notice > 15:
                print("Still waiting for X Chat passcode/recovery to be completed in the browser window.")
                last_notice = time.time()
            continue
        if dm_messages_page_is_readable(ws_url, main_text):
            print("X Chat messages are readable. Resuming DM collection...")
            return True
        if time.time() - last_notice > 15:
            print("Waiting for X Messages to become readable after the visible challenge is completed.")
            last_notice = time.time()
    return False


def dm_messages_page_is_readable(ws_url: str, text: str) -> bool:
    if is_dm_passcode_screen(text):
        return False
    if extract_dm_thread_targets(ws_url):
        return True
    normalized = " ".join(text.lower().split())
    empty_markers = ["no messages", "welcome to your inbox"]
    return any(marker in normalized for marker in empty_markers)


def extract_dm_thread_targets(ws_url: str) -> list[dict[str, Any]]:
    script = r"""
(() => {
  const seen = new Set();
  const ignoredText = /^(messages|new message|message requests|search direct messages|search|settings|home|profile|notifications)$/i;
  const ignoredShortText = /^(all|chat)$/i;
  const visible = (el) => {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return rect.width > 40 && rect.height > 24 && style.visibility !== 'hidden' && style.display !== 'none';
  };
  const clean = (text) => (text || '').replace(/\s+/g, ' ').trim();
  const out = [];

  const replyMeta = (el, label) => {
    const text = clean(label).toLowerCase();
    const aria = clean(el.getAttribute('aria-label') || '').toLowerCase();
    const combined = `${text} ${aria}`;
    const reasons = [];
    if (/\byou\s*[:：]|\byou sent\b|\byou replied\b|\byou responded\b|你\s*[:：]|你已发送|你发送|您\s*[:：]/i.test(combined)) {
      reasons.push('self_reply_label');
    }
    return { replied: reasons.length > 0, reply_reason: reasons.join(',') };
  };
  const timeMeta = (el) => {
    const parts = [];
    for (const node of Array.from(el.querySelectorAll('time'))) {
      parts.push(clean(node.getAttribute('datetime') || ''));
      parts.push(clean(node.getAttribute('title') || ''));
      parts.push(clean(node.getAttribute('aria-label') || ''));
      parts.push(clean(node.innerText || ''));
    }
    parts.push(clean(el.getAttribute('title') || ''));
    parts.push(clean(el.getAttribute('aria-label') || ''));
    return parts.filter(Boolean).join(' ');
  };

  for (const a of document.querySelectorAll('a[href^="/messages/"], a[href^="/i/chat/"], a[href*="x.com/messages/"], a[href*="x.com/i/chat/"]')) {
    if (!visible(a)) continue;
    const url = new URL(a.getAttribute('href'), location.href);
    url.search = '';
    url.hash = '';
    const label = clean(a.innerText || a.getAttribute('aria-label') || '');
    if (!/^https:\/\/(x|twitter)\.com\/(messages\/[^/]+|i\/chat\/[^/]+)/.test(url.href)) continue;
    if (/\/messages\/compose$/.test(url.pathname)) continue;
    if (!label || ignoredText.test(label) || ignoredShortText.test(label)) continue;
    const key = url.href;
    if (seen.has(key)) continue;
    seen.add(key);
    const meta = replyMeta(a, label);
    const rect = a.getBoundingClientRect();
    out.push({
      target_type: 'link',
      url: url.href,
      label,
      time_hint: timeMeta(a),
      x: rect.left + Math.min(rect.width / 2, 280),
      y: rect.top + rect.height / 2,
      ...meta
    });
  }

  const hasThreadMarker = (label) => (
    /\byou\s*[:：]|\byou sent\b|\byou replied\b|\byou responded\b|你\s*[:：]|你已发送|你发送|您\s*[:：]/i.test(label)
    || /\b(now|just now|\d+\s*(m|min|mins|minute|minutes|h|hr|hrs|hour|hours))\b/i.test(label)
    || /(刚刚|\d+\s*(秒|分钟|小时)|今天|今日|上午|下午|晚上|中午)/.test(label)
  );

  const candidates = Array.from(document.querySelectorAll([
    '[role="button"]',
    '[role="link"]',
    '[data-testid*="conversation" i]',
    '[data-testid*="cell" i]',
    '[data-testid="cellInnerDiv"]',
    'a[href*="/messages/"]',
    'div[aria-label]',
    'section div',
    'aside div'
  ].join(',')));
  for (const node of candidates) {
    if (!visible(node)) continue;
    let label = clean(node.innerText || node.getAttribute('aria-label') || '');
    if (!label || label.length < 2 || ignoredText.test(label) || ignoredShortText.test(label)) continue;
    if (label.length > 600) continue;
    if (!/[A-Za-z0-9_\u4e00-\u9fff]/.test(label)) continue;
    let rect = node.getBoundingClientRect();
    const link = node.querySelector && node.querySelector('a[href*="/messages/"], a[href*="/i/chat/"]');
    if (link) {
      const linkLabel = clean(link.innerText || link.getAttribute('aria-label') || '');
      const linkRect = link.getBoundingClientRect();
      if (linkLabel && hasThreadMarker(linkLabel) && linkRect.width > 40 && linkRect.height > 24) {
        label = linkLabel;
        rect = linkRect;
      }
    }
    if (!link && rect.left < 150) continue;
    if (!link && rect.height > 220) continue;
    const isLikelyListRow = rect.left < Math.min(760, window.innerWidth * 0.45) && rect.width > 160 && rect.height >= 36 && rect.height < 180;
    if (!link && !hasThreadMarker(label)) continue;
    if (!node.matches('[role="button"], [role="link"], [data-testid*="conversation" i], [data-testid*="cell" i], [data-testid="cellInnerDiv"], a[href*="/messages/"], div[aria-label]') && (!isLikelyListRow || !hasThreadMarker(label))) continue;
    let url = '';
    if (link) {
      const parsed = new URL(link.getAttribute('href'), location.href);
      parsed.search = '';
      parsed.hash = '';
      url = parsed.href;
    }
    const key = url || `${Math.round(rect.left)}:${Math.round(rect.top)}:${label.slice(0, 80)}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const meta = replyMeta(node, label);
    out.push({
      target_type: url ? 'row_link' : 'row_click',
      url,
      label,
      time_hint: timeMeta(node),
      x: rect.left + Math.min(rect.width / 2, 280),
      y: rect.top + rect.height / 2,
      ...meta
    });
  }
  return out.slice(0, 20);
})()
"""
    value = cdp_eval(ws_url, script)
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            out.append(
                {
                    "target_type": str(item.get("target_type") or ""),
                    "url": str(item.get("url") or ""),
                    "label": str(item.get("label") or ""),
                    "time_hint": str(item.get("time_hint") or ""),
                    "replied": bool(item.get("replied")) or dm_target_has_self_reply(str(item.get("label") or "")),
                    "reply_reason": str(item.get("reply_reason") or ""),
                    "today": dm_target_is_today(str(item.get("label") or ""), str(item.get("time_hint") or "")),
                    "x": float(item.get("x") or 0),
                    "y": float(item.get("y") or 0),
                }
            )
    return dedupe_dm_targets(out)


def dm_target_is_today(label: str, time_hint: str = "") -> bool:
    combined = " ".join(part for part in (time_hint, label) if part)
    if dm_time_hint_is_today(time_hint):
        return True
    normalized = " ".join(combined.lower().split())
    if not normalized:
        return False
    if re.search(r"\b(now|just now|sec|secs|second|seconds|min|mins|minute|minutes|h|hr|hrs|hour|hours)\b", normalized):
        return True
    if re.search(r"\b\d+\s*(m|min|mins|minute|minutes|h|hr|hrs|hour|hours)\b", normalized):
        return True
    if re.search(r"(刚刚|秒|分钟|小时|今天|今日|上午|下午|晚上|中午)", normalized):
        return True
    if re.search(r"\b(yesterday|d|day|days|w|week|weeks|mo|month|months|y|year|years)\b|昨天|周|週|月|年", normalized):
        return False
    return False


def dm_time_hint_is_today(value: str) -> bool:
    if not value:
        return False
    today = dt.datetime.now().astimezone().date()
    for match in re.findall(r"\d{4}-\d{2}-\d{2}(?:[T ][0-9:.+-Z]*)?", value):
        try:
            parsed = dt.datetime.fromisoformat(match.replace("Z", "+00:00"))
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.datetime.now().astimezone().tzinfo)
        if parsed.astimezone().date() == today:
            return True
    return False


def dedupe_dm_targets(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for target in targets:
        key = str(target.get("url") or dm_participant(target) or target.get("label") or "").lower()
        if not key:
            key = f"{round(float(target.get('x') or 0))}:{round(float(target.get('y') or 0))}"
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = target
            continue
        existing["replied"] = bool(existing.get("replied")) or bool(target.get("replied"))
        existing["today"] = bool(existing.get("today")) or bool(target.get("today"))
        reasons = {part for part in str(existing.get("reply_reason") or "").split(",") if part}
        reasons.update(part for part in str(target.get("reply_reason") or "").split(",") if part)
        existing["reply_reason"] = ",".join(sorted(reasons))
        if not existing.get("time_hint") and target.get("time_hint"):
            existing["time_hint"] = target["time_hint"]
        if not existing.get("url") and target.get("url"):
            existing["url"] = target["url"]
            existing["target_type"] = target.get("target_type") or existing.get("target_type")
        if len(str(target.get("label") or "")) > len(str(existing.get("label") or "")):
            existing["label"] = target["label"]
    return list(deduped.values())


def click_point(ws_url: str, x: float, y: float) -> None:
    for event_type in ("mouseMoved", "mousePressed", "mouseReleased"):
        params: dict[str, Any] = {"type": event_type, "x": x, "y": y, "button": "left", "clickCount": 1}
        if event_type == "mousePressed":
            params["buttons"] = 1
        cdp_call(ws_url, "Input.dispatchMouseEvent", params)


def extract_main_text(ws_url: str) -> str:
    script = r"""
(() => {
  const main = document.querySelector('main') || document.body;
  return (main.innerText || '').trim().slice(0, 12000);
})()
"""
    value = cdp_eval(ws_url, script)
    return str(value or "")


def wait_for_cdp(port: int) -> None:
    url = f"http://127.0.0.1:{port}/json/version"
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                json.loads(response.read().decode("utf-8"))
                return
        except Exception:
            time.sleep(0.2)
    raise SystemExit("Timed out waiting for browser DevTools endpoint.")


def wait_for_cdp_page_ws(port: int) -> str:
    url = f"http://127.0.0.1:{port}/json/list"
    deadline = time.time() + 30
    fallback: str | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                targets = json.loads(response.read().decode("utf-8"))
        except Exception:
            time.sleep(0.2)
            continue
        if isinstance(targets, list):
            for target in targets:
                if not isinstance(target, dict):
                    continue
                ws_url = target.get("webSocketDebuggerUrl")
                target_type = target.get("type")
                if isinstance(ws_url, str) and target_type == "page":
                    fallback = fallback or ws_url
                    target_url = str(target.get("url") or "")
                    if "x.com" in target_url or "twitter.com" in target_url:
                        return ws_url
            if fallback:
                return fallback
        time.sleep(0.2)
    raise SystemExit("Timed out waiting for browser page DevTools endpoint.")


def cdp_get_all_cookies(ws_url: str) -> list[dict[str, object]]:
    result = cdp_call(ws_url, "Network.getAllCookies")
    if isinstance(result, dict) and isinstance(result.get("cookies"), list):
        return [c for c in result["cookies"] if isinstance(c, dict)]
    result = cdp_call(ws_url, "Storage.getCookies")
    if isinstance(result, dict) and isinstance(result.get("cookies"), list):
        return [c for c in result["cookies"] if isinstance(c, dict)]
    return []


def cdp_eval(ws_url: str, expression: str) -> Any:
    result = cdp_call(ws_url, "Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True})
    if not isinstance(result, dict) or cdp_error(result):
        return None
    remote = result.get("result", {})
    if isinstance(remote, dict):
        return remote.get("value")
    return None


def cdp_error(result: Any) -> bool:
    return isinstance(result, dict) and isinstance(result.get("_cdp_error"), str)


def cdp_call(ws_url: str, method: str, params: dict[str, Any] | None = None, retries: int = 2) -> Any:
    last_error = ""
    for _ in range(max(retries, 1)):
        sock: socket.socket | None = None
        try:
            sock = websocket_connect(ws_url)
            websocket_send_json(sock, {"id": 1, "method": method, "params": params or {}})
            deadline = time.time() + 20
            while time.time() < deadline:
                message = websocket_recv_json(sock)
                if message.get("id") == 1:
                    if "error" in message:
                        return {"_cdp_error": json.dumps(message.get("error"), ensure_ascii=False)}
                    return message.get("result", {})
            last_error = f"Timed out waiting for CDP response to {method}"
        except Exception as exc:
            last_error = str(exc)
            time.sleep(0.4)
        finally:
            if sock is not None:
                sock.close()
    return {"_cdp_error": last_error or f"CDP call failed: {method}"}


def websocket_connect(ws_url: str) -> socket.socket:
    if not ws_url.startswith("ws://"):
        raise RuntimeError("Only local ws:// DevTools endpoints are supported.")
    without_scheme = ws_url[len("ws://") :]
    host_port, path = without_scheme.split("/", 1)
    path = "/" + path
    host, port_s = host_port.rsplit(":", 1)
    raw_sock = socket.create_connection((host, int(port_s)), timeout=5)
    key = base64.b64encode(os.urandom(16)).decode("ascii")
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host_port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n"
    )
    raw_sock.sendall(request.encode("ascii"))
    response = raw_sock.recv(4096)
    if b" 101 " not in response.split(b"\r\n", 1)[0]:
        raw_sock.close()
        raise RuntimeError("Could not open DevTools WebSocket.")
    return raw_sock


def websocket_send_json(sock: socket.socket, payload: dict[str, object]) -> None:
    data = json.dumps(payload).encode("utf-8")
    header = bytearray([0x81])
    if len(data) < 126:
        header.append(0x80 | len(data))
    elif len(data) < 65536:
        header.append(0x80 | 126)
        header.extend(struct.pack("!H", len(data)))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack("!Q", len(data)))
    mask = os.urandom(4)
    masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(data))
    sock.sendall(bytes(header) + mask + masked)


def websocket_recv_json(sock: socket.socket) -> dict[str, object]:
    first_two = recv_exact(sock, 2)
    opcode = first_two[0] & 0x0F
    if opcode == 0x8:
        raise ConnectionError("DevTools WebSocket closed.")
    length = first_two[1] & 0x7F
    if length == 126:
        length = struct.unpack("!H", recv_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", recv_exact(sock, 8))[0]
    masked = bool(first_two[1] & 0x80)
    mask = recv_exact(sock, 4) if masked else b""
    data = recv_exact(sock, length)
    if masked:
        data = bytes(byte ^ mask[index % 4] for index, byte in enumerate(data))
    if opcode != 0x1:
        return {}
    return json.loads(data.decode("utf-8"))


def recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        chunk = sock.recv(size - len(chunks))
        if not chunk:
            raise ConnectionError("Unexpected end of DevTools WebSocket stream.")
        chunks.extend(chunk)
    return bytes(chunks)


def ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except PermissionError:
        pass
