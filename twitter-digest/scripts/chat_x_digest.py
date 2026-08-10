#!/usr/bin/env python3
"""Collect and decrypt recent X Chat conversations for twitter-digest."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from chat_config_store import cached_signing_keys, load_chat_config


MAX_API_ATTEMPTS = 4
RETRYABLE_HTTP_CODES = {408, 425, 429, 500, 502, 503, 504}
DEFAULT_EVENT_REQUEST_BUDGET = 20
DEFAULT_EVENT_RATE_LIMIT_RESERVE = 5
DEFAULT_MAX_EVENT_PAGES_PER_CONVERSATION = 3
DEFAULT_MAX_CONSECUTIVE_OLD_CONVERSATIONS = 3
EVENT_RATE_LIMIT_ROUTE = "/chat/conversations/:id/events"
RATE_LIMIT_TRACKER: dict[str, dict[str, int]] = {}


class RateLimitError(RuntimeError):
    """Stop the entire Chat collection when X reports a shared rate limit."""


class EventBudgetExhausted(RuntimeError):
    """Stop safely before the X Chat events endpoint reaches its limit."""


class EventRequestBudget:
    def __init__(self, max_requests: int, reserve: int = DEFAULT_EVENT_RATE_LIMIT_RESERVE) -> None:
        self.max_requests = max(1, max_requests)
        self.reserve = max(0, reserve)
        self.used = 0

    def consume(self, now: float | None = None) -> None:
        if self.used >= self.max_requests:
            raise EventBudgetExhausted("safe_event_request_budget")
        current_time = time.time() if now is None else now
        state = RATE_LIMIT_TRACKER.get(EVENT_RATE_LIMIT_ROUTE) or {}
        remaining = state.get("remaining")
        reset = state.get("reset")
        if remaining is not None and (reset is None or reset > current_time) and remaining <= self.reserve:
            raise EventBudgetExhausted("reported_rate_limit_reserve")
        self.used += 1


class OldConversationStopper:
    def __init__(self, max_consecutive: int) -> None:
        self.max_consecutive = max(1, max_consecutive)
        self.consecutive = 0

    def observe(self, is_old: bool) -> bool:
        self.consecutive = self.consecutive + 1 if is_old else 0
        return self.consecutive >= self.max_consecutive


def normalize_rate_limit_route(path: str) -> str:
    if path.startswith("/chat/conversations/") and path.endswith("/events"):
        return EVENT_RATE_LIMIT_ROUTE
    if path.startswith("/users/") and path.endswith("/public_keys"):
        return "/users/:id/public_keys"
    return path


def observe_rate_limit(path: str, headers: Any) -> None:
    try:
        limit = int(str(headers.get("x-rate-limit-limit", "")))
        remaining = int(str(headers.get("x-rate-limit-remaining", "")))
        reset = int(str(headers.get("x-rate-limit-reset", "")))
    except (AttributeError, TypeError, ValueError):
        return
    RATE_LIMIT_TRACKER[normalize_rate_limit_route(path)] = {
        "limit": limit,
        "remaining": remaining,
        "reset": reset,
    }


def retry_delay(attempt: int, retry_after: str = "") -> float:
    try:
        return max(0.0, min(float(retry_after), 60.0))
    except (TypeError, ValueError):
        return min(2 ** (attempt - 1), 8)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bearer-token", default=os.environ.get("X_BEARER_TOKEN") or "")
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--max-conversations", type=int, default=50)
    parser.add_argument("--out", required=True)
    return parser.parse_args()


def api_get(token: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    query = urllib.parse.urlencode({key: value for key, value in (params or {}).items() if value not in (None, "")})
    url = "https://api.x.com/2" + path + (("?" + query) if query else "")
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": "twitter-digest-chat/1.0"})
    for attempt in range(1, MAX_API_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
                observe_rate_limit(path, response.headers)
                return payload
        except urllib.error.HTTPError as exc:
            observe_rate_limit(path, exc.headers)
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code == 429:
                retry_after = rate_limit_retry_after(exc.headers)
                suffix = f"; retry after about {retry_after} seconds" if retry_after is not None else ""
                raise RateLimitError(f"GET {path} failed with HTTP 429 Too Many Requests{suffix}: {detail[:800]}") from exc
            if exc.code not in RETRYABLE_HTTP_CODES or attempt == MAX_API_ATTEMPTS:
                raise RuntimeError(f"GET {path} failed with HTTP {exc.code}: {detail[:800]}") from exc
            time.sleep(retry_delay(attempt, exc.headers.get("Retry-After", "")))
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            if attempt == MAX_API_ATTEMPTS:
                raise RuntimeError(
                    f"GET {path} failed after {MAX_API_ATTEMPTS} attempts: {exc}"
                ) from exc
            time.sleep(retry_delay(attempt))
    raise AssertionError("unreachable")


def rate_limit_retry_after(headers: Any) -> int | None:
    retry_after = str(headers.get("Retry-After", "") or "").strip()
    if retry_after:
        try:
            return max(0, int(float(retry_after)))
        except ValueError:
            pass
    reset = str(headers.get("x-rate-limit-reset", "") or "").strip()
    if reset:
        try:
            return max(0, int(float(reset) - time.time()))
        except ValueError:
            pass
    return None


def parse_time(value: Any) -> dt.datetime | None:
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=dt.timezone.utc) if parsed.tzinfo is None else parsed
    except (TypeError, ValueError):
        return None


def event_time(event: dict[str, Any]) -> dt.datetime | None:
    milliseconds = event.get("created_at_msec")
    if milliseconds not in (None, ""):
        try:
            return dt.datetime.fromtimestamp(int(str(milliseconds)) / 1000, tz=dt.timezone.utc)
        except (TypeError, ValueError, OverflowError):
            return None
    return parse_time(event.get("created_at"))


def collect_conversations(token: str, maximum: int) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], bool]:
    conversations: list[dict[str, Any]] = []
    users: dict[str, dict[str, Any]] = {}
    has_message_requests = False
    next_token = ""
    while len(conversations) < maximum:
        payload = api_get(
            token,
            "/chat/conversations",
            {
                "max_results": min(100, maximum - len(conversations)),
                "pagination_token": next_token,
                "chat_conversation.fields": "id,type,group_name,created_at,updated_at",
                "expansions": "participant_ids,member_ids",
                "user.fields": "id,username,name",
            },
        )
        conversations.extend(item for item in payload.get("data") or [] if isinstance(item, dict))
        includes = payload.get("includes") if isinstance(payload.get("includes"), dict) else {}
        for user in includes.get("users") or []:
            if isinstance(user, dict) and user.get("id"):
                users[str(user["id"])] = user
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        has_message_requests = has_message_requests or bool(meta.get("has_message_requests"))
        next_token = str(meta.get("next_token") or "")
        if not next_token:
            break
    return conversations[:maximum], users, has_message_requests


def collect_events(
    token: str,
    conversation_id: str,
    cutoff: dt.datetime,
    budget: EventRequestBudget,
    max_pages: int = DEFAULT_MAX_EVENT_PAGES_PER_CONVERSATION,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    events: list[dict[str, Any]] = []
    key_events: list[str] = []
    next_token = ""
    pages_used = 0
    stop_reason = ""
    while True:
        try:
            budget.consume()
        except EventBudgetExhausted:
            if not events:
                raise
            stop_reason = "event_request_budget"
            break
        payload = api_get(
            token,
            f"/chat/conversations/{urllib.parse.quote(conversation_id, safe='')}/events",
            {
                "max_results": 100,
                "pagination_token": next_token,
                "chat_message_event.fields": "conversation_id,conversation_token,created_at,encoded_event,id,is_trusted,message_event_signature,previous_id,sender_id",
            },
        )
        pages_used += 1
        page = [item for item in payload.get("data") or [] if isinstance(item, dict)]
        events.extend(page)
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        key_events.extend(str(item) for item in meta.get("conversation_key_events") or [] if item)
        next_token = str(meta.get("next_token") or "")
        oldest = min((stamp for stamp in (event_time(item) for item in page) if stamp), default=None)
        if not next_token:
            break
        if oldest and oldest < cutoff:
            stop_reason = "window_complete"
            break
        if pages_used >= max(1, max_pages):
            stop_reason = "conversation_page_limit"
            break
    truncated = bool(next_token and stop_reason not in {"", "window_complete"})
    return events, list(dict.fromkeys(key_events)), {
        "pages_used": pages_used,
        "truncated": truncated,
        "stop_reason": stop_reason,
    }


def fetch_user_signing_keys(token: str, user_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    payload = api_get(
        token,
        f"/users/{user_id}/public_keys",
        {"public_key.fields": "public_key_version,public_key,signing_public_key,identity_public_key_signature"},
    )
    for record in payload.get("data") or []:
        if not isinstance(record, dict):
            continue
        result.append(
            {
                "user_id": user_id,
                "public_key_version": str(record.get("public_key_version") or ""),
                "public_key": str(record.get("signing_public_key") or ""),
                "identity_public_key": str(record.get("public_key") or ""),
                "identity_public_key_signature": str(record.get("identity_public_key_signature") or ""),
            }
        )
    return result


def signing_keys(
    token: str,
    owner_user_id: str,
    user_ids: set[str],
    force_refresh_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    return cached_signing_keys(
        owner_user_id,
        user_ids,
        lambda user_id: fetch_user_signing_keys(token, user_id),
        force_refresh_ids=force_refresh_ids,
    )


def participant_ids(conversation: dict[str, Any], current_user_id: str) -> set[str]:
    values = conversation.get("participant_ids") or conversation.get("member_ids") or []
    return {str(value) for value in values if value and str(value) != current_user_id}


def participant_label(conversation: dict[str, Any], users: dict[str, dict[str, Any]], current_user_id: str) -> str:
    if conversation.get("group_name"):
        return str(conversation["group_name"])
    labels = []
    for user_id in sorted(participant_ids(conversation, current_user_id)):
        user = users.get(user_id) or {}
        labels.append("@" + str(user["username"]) if user.get("username") else str(user.get("name") or user_id))
    return ", ".join(labels) or str(conversation.get("id") or "")


def unavailable_thread(
    conversation: dict[str, Any],
    users: dict[str, dict[str, Any]],
    current_user_id: str,
    status: str,
    detail: str,
) -> dict[str, Any]:
    conversation_id = str(conversation.get("id") or "")
    label = participant_label(conversation, users, current_user_id)
    return {
        "participant": label,
        "label": label,
        "url": f"https://x.com/messages/{conversation_id}",
        "reply_state": "unknown",
        "replied": None,
        "message_count": 0,
        "messages": [],
        "text": "",
        "latest_time": str(conversation.get("updated_at") or ""),
        "collection_status": status,
        "collection_detail": detail,
        "requires_user_ui": True,
        "user_action": (
            "Agent/API 无法读取这段会话历史，这不代表存在未读消息。"
            "如需确认，请打开该会话，在 X 界面查看最新消息和未读状态。"
        ),
        "dm_load_complete": False,
        "dm_scrolls_used": 0,
        "dm_window_exceeded": False,
        "dm_hit_message_cap": False,
    }


def zero_event_history_is_failure(
    conversations: list[dict[str, Any]],
    fetched_event_count: int,
    *,
    scan_complete: bool,
) -> bool:
    """Treat an empty history as an error only after every listed chat was checked."""
    return bool(conversations) and fetched_event_count == 0 and scan_complete


def main() -> None:
    args = parse_args()
    if not args.bearer_token:
        raise SystemExit("X Chat collection requires the saved OAuth2 user token.")
    config = load_chat_config()
    user_id = str(config.get("user_id") or "")
    key_version = str(config.get("key_version") or "")
    try:
        private_blob = base64.b64decode(str(config.get("private_key_blob") or ""), validate=True)
    except ValueError as exc:
        raise SystemExit("Saved X Chat private-key blob is invalid. Reconfigure X Chat.") from exc
    if not user_id or not key_version or not private_blob:
        raise SystemExit("X Chat is not configured.")

    from chat_xdk import Chat

    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=max(1, args.hours))
    conversations, users, has_message_requests = collect_conversations(args.bearer_token, max(1, args.max_conversations))
    chat = Chat()
    chat.import_keys(private_blob, version=key_version)
    chat.set_identity(user_id, key_version)
    chat.set_cache_keys(True)

    threads = []
    errors = []
    fetched_event_count = 0
    unavailable_thread_count = 0
    refreshed_user_ids: set[str] = set()
    event_budget = EventRequestBudget(DEFAULT_EVENT_REQUEST_BUDGET)
    old_stopper = OldConversationStopper(DEFAULT_MAX_CONSECUTIVE_OLD_CONVERSATIONS)
    scanned_conversation_count = 0
    old_conversation_count = 0
    truncated_conversation_count = 0
    scan_complete = True
    scan_stop_reason = ""
    for conversation in conversations:
        conversation_id = str(conversation.get("id") or "")
        if not conversation_id:
            continue
        try:
            raw_events, key_events, event_scan = collect_events(
                args.bearer_token,
                conversation_id,
                cutoff,
                event_budget,
            )
            scanned_conversation_count += 1
            fetched_event_count += len(raw_events)
            newest_event = max((stamp for stamp in (event_time(item) for item in raw_events) if stamp), default=None)
            if newest_event and newest_event < cutoff:
                old_conversation_count += 1
                if old_stopper.observe(is_old=True):
                    scan_complete = False
                    scan_stop_reason = "consecutive_old_conversations"
                    break
                continue
            old_stopper.observe(is_old=False)
            if not raw_events:
                unavailable_thread_count += 1
                threads.append(
                    unavailable_thread(
                        conversation,
                        users,
                        user_id,
                        "history_unavailable",
                        "X Chat listed this conversation but returned no event history. Its reply state and message contents are unknown.",
                    )
                )
                continue
            window_events = [
                event
                for event in raw_events
                if event.get("encoded_event") and (event_time(event) or dt.datetime.min.replace(tzinfo=dt.timezone.utc)) >= cutoff
            ]
            conversation_user_ids = {user_id} | participant_ids(conversation, user_id)
            chat.set_signing_keys(signing_keys(args.bearer_token, user_id, conversation_user_ids))
            encoded_events = key_events + [str(event.get("encoded_event")) for event in reversed(window_events)]
            decrypted = chat.decrypt_events(encoded_events)
            if decrypted.get("errors"):
                refresh_ids = conversation_user_ids - refreshed_user_ids
                if refresh_ids:
                    chat.set_signing_keys(
                        signing_keys(args.bearer_token, user_id, conversation_user_ids, force_refresh_ids=refresh_ids)
                    )
                    refreshed_user_ids.update(refresh_ids)
                    decrypted = chat.decrypt_events(encoded_events)
                if decrypted.get("errors"):
                    raise RuntimeError(f"Chat XDK could not decrypt or verify {len(decrypted['errors'])} event(s)")
            if event_scan.get("truncated"):
                truncated_conversation_count += 1
        except EventBudgetExhausted as exc:
            scan_complete = False
            scan_stop_reason = str(exc)
            break
        except RateLimitError as exc:
            raise SystemExit(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001 - preserve the conversation id for any SDK/API failure.
            errors.append(f"{conversation_id}: {exc}")
            continue
        messages = []
        raw_by_encoded = {str(event.get("encoded_event") or ""): event for event in window_events}
        for row in decrypted.get("messages") or []:
            event = row.get("event") if isinstance(row, dict) else None
            if not isinstance(event, dict) or str(event.get("type") or "").lower() != "message":
                continue
            content = event.get("content") if isinstance(event.get("content"), dict) else {}
            content_type = str(content.get("content_type") or "Unknown")
            text = str(content.get("text") or "")
            if content_type.lower() != "text":
                text = f"[X Chat content type not supported by Chat XDK: {content_type}]"
            raw_event = raw_by_encoded.get(str(row.get("original_b64") or "")) or {}
            created_at = event_time(raw_event)
            if not created_at or created_at < cutoff:
                continue
            sender_id = str(event.get("sender_id") or raw_event.get("sender_id") or "")
            messages.append(
                {
                    "sender": "me" if sender_id == user_id else "other",
                    "sender_id": sender_id,
                    "time": created_at.isoformat() if created_at else "",
                    "text": text,
                    "content_type": content_type,
                    "verified": bool(event.get("verified")),
                }
            )
        messages.sort(key=lambda item: str(item.get("time") or ""))
        if not messages:
            unavailable_thread_count += 1
            threads.append(
                unavailable_thread(
                    conversation,
                    users,
                    user_id,
                    "no_readable_messages_in_window",
                    "X Chat returned events, but no readable message with a valid timestamp was available in the requested window.",
                )
            )
            continue
        replied = messages[-1].get("sender") == "me"
        label = participant_label(conversation, users, user_id)
        threads.append(
            {
                "participant": label,
                "label": label,
                "url": f"https://x.com/messages/{conversation_id}",
                "replied": replied,
                "message_count": len(messages),
                "messages": messages,
                "text": "\n".join(f"{item['sender']} {item['time']}: {item['text']}" for item in messages),
                "latest_time": str(messages[-1].get("time") or ""),
                "reply_state": "last_from_me" if replied else "waiting_reply",
                "collection_status": "complete",
                "collection_detail": "",
                "dm_load_complete": not bool(event_scan.get("truncated")),
                "dm_scrolls_used": int(event_scan.get("pages_used") or 0),
                "dm_window_exceeded": False,
                "dm_hit_message_cap": bool(event_scan.get("truncated")),
            }
        )
    threads.sort(key=lambda item: str(item.get("latest_time") or ""), reverse=True)
    if errors:
        raise SystemExit("X Chat collection/decryption failed: " + "; ".join(errors)[:1800])
    if zero_event_history_is_failure(
        conversations,
        fetched_event_count,
        scan_complete=scan_complete,
    ):
        raise SystemExit(
            "X Chat history returned zero events for every listed conversation. "
            "The read-only OAuth token may lack access to this X Chat history endpoint; "
            "refusing to report an empty inbox."
        )
    waiting = [thread for thread in threads if thread.get("reply_state") == "waiting_reply"]
    replied = [thread for thread in threads if thread.get("reply_state") == "last_from_me"]
    data_gaps = []
    if unavailable_thread_count:
        data_gaps.append(
            {
                "source": "x_chat",
                "status": "conversation_history_unavailable",
                "detail": (
                    f"{unavailable_thread_count} listed X Chat conversation(s) had no readable messages in the requested {max(1, args.hours)}-hour window. "
                    "Do not infer that these conversations are empty, unread, or already handled."
                ),
            }
        )
    if not scan_complete or truncated_conversation_count:
        data_gaps.append(
            {
                "source": "x_chat",
                "status": "safe_scan_limited",
                "detail": (
                    f"X Chat safely checked {scanned_conversation_count} of {len(conversations)} listed conversations using "
                    f"{event_budget.used} event request(s). stop_reason={scan_stop_reason or 'conversation_page_limit'}; "
                    f"truncated_conversations={truncated_conversation_count}. Do not claim unscanned conversations had no messages."
                ),
            }
        )
    payload = {
        "kind": "messages",
        "url": "https://api.x.com/2/chat/conversations",
        "items": [],
        "dm_status": "x_chat_collected",
        "dm_window_hours": max(1, args.hours),
        "dm_note": "X Chat messages were decrypted locally with Chat XDK. The X Chat passcode was not stored.",
        "dm_threads": threads,
        "dm_visible_thread_count": len(threads),
        "dm_replied_thread_count": len(replied),
        "dm_unreplied_thread_count": len(waiting),
        "dm_unknown_thread_count": unavailable_thread_count,
        "dm_captured_message_count": sum(int(thread.get("message_count") or 0) for thread in threads),
        "dm_has_message_requests": has_message_requests,
        "dm_listed_conversation_count": len(conversations),
        "dm_scanned_conversation_count": scanned_conversation_count,
        "dm_old_conversation_count": old_conversation_count,
        "dm_event_request_count": event_budget.used,
        "dm_scan_complete": scan_complete and truncated_conversation_count == 0,
        "dm_scan_stop_reason": scan_stop_reason,
        "dm_truncated_conversation_count": truncated_conversation_count,
        "data_gaps": data_gaps,
        "todo_items": (
            [
                {
                    "source": "x_chat",
                    "status": "message_request_pending",
                    "detail": "X reports at least one pending Chat message request, but the API does not identify the sender or expose the request contents.",
                    "requires_user_ui": True,
                    "user_action": "需要你手动操作：打开 X → 消息 → 请求，查看发送者和内容后，自行选择接受、删除或忽略。Agent 不会代为接受或回复。",
                    "action_url": "https://x.com/messages",
                }
            ]
            if has_message_requests
            else []
        ),
    }
    output_path = Path(args.out)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_path.chmod(0o600)


if __name__ == "__main__":
    main()
