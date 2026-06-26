#!/usr/bin/env python3
"""Collect X/Twitter digest input through a persistent local browser session."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import socket
import struct
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    default_state_dir = Path(__file__).resolve().parents[1] / ".state"
    parser.add_argument("--handle", help="Your X handle, with or without @. If omitted, the script tries to detect it from the logged-in page.")
    parser.add_argument("--keywords", default="", help="Comma-separated keywords or queries for hotspot search.")
    parser.add_argument("--out", default=str(default_state_dir / "run"), help="Output directory.")
    parser.add_argument("--profile-dir", default=str(default_state_dir / "chrome-profile"))
    parser.add_argument("--scrolls", type=int, default=4, help="Scroll rounds per page.")
    parser.add_argument("--login-timeout-sec", type=int, default=300)
    parser.add_argument("--include-dms", action="store_true", help="Also visit X messages and capture visible conversation text.")
    parser.add_argument("--dm-threads", type=int, default=5, help="Maximum recent DM threads to open when --include-dms is set.")
    parser.add_argument("--headless", action="store_true", help="Run without a visible browser window. This is the default after first login.")
    parser.add_argument("--headed", action="store_true", help="Force a visible browser window for debugging or manual login.")
    parser.add_argument("--non-interactive", action="store_true", help="Do not open a visible browser for DM passcode recovery; record a data gap instead.")
    parser.add_argument("--keep-browser-open", action="store_true")
    return parser.parse_args()


def find_chrome() -> str:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
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
    wait_for_cdp(port)
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


def build_pages(handle: str | None, keywords: str, include_dms: bool) -> list[dict[str, str]]:
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


def collect_page(port: int, page: dict[str, str], scrolls: int, dm_threads: int = 5) -> dict[str, Any]:
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
    posts: list[dict[str, Any]] = []
    for _ in range(max(scrolls, 1)):
        posts.extend(extract_articles(ws_url))
        cdp_eval(ws_url, "window.scrollBy(0, Math.max(900, window.innerHeight * 0.9));")
        time.sleep(2)
    posts.extend(extract_articles(ws_url))
    extra: dict[str, Any] = {}
    if page["kind"] == "messages":
        extra["visible_text"] = extract_main_text(ws_url)
        extra.update(collect_dm_threads(ws_url, max_threads=dm_threads))
    return {"kind": page["kind"], "url": page["url"], "items": dedupe_items(posts), **extra}


def collect_dm_threads(ws_url: str, max_threads: int) -> dict[str, Any]:
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
                    "but all appeared to have a self reply."
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
        if target.get("url"):
            cdp_call(ws_url, "Page.navigate", {"url": str(target["url"])})
        else:
            click_point(ws_url, float(target.get("x") or 0), float(target.get("y") or 0))
        time.sleep(4)
        for _ in range(2):
            cdp_eval(ws_url, "window.scrollBy(0, -Math.max(700, window.innerHeight * 0.8));")
            time.sleep(1)
        thread_text = extract_main_text(ws_url)
        message_count = count_dm_messages(ws_url)
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
                "text": thread_text,
            }
        )
        cdp_call(ws_url, "Page.navigate", {"url": "https://x.com/messages"})
        wait_for_dm_ready(ws_url, timeout_sec=8)

    return {
        "dm_status": "captured_unreplied_threads" if threads else "no_unreplied_threads",
        "dm_note": (
            f"Today visible DM threads: {counts['dm_visible_thread_count']}; replied: {counts['dm_replied_thread_count']}; "
            f"unreplied: {counts['dm_unreplied_thread_count']}. Opened up to {max_threads} unreplied thread(s); "
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


def count_dm_messages(ws_url: str) -> int:
    script = r"""
