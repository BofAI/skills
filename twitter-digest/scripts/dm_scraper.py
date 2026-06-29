"""X Direct Message scraping helpers.

Module map:
- Page-level collection: read the X Messages page and decide the DM status.
- Conversation-list scanning: scan today's visible threads and classify reply state.
- Conversation loading: open waiting-reply threads and load enough history.
- Readiness detection: distinguish empty inbox, loading skeleton, and passcode screens.
- Target parsing: normalize DOM-extracted thread rows into Python dictionaries.
"""

from __future__ import annotations

import datetime as dt
import re
import time
from typing import Any

from cdp_client import cdp_call, cdp_eval, wait_for_cdp_page_ws
from dom_script_loader import load_dom_script
from public_scraper import extract_main_text


DM_EMPTY_MARKERS = ("no messages", "welcome to your inbox")
DM_CONVERSATION_MARKERS = ("you:", "you sent", "now", " min", "m ", "h ", "today", "今天")
DM_SELF_REPLY_RE = re.compile(
    r"\byou\s*[:：]|\byou sent\b|\byou replied\b|\byou responded\b|你\s*[:：]|你已发送|你发送|您\s*[:：]",
    re.IGNORECASE,
)
DM_TODAY_WORD_RE = re.compile(r"\b(now|just now|sec|secs|second|seconds|min|mins|minute|minutes|h|hr|hrs|hour|hours)\b", re.IGNORECASE)
DM_TODAY_AGE_RE = re.compile(r"\b\d+\s*(m|min|mins|minute|minutes|h|hr|hrs|hour|hours)\b", re.IGNORECASE)
DM_TODAY_CN_RE = re.compile(r"(刚刚|秒|分钟|小时|今天|今日|上午|下午|晚上|中午)")
DM_OLD_TIME_RE = re.compile(r"\b(yesterday|d|day|days|w|week|weeks|mo|month|months|y|year|years)\b|昨天|周|週|月|年", re.IGNORECASE)
DM_PASSCODE_PHRASES = (
    "create passcode",
    "set passcode",
    "enter passcode",
    "your passcode is required",
    "recover your encryption keys",
    "encryption keys",
)
DM_LIST_STABLE_STOP_ROUNDS = 4
DM_LIST_OLDER_AFTER_TODAY_STABLE_ROUNDS = 2
DM_LIST_BOTTOM_CONFIRM_ROUNDS = 1
DM_LIST_SCROLL_SETTLE_SEC = 1.0
DM_ROW_RELOCATE_MAX_SCROLLS = 8
DM_ROW_RELOCATE_SETTLE_SEC = 0.5
DM_CONVERSATION_READY_TIMEOUT_SEC = 12
DM_CONVERSATION_READY_MIN_WORDS = 3
DM_CONVERSATION_READY_POLL_SEC = 0.5
DM_READY_AFTER_NAV_TIMEOUT_SEC = 8
DM_READY_POLL_SEC = 1.0
DM_HISTORY_SCROLL_SETTLE_SEC = 0.8
DM_HISTORY_TOP_CONFIRM_ROUNDS = 1
DM_PASSCODE_POLL_SEC = 3.0
DM_PASSCODE_NOTICE_INTERVAL_SEC = 15.0


# Page-level collection


def collect_messages_page(ws_url: str, dm_threads: int, dm_scrolls: int, dm_max_messages: int, dm_window_hours: int, dm_list_scrolls: int = 20) -> dict[str, Any]:
    extra: dict[str, Any] = {}
    extra["visible_text"] = extract_main_text(ws_url)
    loading_state = dm_page_loading_state(ws_url)
    extra["dm_loading_state"] = loading_state
    if bool(loading_state.get("loading")):
        return {**extra, **dm_loading_timeout_result()}
    extra.update(
        collect_dm_threads(
            ws_url,
            max_threads=dm_threads,
            dm_scrolls=dm_scrolls,
            dm_max_messages=dm_max_messages,
            dm_window_hours=dm_window_hours,
            dm_list_scrolls=dm_list_scrolls,
        )
    )
    return extra

def dm_collection_looks_premature(extra: dict[str, Any]) -> bool:
    status = str(extra.get("dm_status") or "")
    text = " ".join(str(extra.get("visible_text") or "").lower().split())
    if status == "dm_page_loading_timeout":
        return True
    loading_state = extra.get("dm_loading_state") if isinstance(extra.get("dm_loading_state"), dict) else {}
    if bool(loading_state.get("loading")):
        return True
    if status not in {"no_today_threads", "no_visible_threads", "visible_threads_unopened"}:
        return False
    if "start conversation" not in text:
        return False
    return not any(marker in text for marker in DM_CONVERSATION_MARKERS)


