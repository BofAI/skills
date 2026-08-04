#!/usr/bin/env python3
"""Collect and decrypt recent X Chat conversations for twitter-digest."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from chat_config_store import load_chat_config


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
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GET {path} failed with HTTP {exc.code}: {detail[:800]}") from exc


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


def collect_events(token: str, conversation_id: str, cutoff: dt.datetime) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    key_events: list[str] = []
    next_token = ""
    while True:
        payload = api_get(
            token,
            f"/chat/conversations/{urllib.parse.quote(conversation_id, safe='')}/events",
            {
                "max_results": 100,
                "pagination_token": next_token,
                "chat_message_event.fields": "conversation_id,conversation_token,created_at,encoded_event,id,is_trusted,message_event_signature,previous_id,sender_id",
            },
        )
        page = [item for item in payload.get("data") or [] if isinstance(item, dict)]
        events.extend(page)
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        key_events.extend(str(item) for item in meta.get("conversation_key_events") or [] if item)
        next_token = str(meta.get("next_token") or "")
        oldest = min((stamp for stamp in (event_time(item) for item in page) if stamp), default=None)
        if not next_token or (oldest and oldest < cutoff):
            break
    return events, list(dict.fromkeys(key_events))


def signing_keys(token: str, user_ids: set[str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for user_id in sorted(user_ids):
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
        "dm_load_complete": False,
        "dm_scrolls_used": 0,
        "dm_window_exceeded": False,
        "dm_hit_message_cap": False,
    }


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
    users_to_fetch = {user_id}
    for conversation in conversations:
        users_to_fetch.update(participant_ids(conversation, user_id))
    chat = Chat()
    chat.import_keys(private_blob, version=key_version)
    chat.set_identity(user_id, key_version)
    chat.set_signing_keys(signing_keys(args.bearer_token, users_to_fetch))
    chat.set_cache_keys(True)

    threads = []
    errors = []
    fetched_event_count = 0
    unavailable_thread_count = 0
    for conversation in conversations:
        updated_at = parse_time(conversation.get("updated_at"))
        if updated_at and updated_at < cutoff:
            continue
        conversation_id = str(conversation.get("id") or "")
        if not conversation_id:
            continue
        try:
            raw_events, key_events = collect_events(args.bearer_token, conversation_id, cutoff)
            fetched_event_count += len(raw_events)
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
            encoded_events = key_events + [str(event.get("encoded_event")) for event in reversed(window_events)]
            decrypted = chat.decrypt_events(encoded_events)
            if decrypted.get("errors"):
                raise RuntimeError(f"Chat XDK could not decrypt or verify {len(decrypted['errors'])} event(s)")
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
                "dm_load_complete": True,
                "dm_scrolls_used": 0,
                "dm_window_exceeded": False,
                "dm_hit_message_cap": False,
            }
        )
    threads.sort(key=lambda item: str(item.get("latest_time") or ""), reverse=True)
    if errors:
        raise SystemExit("X Chat collection/decryption failed: " + "; ".join(errors)[:1800])
    if conversations and fetched_event_count == 0:
        raise SystemExit(
            "X Chat history returned zero events for every listed conversation. "
            "The OAuth token may be missing dm.write or the Chat history endpoint is not returning authorized data; "
            "refusing to report an empty inbox."
        )
    waiting = [thread for thread in threads if thread.get("reply_state") == "waiting_reply"]
    replied = [thread for thread in threads if thread.get("reply_state") == "last_from_me"]
    payload = {
        "kind": "messages",
        "url": "https://api.x.com/2/chat/conversations",
        "items": [],
        "dm_status": "x_chat_collected",
        "dm_note": "X Chat messages were decrypted locally with Chat XDK. The X Chat passcode was not stored.",
        "dm_threads": threads,
        "dm_visible_thread_count": len(threads),
        "dm_replied_thread_count": len(replied),
        "dm_unreplied_thread_count": len(waiting),
        "dm_unknown_thread_count": unavailable_thread_count,
        "dm_captured_message_count": sum(int(thread.get("message_count") or 0) for thread in threads),
        "dm_has_message_requests": has_message_requests,
        "data_gaps": [
            {
                "source": "x_chat",
                "status": "conversation_history_unavailable",
                "detail": (
                    f"{unavailable_thread_count} listed X Chat conversation(s) had no readable messages in the requested {max(1, args.hours)}-hour window. "
                    "Do not infer that these conversations are empty or already handled."
                ),
            }
        ] if unavailable_thread_count else [],
        "todo_items": (
            [
                {
                    "source": "x_chat",
                    "status": "message_request_pending",
                    "detail": "X reports at least one pending Chat message request. Review Requests in X; the API does not identify which listed conversation is pending.",
                }
            ]
            if has_message_requests
            else []
        ),
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