(() => {
  const main = document.querySelector('main') || document.body;
  const nodes = Array.from(main.querySelectorAll('[data-testid="messageEntry"], [data-testid*="message" i], [role="group"]'));
  const seen = new Set();
  let count = 0;
  for (const node of nodes) {
    const text = (node.innerText || '').replace(/\s+/g, ' ').trim();
    if (!text || text.length < 1) continue;
    if (/^(chat|search|message|messages|today|this conversation is now end-to-end encrypted)$/i.test(text)) continue;
    const rect = node.getBoundingClientRect();
    if (rect.width < 20 || rect.height < 12) continue;
    const key = `${Math.round(rect.left)}:${Math.round(rect.top)}:${text.slice(0, 80)}`;
    if (seen.has(key)) continue;
    seen.add(key);
    count += 1;
  }
  if (count > 0) return count;
  return Array.from(main.querySelectorAll('div[dir="auto"]')).filter((node) => {
    const text = (node.innerText || '').replace(/\s+/g, ' ').trim();
    const rect = node.getBoundingClientRect();
    if (!text || rect.width < 20 || rect.height < 12) return false;
    return !/^(chat|search|message|messages|today|this conversation is now end-to-end encrypted)$/i.test(text);
  }).length;
})()
"""
    value = cdp_eval(ws_url, script)
    return int(value) if isinstance(value, (int, float)) else 0


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
        empty_markers = ["no messages", "welcome to your inbox", "send a message to start a conversation"]
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
    print("X Chat passcode is required. Complete it in the opened browser window; collection will resume automatically.")
    deadline = time.time() + timeout_sec
    last_notice = 0.0
    while time.time() < deadline:
        time.sleep(3)
        main_text = extract_main_text(ws_url)
        if not is_dm_passcode_screen(main_text):
            print("X Chat passcode screen cleared. Resuming DM collection...")
            return True
        if time.time() - last_notice > 15:
            print("Still waiting for X Chat passcode to be completed in the opened browser window.")
            last_notice = time.time()
    return False


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

  for (const a of document.querySelectorAll('a[href^="/messages/"], a[href*="x.com/messages/"]')) {
    if (!visible(a)) continue;
    const url = new URL(a.getAttribute('href'), location.href);
    url.search = '';
    url.hash = '';
    const label = clean(a.innerText || a.getAttribute('aria-label') || '');
    if (!/^https:\/\/(x|twitter)\.com\/messages\/[^/]+/.test(url.href)) continue;
    if (/\/messages\/compose$/.test(url.pathname)) continue;
    if (!label || ignoredText.test(label) || ignoredShortText.test(label)) continue;
    const key = url.href;
    if (seen.has(key)) continue;
    seen.add(key);
    const meta = replyMeta(a, label);
    out.push({ target_type: 'link', url: url.href, label, ...meta });
  }

  const candidates = Array.from(document.querySelectorAll('[role="button"], [data-testid*="conversation" i], [data-testid*="cell" i]'));
  for (const node of candidates) {
    if (!visible(node)) continue;
    const label = clean(node.innerText || node.getAttribute('aria-label') || '');
    if (!label || label.length < 2 || ignoredText.test(label) || ignoredShortText.test(label)) continue;
    if (!/[A-Za-z0-9_\u4e00-\u9fff]/.test(label)) continue;
    const link = node.querySelector && node.querySelector('a[href*="/messages/"]');
    let url = '';
    if (link) {
      const parsed = new URL(link.getAttribute('href'), location.href);
      parsed.search = '';
      parsed.hash = '';
      url = parsed.href;
    }
    const rect = node.getBoundingClientRect();
    const key = url || `${Math.round(rect.left)}:${Math.round(rect.top)}:${label.slice(0, 80)}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const meta = replyMeta(node, label);
    out.push({
      target_type: url ? 'row_link' : 'row_click',
      url,
      label,
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
                    "replied": bool(item.get("replied")) or dm_target_has_self_reply(str(item.get("label") or "")),
                    "reply_reason": str(item.get("reply_reason") or ""),
                    "today": dm_target_is_today(str(item.get("label") or "")),
                    "x": float(item.get("x") or 0),
                    "y": float(item.get("y") or 0),
                }
            )
    return dedupe_dm_targets(out)


def dm_target_is_today(label: str) -> bool:
    normalized = " ".join(label.lower().split())
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


def extract_articles(ws_url: str) -> list[dict[str, Any]]:
    script = r"""