def dm_loading_timeout_result() -> dict[str, Any]:
    return {
        "dm_status": "dm_page_loading_timeout",
        "dm_note": (
            "X Messages page still showed skeleton/loading placeholders or Start Conversation before the "
            "conversation list became readable. The collector will retry before treating DMs as unavailable."
        ),
        "dm_threads": [],
        **dm_counts([]),
    }


def collect_dm_threads(ws_url: str, max_threads: int, dm_scrolls: int, dm_max_messages: int, dm_window_hours: int, dm_list_scrolls: int = 20) -> dict[str, Any]:
    main_text = wait_for_dm_ready(ws_url)
    if is_dm_passcode_screen(main_text):
        return {
            "dm_status": "blocked_by_x_chat_passcode",
            "dm_note": "X Chat is asking for an encryption passcode before message content is visible.",
            "dm_threads": [],
            **dm_counts([]),
        }

    list_info = load_dm_thread_list_targets(ws_url, max_scrolls=dm_list_scrolls)
    all_targets = list_info["targets"]
    today_targets = today_dm_targets(all_targets)
    thread_targets = unreplied_dm_targets(today_targets)
    counts = dm_counts(today_targets)
    if not thread_targets:
        return no_unreplied_targets_result(main_text, all_targets, today_targets, counts, list_info)

    threads: list[dict[str, Any]] = []
    seen_targets: set[str] = set()
    for target in thread_targets[: max(max_threads, 0)]:
        if dm_target_key(target) in seen_targets:
            continue
        seen_targets.add(dm_target_key(target))
        threads.append(open_dm_thread(ws_url, target, dm_scrolls, dm_max_messages, dm_window_hours))
        cdp_call(ws_url, "Page.navigate", {"url": "https://x.com/messages"})
        wait_for_dm_ready(ws_url, timeout_sec=DM_READY_AFTER_NAV_TIMEOUT_SEC)

    return with_dm_list_metadata(
        {
            "dm_status": "captured_unreplied_threads" if threads else "no_unreplied_threads",
            "dm_note": (
                f"Today visible DM threads: {counts['dm_visible_thread_count']}; latest from you: {counts['dm_replied_thread_count']}; "
                f"waiting for your reply: {counts['dm_unreplied_thread_count']}. Opened up to {max_threads} waiting-reply thread(s); "
                f"scanned DM list with {list_info['scrolls_used']} downward scroll round(s); "
                f"loaded up to {dm_max_messages} message bubbles per thread with {dm_scrolls} upward scroll round(s); "
                f"captured message bubbles: {sum(int(thread.get('message_count') or 0) for thread in threads)}."
            ),
            "dm_threads": threads,
            "dm_captured_message_count": sum(int(thread.get("message_count") or 0) for thread in threads),
            **counts,
        },
        list_info,
        len(all_targets),
    )


def no_unreplied_targets_result(
    main_text: str,
    all_targets: list[dict[str, Any]],
    today_targets: list[dict[str, Any]],
    counts: dict[str, int],
    list_info: dict[str, Any],
) -> dict[str, Any]:
    if today_targets:
        status = "no_unreplied_threads"
        note = (
            f"DM conversation list was visible with {counts['dm_visible_thread_count']} today thread target(s), "
            "but every latest preview appears to be from you."
        )
    elif all_targets:
        status = "no_today_threads"
        note = f"DM conversation list was visible with {len(all_targets)} older thread target(s), but no today conversation targets were found."
    elif looks_like_dm_list_text(main_text):
        status = "visible_threads_unopened"
        note = "DM conversation list text was visible, but no unreplied openable conversation link or row target could be detected."
    else:
        status = "no_visible_threads"
        note = "No DM conversation links or clickable conversation rows were visible after waiting for the messages page."
    return with_dm_list_metadata(
        {"dm_status": status, "dm_note": note, "dm_threads": [], **counts},
        list_info,
        len(all_targets),
    )


def with_dm_list_metadata(result: dict[str, Any], list_info: dict[str, Any], target_count: int) -> dict[str, Any]:
    return {
        **result,
        "dm_list_scrolls_used": int(list_info.get("scrolls_used") or 0),
        "dm_list_load_complete": bool(list_info.get("load_complete")),
        "dm_list_target_count": target_count,
    }


def open_dm_thread(ws_url: str, target: dict[str, Any], dm_scrolls: int, dm_max_messages: int, dm_window_hours: int) -> dict[str, Any]:
    if not open_dm_target(ws_url, target):
        return skipped_dm_thread(target, "Could not relocate DM row after scanning the thread list.")
    wait_for_dm_conversation_content(ws_url, timeout_sec=DM_CONVERSATION_READY_TIMEOUT_SEC)
    load_info = load_dm_thread_history(ws_url, max_scrolls=dm_scrolls, target_messages=dm_max_messages, window_hours=dm_window_hours)
    messages = extract_dm_messages(ws_url, max_messages=dm_max_messages)
    thread_text = render_dm_messages(messages) or extract_dm_conversation_text(ws_url)
    message_count = len(messages) if messages else count_dm_messages(ws_url)
    return {
        **dm_thread_identity(target),
        "message_count": message_count,
        "dm_scrolls_used": load_info.get("scrolls_used", 0),
        "dm_load_complete": load_info.get("load_complete", False),
        "dm_window_exceeded": load_info.get("window_exceeded", False),
        "dm_hit_message_cap": load_info.get("hit_message_cap", False),
        "messages": messages,
        "text": thread_text,
    }


def open_dm_target(ws_url: str, target: dict[str, Any]) -> bool:
    has_click_point = float(target.get("x") or 0) > 0 and float(target.get("y") or 0) > 0
    if has_click_point:
        cdp_call(ws_url, "Page.navigate", {"url": "https://x.com/messages"})
        wait_for_dm_ready(ws_url, timeout_sec=DM_READY_AFTER_NAV_TIMEOUT_SEC)
        if not restore_dm_thread_list_position(ws_url, target):
            return False
        click_point(ws_url, float(target.get("x") or 0), float(target.get("y") or 0))
        return True
    if target.get("url"):
        cdp_call(ws_url, "Page.navigate", {"url": str(target["url"])})
        return True
    return False


def skipped_dm_thread(target: dict[str, Any], error: str) -> dict[str, Any]:
    return {
        **dm_thread_identity(target),
        "message_count": 0,
        "dm_scrolls_used": 0,
        "dm_load_complete": False,
        "dm_window_exceeded": False,
        "dm_hit_message_cap": False,
        "messages": [],
        "text": "",
        "collection_status": "skipped",
        "collection_error": error,
    }


def dm_thread_identity(target: dict[str, Any]) -> dict[str, Any]:
    return {
        "url": str(target.get("url") or ""),
        "label": str(target.get("label") or ""),
        "participant": dm_participant(target),
        "target_type": str(target.get("target_type") or ""),
        "replied": bool(target.get("replied")),
        "reply_reason": str(target.get("reply_reason") or ""),
        "today": bool(target.get("today")),
    }


# Conversation-list scanning


def load_dm_thread_list_targets(ws_url: str, max_scrolls: int = 20) -> dict[str, Any]:
    scroll_limit = max(0, int(max_scrolls))
    targets = extract_dm_thread_targets(ws_url)
    previous_today = len(today_dm_targets(targets))
    previous_total = len(targets)
    stable_rounds = 0
    scrolls_used = 0
    at_bottom = False

    for _ in range(scroll_limit):
        if at_bottom and stable_rounds >= DM_LIST_BOTTOM_CONFIRM_ROUNDS:
            break
        info = scroll_dm_thread_list_down(ws_url)
        scrolls_used += 1
        time.sleep(DM_LIST_SCROLL_SETTLE_SEC)
        current = dedupe_dm_targets([*targets, *extract_dm_thread_targets(ws_url)])
        current_today = len(today_dm_targets(current))
        current_total = len(current)
        at_bottom = bool(info.get("at_bottom"))
        if current_today <= previous_today and current_total <= previous_total:
            stable_rounds += 1
        else:
            stable_rounds = 0
        targets = current
        previous_today = current_today
        previous_total = current_total
        if dm_list_scan_should_stop(current_total, current_today, stable_rounds):
            break

    return {
        "targets": targets,
        "scrolls_used": scrolls_used,
        "load_complete": at_bottom or stable_rounds >= DM_LIST_STABLE_STOP_ROUNDS,
        "stable_rounds": stable_rounds,
    }

def scroll_dm_thread_list_down(ws_url: str) -> dict[str, Any]:
    script = load_dom_script("scroll_dm_thread_list_down.js")
    value = cdp_eval(ws_url, script)
    return value if isinstance(value, dict) else {}


def dm_list_scan_should_stop(total_targets: int, today_targets_count: int, stable_rounds: int) -> bool:
    if stable_rounds >= DM_LIST_STABLE_STOP_ROUNDS:
        return True
    reached_older_threads_after_today = total_targets > 0 and today_targets_count > 0 and today_targets_count < total_targets
    return reached_older_threads_after_today and stable_rounds >= DM_LIST_OLDER_AFTER_TODAY_STABLE_ROUNDS


def restore_dm_thread_list_position(ws_url: str, target: dict[str, Any]) -> bool:
    key = dm_target_key(target)
    for _ in range(DM_ROW_RELOCATE_MAX_SCROLLS):
        candidates = {dm_target_key(item): item for item in extract_dm_thread_targets(ws_url)}
        current = candidates.get(key)
        if current:
            target["x"] = current.get("x") or target.get("x")
            target["y"] = current.get("y") or target.get("y")
            return True
        scroll_dm_thread_list_down(ws_url)
        time.sleep(DM_ROW_RELOCATE_SETTLE_SEC)
    return False