(() => {
  const statusUrl = (href) => {
    try {
      const url = new URL(href, location.href);
      return /\/status\/\d+/.test(url.pathname) ? url.href : null;
    } catch { return null; }
  };
  return Array.from(document.querySelectorAll('article')).map((article) => {
    const text = (article.innerText || '').trim();
    const links = Array.from(article.querySelectorAll('a[href]')).map(a => a.href).filter(Boolean);
    const status = links.map(statusUrl).find(Boolean) || null;
    const times = Array.from(article.querySelectorAll('time')).map(t => t.getAttribute('datetime')).filter(Boolean);
    const authorLinks = links.filter(h => {
      try {
        const p = new URL(h).pathname;
        return /^\/[^/]+$/.test(p) && !p.includes('/i/');
      } catch { return false; }
    });
    return { text, url: status, links, time: times[0] || null, authorUrl: authorLinks[0] || null };
  }).filter(item => item.text);
})()
"""
    value = cdp_eval(ws_url, script)
    return value if isinstance(value, list) else []


def extract_main_text(ws_url: str) -> str:
    script = r"""
(() => {
  const main = document.querySelector('main') || document.body;
  return (main.innerText || '').trim().slice(0, 12000);
})()
"""
    value = cdp_eval(ws_url, script)
    return str(value or "")


def detect_handle(port: int) -> str | None:
    try:
        ws_url = wait_for_cdp_page_ws(port)
        cdp_call(ws_url, "Page.enable")
        cdp_call(ws_url, "Runtime.enable")
        cdp_call(ws_url, "Page.navigate", {"url": "https://x.com/home"})
        time.sleep(5)
        script = r"""
(() => {
  const account = document.querySelector('[data-testid="SideNav_AccountSwitcher_Button"]');
  const accountText = account ? account.innerText : '';
  const accountMatch = accountText.match(/@([A-Za-z0-9_]{1,15})/);
  if (accountMatch) return accountMatch[1];
  const profileLink = document.querySelector('[data-testid="AppTabBar_Profile_Link"]');
  const profileHref = profileLink ? profileLink.getAttribute('href') : '';
  const profileMatch = profileHref.match(/^\/([A-Za-z0-9_]{1,15})$/);
  if (profileMatch) return profileMatch[1];
  const labels = Array.from(document.querySelectorAll('[aria-label]')).map(el => el.getAttribute('aria-label') || '');
  for (const label of labels) {
    const match = label.match(/@([A-Za-z0-9_]{1,15})/);
    if (match && /account|profile|账号|帳號|账户/i.test(label)) return match[1];
  }
  return null;
})()
"""
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


def render_markdown(data: dict[str, Any]) -> str:
    lines = [
        "# X 浏览器采集输入",
        "",
        f"- 生成时间: `{data['generated_at']}`",
        f"- 浏览器 profile: `{data['profile_dir']}`",
        f"- 当前账号: `{data.get('handle') or ''}`",
        "",
    ]
    for page in data["pages"]:
        lines.extend([f"## {page['kind']}", "", f"Source: {page['url']}", ""])
        lines.append(f"采集条数: `{len(page.get('items', []))}`")
        lines.append("")
        for item in page["items"][:80]:
            text = " ".join(str(item.get("text") or "").split())
            url = item.get("url") or ""
            timestamp = item.get("time") or ""
            lines.append(f"- `{timestamp}` {url}")
            lines.append(f"  {text[:1000]}")
        if page.get("visible_text"):
            lines.extend(["", "页面可见文本摘录:", "", str(page["visible_text"])[:3000]])
        if page.get("dm_status"):
            lines.extend(["", f"DM 状态: `{page['dm_status']}`"])
            lines.append(
                "DM 会话统计: "
                f"今日可见 `{int(page.get('dm_visible_thread_count') or 0)}` / "
                f"已回复 `{int(page.get('dm_replied_thread_count') or 0)}` / "
                f"未回复 `{int(page.get('dm_unreplied_thread_count') or 0)}`"
            )
            lines.append(f"DM 消息统计: 已打开未回复会话中捕获消息气泡 `{int(page.get('dm_captured_message_count') or 0)}`")
            if page.get("dm_note"):
                lines.append(str(page["dm_note"]))
        if page.get("collection_error"):
            lines.extend(["", f"采集错误: `{page['collection_error']}`"])
        for thread in page.get("dm_threads", [])[:20]:
            participant = thread.get("participant") or thread.get("label") or thread.get("url")
            lines.extend(["", f"### DM thread: {participant}", ""])
            if participant:
                lines.append(f"会话对象: `{participant}`")
                lines.append(f"回复状态: `{'已回复' if thread.get('replied') else '未回复'}`")
                lines.append(f"消息数量: `{int(thread.get('message_count') or 0)}`")
                lines.append("发信人判断: 使用会话对象/消息气泡判断；引用帖、转发卡片或链接预览里的作者不是 DM 发信人。")
                lines.append("")
            lines.append(str(thread.get("text") or "")[:3000])
        lines.append("")
    lines.extend(
        [
            "## 数据缺口",
            "",
            "- 浏览器采集依赖 X 页面结构和已加载的可见内容。",
            "- 日报默认使用较小滚动次数；需要更全覆盖时再提高 `--scrolls`。",
            "- DM 属于私密内容。只有用户明确同意本地读取时才使用 `--include-dms`。",
        ]
    )
    return "\n".join(lines) + "\n"


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


def write_digest_output(out_dir: Path, data: dict[str, Any]) -> None:
    ensure_private_dir(out_dir)
    (out_dir / "digest-input.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "digest-input.md").write_text(render_markdown(data), encoding="utf-8")


def main() -> None:
    args = parse_args()
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
        pages = build_pages(handle, args.keywords, args.include_dms)
        data = {
            "generated_at": dt.datetime.now().astimezone().isoformat(),
            "profile_dir": str(profile_dir),
            "handle": handle,
            "keywords": [k.strip() for k in args.keywords.split(",") if k.strip()],
            "pages": [],
        }
        for page in pages:
            print(f"Collecting {page['kind']}: {page['url']}")
            result = collect_page(port, page, args.scrolls, args.dm_threads)
            if page["kind"] == "messages" and result.get("dm_status") == "blocked_by_x_chat_passcode":
                if args.non_interactive:
                    result["dm_note"] = "X Chat passcode is required. Non-interactive mode skipped DM recovery for this run."
                    data["pages"].append(result)
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
                        print("X Chat passcode was completed. Returning to headless collection...")
                        stop_browser(proc)
                        proc, port = launch_browser(profile_dir, "https://x.com/messages", headless=True)
                        headless = True
                        wait_for_login(port, args.login_timeout_sec, interactive=False)
                    result = collect_page(port, page, args.scrolls, args.dm_threads)
                else:
                    result["dm_note"] = (
                        "Timed out waiting for the X Chat passcode screen to clear. "
                        "Open the visible browser window, complete passcode setup or entry, then rerun the digest."
                    )
            data["pages"].append(result)
        write_digest_output(out_dir, data)
        print(json.dumps({"out_dir": str(out_dir), "pages": len(data["pages"]), "headless": headless}, indent=2))
    finally:
        if not args.keep_browser_open:
            stop_browser(proc)


if __name__ == "__main__":
    main()