# Conversation loading and message extraction


def wait_for_dm_conversation_content(ws_url: str, timeout_sec: int = 12) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if count_dm_messages(ws_url) > 0:
            return
        text = extract_dm_conversation_text(ws_url)
        if text and not is_dm_passcode_screen(text) and len(text.split()) > DM_CONVERSATION_READY_MIN_WORDS:
            return
        time.sleep(DM_CONVERSATION_READY_POLL_SEC)

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
    return bool(DM_SELF_REPLY_RE.search(normalized))

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
        time.sleep(DM_HISTORY_SCROLL_SETTLE_SEC)
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
        if reached_top and stable_top_rounds >= DM_HISTORY_TOP_CONFIRM_ROUNDS:
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
    script = load_dom_script("get_dm_history_state.js")
    value = cdp_eval(ws_url, script)
    return value if isinstance(value, dict) else {}

def scroll_dm_messages_up(ws_url: str) -> dict[str, Any]:
    script = load_dom_script("scroll_dm_messages_up.js")
    value = cdp_eval(ws_url, script)
    return value if isinstance(value, dict) else {}

def dm_loaded_beyond_window(ws_url: str, window_hours: int) -> bool:
    script = load_dom_script("dm_loaded_beyond_window.js") % max(1, int(window_hours))
    return bool(cdp_eval(ws_url, script))

def count_dm_messages(ws_url: str) -> int:
    script = load_dom_script("count_dm_messages.js")
    value = cdp_eval(ws_url, script)
    return int(value) if isinstance(value, (int, float)) else 0

def extract_dm_messages(ws_url: str, max_messages: int = 300) -> list[dict[str, Any]]:
    script = load_dom_script("extract_dm_messages.js") % max(1, int(max_messages))
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
    script = load_dom_script("extract_dm_conversation_text.js")
    value = cdp_eval(ws_url, script)
    return str(value or "")


# Page readiness and status detection


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
        state = dm_page_loading_state(ws_url)
        if bool(state.get("loading")):
            time.sleep(DM_READY_POLL_SEC)
            continue
        normalized = " ".join(text.lower().split())
        if any(marker in normalized for marker in DM_EMPTY_MARKERS):
            return text
        time.sleep(DM_READY_POLL_SEC)
    return last_text

def dm_page_loading_state(ws_url: str) -> dict[str, Any]:
    script = load_dom_script("dm_page_loading_state.js")
    value = cdp_eval(ws_url, script)
    return value if isinstance(value, dict) else {}

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
    return any(phrase in normalized for phrase in DM_PASSCODE_PHRASES)

def wait_for_dm_passcode_resolution(port: int, timeout_sec: int) -> bool:
    ws_url = wait_for_cdp_page_ws(port)
    cdp_call(ws_url, "Page.enable")
    cdp_call(ws_url, "Runtime.enable")
    cdp_call(ws_url, "Page.navigate", {"url": "https://x.com/messages"})
    print("X Chat passcode is required. Complete it in the opened browser window; collection will resume automatically.")
    deadline = time.time() + timeout_sec
    last_notice = 0.0
    while time.time() < deadline:
        time.sleep(DM_PASSCODE_POLL_SEC)
        main_text = extract_main_text(ws_url)
        if is_dm_passcode_screen(main_text):
            if time.time() - last_notice > DM_PASSCODE_NOTICE_INTERVAL_SEC:
                print("Still waiting for X Chat passcode to be completed in the opened browser window.")
                last_notice = time.time()
            continue
        if dm_messages_page_is_readable(ws_url, main_text):
            print("X Chat messages are readable. Resuming DM collection...")
            return True
        if time.time() - last_notice > DM_PASSCODE_NOTICE_INTERVAL_SEC:
            print("Passcode screen is not readable yet or messages are still loading. Keep the visible browser open until X Messages shows the inbox.")
            last_notice = time.time()
    return False

def dm_messages_page_is_readable(ws_url: str, text: str) -> bool:
    if is_dm_passcode_screen(text):
        return False
    if extract_dm_thread_targets(ws_url):
        return True
    normalized = " ".join(text.lower().split())
    if any(marker in normalized for marker in DM_EMPTY_MARKERS):
        return True
    return False


# Conversation target parsing


def extract_dm_thread_targets(ws_url: str) -> list[dict[str, Any]]:
    script = load_dom_script("extract_dm_thread_targets.js")
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
    if DM_TODAY_WORD_RE.search(normalized):
        return True
    if DM_TODAY_AGE_RE.search(normalized):
        return True
    if DM_TODAY_CN_RE.search(normalized):
        return True
    if DM_OLD_TIME_RE.search(normalized):
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
