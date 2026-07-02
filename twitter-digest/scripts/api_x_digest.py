#!/usr/bin/env python3
"""Collect X/Twitter digest input through the official API when configured."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional

from digest_io import write_digest_output


API_BASE = "https://api.x.com/2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    default_state_dir = Path(__file__).resolve().parents[1] / ".state"
    parser.add_argument("--handle", help="Your X handle, with or without @.")
    parser.add_argument("--user-id", default=os.environ.get("X_USER_ID") or os.environ.get("TWITTER_USER_ID") or "")
    parser.add_argument("--bearer-token", default=os.environ.get("X_BEARER_TOKEN") or os.environ.get("TWITTER_BEARER_TOKEN") or "")
    parser.add_argument("--api-base", default=os.environ.get("X_API_BASE_URL") or API_BASE)
    parser.add_argument("--keywords", default="", help="Comma-separated keywords or queries for optional search.")
    parser.add_argument("--out", default=str(default_state_dir / "run"))
    parser.add_argument("--include-dms", action="store_true", help="Try DM endpoints when API access supports them.")
    parser.add_argument("--dm-max-events", type=int, default=300, help="Maximum Direct Message events kept from the API.")
    parser.add_argument("--max-public-items", type=int, default=300)
    parser.add_argument("--public-window-hours", type=int, default=24)
    parser.add_argument("--scrolls", type=int, default=0, help=argparse.SUPPRESS)
    return parser.parse_args()


def auth_headers(args: argparse.Namespace) -> dict[str, str]:
    if args.bearer_token:
        return {"Authorization": f"Bearer {args.bearer_token}", "User-Agent": "twitter-digest/1.0"}
    return {"User-Agent": "twitter-digest/1.0"}


def api_get(args: argparse.Namespace, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None and v != ""})
    url = args.api_base.rstrip("/") + path
    if query:
        url += "?" + query
    request = urllib.request.Request(url, headers=auth_headers(args))
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GET {path} failed with HTTP {exc.code}: {body[:1000]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GET {path} failed: {exc}") from exc


def resolve_user(args: argparse.Namespace, handle: Optional[str], user_id: Optional[str]) -> dict[str, str]:
    if user_id:
        try:
            result = api_get(args, f"/users/{user_id}", {"user.fields": "username,name"})
            data = result.get("data") if isinstance(result, dict) else None
            if isinstance(data, dict):
                return {"id": str(data.get("id") or user_id), "username": str(data.get("username") or handle or ""), "name": str(data.get("name") or "")}
        except RuntimeError:
            pass
    if handle:
        clean = handle.lstrip("@")
        try:
            result = api_get(args, f"/users/by/username/{urllib.parse.quote(clean)}", {"user.fields": "username,name"})
            data = result.get("data") if isinstance(result, dict) else None
            if isinstance(data, dict):
                return {"id": str(data.get("id") or ""), "username": str(data.get("username") or clean), "name": str(data.get("name") or "")}
        except RuntimeError:
            pass
    result = api_get(args, "/users/me", {"user.fields": "username,name"})
    data = result.get("data") if isinstance(result, dict) else None
    if isinstance(data, dict):
        return {"id": str(data.get("id") or ""), "username": str(data.get("username") or ""), "name": str(data.get("name") or "")}
    raise RuntimeError("Could not resolve X API user. Provide --handle or X_USER_ID when /users/me is unavailable.")


def window_start(hours: int) -> str:
    start = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=max(1, hours))
    return start.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def tweet_params(max_results: int, hours: int) -> dict[str, Any]:
    return {
        "max_results": max(10, min(100, max_results)),
        "start_time": window_start(hours),
        "tweet.fields": "created_at,public_metrics,entities,attachments,referenced_tweets,conversation_id",
        "expansions": "author_id,attachments.media_keys,referenced_tweets.id,referenced_tweets.id.author_id",
        "media.fields": "url,preview_image_url,alt_text,type",
        "user.fields": "username,name",
    }


def dm_params(max_results: int, hours: int) -> dict[str, Any]:
    return {
        "max_results": max(10, min(100, max_results)),
        "dm_event.fields": "id,text,event_type,created_at,dm_conversation_id,sender_id,participant_ids,attachments,referenced_tweets",
        "expansions": "sender_id,participant_ids,attachments.media_keys,referenced_tweets.id",
        "user.fields": "username,name",
        "media.fields": "url,preview_image_url,alt_text,type",
        "post.fields": "created_at,author_id,text,entities",
    }


def collect_paginated(
    args: argparse.Namespace,
    path: str,
    params: dict[str, Any],
    max_items: int,
    page_token_name: str = "pagination_token",
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    items: list[dict[str, Any]] = []
    includes: dict[str, Any] = {"users": [], "media": [], "tweets": []}
    errors: list[str] = []
    next_token = ""
    seen_ids: set[str] = set()
    while len(items) < max_items:
        page_params = dict(params)
        if next_token:
            page_params[page_token_name] = next_token
        try:
            result = api_get(args, path, page_params)
        except RuntimeError as exc:
            errors.append(str(exc))
            break
        data = result.get("data") if isinstance(result, dict) else None
        new_items: list[dict[str, Any]] = []
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                item_id = str(item.get("id") or "")
                if item_id and item_id in seen_ids:
                    continue
                if item_id:
                    seen_ids.add(item_id)
                new_items.append(item)
            items.extend(new_items)
        inc = result.get("includes") if isinstance(result, dict) else None
        if isinstance(inc, dict):
            for key in includes:
                value = inc.get(key)
                if isinstance(value, list):
                    includes[key].extend(item for item in value if isinstance(item, dict))
        meta = result.get("meta") if isinstance(result, dict) else {}
        next_token = str(meta.get("next_token") or "") if isinstance(meta, dict) else ""
        if not next_token or not data or not new_items:
            break
        time.sleep(0.2)
    return items[:max_items], includes, errors


def index_by(items: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(item.get(key)): item for item in items if item.get(key)}


def normalize_tweets(raw: list[dict[str, Any]], includes: dict[str, Any], source_kind: str) -> list[dict[str, Any]]:
    users = index_by(includes.get("users", []), "id")
    media = index_by(includes.get("media", []), "media_key")
    tweets = index_by(includes.get("tweets", []), "id")
    out: list[dict[str, Any]] = []
    for tweet in raw:
        author = users.get(str(tweet.get("author_id"))) or {}
        username = str(author.get("username") or "")
        tweet_id = str(tweet.get("id") or "")
        url = f"https://x.com/{username}/status/{tweet_id}" if username and tweet_id else ""
        entities = tweet.get("entities") if isinstance(tweet.get("entities"), dict) else {}
        external_links = []
        for link in entities.get("urls") or []:
            if not isinstance(link, dict):
                continue
            expanded = str(link.get("expanded_url") or link.get("url") or "")
            if expanded:
                external_links.append({"url": expanded, "label": str(link.get("title") or link.get("display_url") or "")})
        media_items = []
        attachments = tweet.get("attachments") if isinstance(tweet.get("attachments"), dict) else {}
        for key in attachments.get("media_keys") or []:
            item = media.get(str(key))
            if not item:
                continue
            url_value = item.get("url") or item.get("preview_image_url") or ""
            if url_value:
                media_items.append({"type": str(item.get("type") or "media"), "url": str(url_value), "alt": str(item.get("alt_text") or "")})
        cards = []
        for ref in tweet.get("referenced_tweets") or []:
            if not isinstance(ref, dict):
                continue
            ref_tweet = tweets.get(str(ref.get("id"))) or {}
            ref_author = users.get(str(ref_tweet.get("author_id"))) or {}
            ref_username = str(ref_author.get("username") or "")
            ref_id = str(ref.get("id") or "")
            if ref_username and ref_id:
                cards.append({"url": f"https://x.com/{ref_username}/status/{ref_id}", "text": str(ref_tweet.get("text") or ref.get("type") or "")[:500]})
        text = str(tweet.get("text") or "")
        metrics = tweet.get("public_metrics") if isinstance(tweet.get("public_metrics"), dict) else {}
        out.append(
            {
                "api_source": source_kind,
                "id": tweet_id,
                "conversation_id": str(tweet.get("conversation_id") or ""),
                "author_username": username,
                "text": text,
                "metrics": metrics,
                "url": url,
                "links": [link.get("url") for link in external_links],
                "externalLinks": external_links,
                "media": media_items,
                "cards": cards,
                "time": tweet.get("created_at"),
                "authorUrl": f"https://x.com/{username}" if username else "",
                "referenced_tweets": [
                    {"id": str(ref.get("id") or ""), "type": str(ref.get("type") or "")}
                    for ref in (tweet.get("referenced_tweets") or [])
                    if isinstance(ref, dict)
                ],
            }
        )
    return out


def parse_time(value: Any) -> Optional[dt.datetime]:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def normalize_dm_asset_links(event: dict[str, Any]) -> list[dict[str, str]]:
    entities = event.get("entities") if isinstance(event.get("entities"), dict) else {}
    links = []
    for link in entities.get("urls") or []:
        if not isinstance(link, dict):
            continue
        url = str(link.get("expanded_url") or link.get("url") or "")
        if url:
            links.append({"url": url, "label": str(link.get("title") or link.get("display_url") or "")})
    return links


def normalize_dm_events(raw: list[dict[str, Any]], includes: dict[str, Any], current_user_id: str, max_threads: int = 50) -> dict[str, Any]:
    users = index_by(includes.get("users", []), "id")
    media = index_by(includes.get("media", []), "media_key")
    tweets = index_by(includes.get("tweets", []), "id")
    conversations: dict[str, list[dict[str, Any]]] = {}
    for event in raw:
        if not isinstance(event, dict):
            continue
        if str(event.get("event_type") or "").lower() not in {"message_create", "messagecreate", ""}:
            continue
        conversation_id = str(event.get("dm_conversation_id") or event.get("conversation_id") or event.get("id") or "")
        if not conversation_id:
            continue
        conversations.setdefault(conversation_id, []).append(event)

    thread_rows: list[dict[str, Any]] = []
    for conversation_id, events in conversations.items():
        events.sort(key=lambda item: str(item.get("created_at") or ""))
        latest = events[-1] if events else {}
        participant_ids: set[str] = set()
        for event in events:
            sender_id = str(event.get("sender_id") or "")
            if sender_id:
                participant_ids.add(sender_id)
            for participant_id in event.get("participant_ids") or []:
                participant_ids.add(str(participant_id))
        other_ids = [pid for pid in participant_ids if pid and pid != current_user_id]
        participant_names = []
        for pid in other_ids:
            user = users.get(pid) or {}
            username = str(user.get("username") or "")
            name = str(user.get("name") or "")
            participant_names.append(f"@{username}" if username else name or pid)
        participant = ", ".join(participant_names) or conversation_id
        replied = str(latest.get("sender_id") or "") == current_user_id
        messages = []
        for event in events:
            sender = "me" if str(event.get("sender_id") or "") == current_user_id else "other"
            text = str(event.get("text") or "")
            media_items = []
            attachments = event.get("attachments") if isinstance(event.get("attachments"), dict) else {}
            for key in attachments.get("media_keys") or []:
                item = media.get(str(key))
                if not item:
                    continue
                url = item.get("url") or item.get("preview_image_url") or ""
                if url:
                    media_items.append({"type": str(item.get("type") or "media"), "url": str(url), "alt": str(item.get("alt_text") or "")})
            links = normalize_dm_asset_links(event)
            cards = []
            for ref in event.get("referenced_tweets") or []:
                if not isinstance(ref, dict):
                    continue
                tweet = tweets.get(str(ref.get("id"))) or {}
                cards.append({"url": f"https://x.com/i/web/status/{ref.get('id')}", "text": str(tweet.get("text") or "")[:500]})
            messages.append({"sender": sender, "time": str(event.get("created_at") or ""), "text": text, "links": links + cards, "media": media_items})
        thread_text = "\n".join(f"{message['sender']} {message.get('time') or ''}: {message.get('text') or ''}" for message in messages)
        thread_rows.append(
            {
                "participant": participant,
                "label": participant,
                "url": f"https://x.com/messages/{conversation_id}",
                "replied": replied,
                "message_count": len(messages),
                "text": thread_text,
                "messages": messages,
                "dm_load_complete": True,
                "dm_scrolls_used": 0,
                "dm_window_exceeded": False,
                "dm_hit_message_cap": False,
                "latest_time": str(latest.get("created_at") or ""),
            }
        )

    thread_rows.sort(key=lambda row: str(row.get("latest_time") or ""), reverse=True)
    visible_threads = thread_rows[:max_threads]
    waiting_threads = [thread for thread in visible_threads if not thread.get("replied")]
    replied_threads = [thread for thread in visible_threads if thread.get("replied")]
    return {
        "threads": waiting_threads,
        "visible_count": len(visible_threads),
        "replied_count": len(replied_threads),
        "unreplied_count": len(waiting_threads),
        "captured_messages": sum(int(thread.get("message_count") or 0) for thread in waiting_threads),
    }


def filter_events_by_window(raw: list[dict[str, Any]], hours: int) -> list[dict[str, Any]]:
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=max(1, hours))
    filtered = []
    for event in raw:
        if not isinstance(event, dict):
            continue
        event_time = parse_time(event.get("created_at"))
        if event_time and event_time >= cutoff:
            filtered.append(event)
    return filtered


def page(kind: str, url: str, items: list[dict[str, Any]], note: str = "", error: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {"kind": kind, "url": url, "items": items}
    if note:
        result["api_note"] = note
    if error:
        result["collection_status"] = "error"
        result["collection_error"] = error
    return result


def collect_api(args: argparse.Namespace) -> dict[str, Any]:
    if not args.bearer_token:
        raise SystemExit("X API is not configured. Configure OAuth2 PKCE or set an OAuth2 user access token with X_BEARER_TOKEN.")
    user = resolve_user(args, args.handle, args.user_id)
    handle = user.get("username") or (args.handle or "").lstrip("@")
    user_id = user.get("id") or args.user_id
    max_items = max(1, int(args.max_public_items))
    hours = max(1, int(args.public_window_hours))
    pages: list[dict[str, Any]] = []

    mentions_raw, mentions_includes, mentions_errors = collect_paginated(
        args,
        f"/users/{user_id}/mentions",
        tweet_params(max_items, hours),
        max_items,
    )
    pages.append(page("mentions_notifications", f"{args.api_base}/users/{user_id}/mentions", normalize_tweets(mentions_raw, mentions_includes, "mentions"), error="; ".join(mentions_errors)))

    tweets_raw, tweets_includes, tweets_errors = collect_paginated(
        args,
        f"/users/{user_id}/tweets",
        tweet_params(max_items, hours),
        max_items,
    )
    pages.append(page("own_profile", f"{args.api_base}/users/{user_id}/tweets", normalize_tweets(tweets_raw, tweets_includes, "own_profile"), error="; ".join(tweets_errors)))

    search_query = f"@{handle} -from:{handle}" if handle else ""
    if search_query:
        search_raw, search_includes, search_errors = collect_paginated(
            args,
            "/tweets/search/recent",
            {**tweet_params(max_items, hours), "query": search_query},
            max_items,
            page_token_name="next_token",
        )
        pages.append(page("mentions_search", f"{args.api_base}/tweets/search/recent?q={urllib.parse.quote(search_query)}", normalize_tweets(search_raw, search_includes, "mentions_search"), error="; ".join(search_errors)))
    else:
        pages.append(page("mentions_search", "", [], note="Skipped because handle was unavailable."))

    home_raw, home_includes, home_errors = collect_paginated(
        args,
        f"/users/{user_id}/timelines/reverse_chronological",
        tweet_params(max_items, hours),
        max_items,
    )
    home_items = normalize_tweets(home_raw, home_includes, "home")
    home_note = "Home timeline API requires user-context access for the authenticated user."
    pages.insert(
        0,
        page(
            "home",
            f"{args.api_base}/users/{user_id}/timelines/reverse_chronological",
            home_items,
            note=home_note,
            error="; ".join(home_errors),
        ),
    )

    for index, keyword in enumerate([k.strip() for k in args.keywords.split(",") if k.strip()], start=1):
        raw, includes, errors = collect_paginated(
            args,
            "/tweets/search/recent",
            {**tweet_params(max_items, hours), "query": keyword},
            max_items,
            page_token_name="next_token",
        )
        pages.append(page(f"keyword_{index}", f"{args.api_base}/tweets/search/recent?q={urllib.parse.quote(keyword)}", normalize_tweets(raw, includes, f"keyword_{index}"), error="; ".join(errors)))

    if args.include_dms:
        dm_raw, dm_includes, dm_errors = collect_paginated(
            args,
            "/dm_events",
            dm_params(max(10, int(args.dm_max_events)), hours),
            max(1, int(args.dm_max_events)),
        )
        dm_window_raw = filter_events_by_window(dm_raw, hours)
        dm_summary = normalize_dm_events(dm_window_raw, dm_includes, user_id, max_threads=50)
        if dm_errors:
            dm_status = "api_dm_todo"
            dm_note = "TODO: X API DM lookup failed. Do not treat this as an empty inbox; use browser DM collection if DM coverage is required."
            dm_todo_detail = "API DM request failed; check OAuth2 dm.read scope, Project/API access, rate limits, or use browser DM collection."
        elif dm_summary["visible_count"] == 0:
            dm_status = "api_dm_todo"
            dm_note = "TODO: X API returned 0 DM events in the digest window. XChat/encrypted messages may not be exposed through DM Events API; use browser DM collection if DM coverage is required."
            dm_todo_detail = "API DM returned 0 events; verify with browser X Chat before saying there are no DMs."
        elif dm_summary["unreplied_count"] == 0:
            dm_status = "api_dm_todo"
            dm_note = "TODO: X API returned DM events but no waiting-reply conversation. Browser X Chat should be checked before concluding no DM action is needed."
            dm_todo_detail = "API DM has events but no waiting-reply thread; browser DM collection remains authoritative for XChat/encrypted conversations."
        else:
            dm_status = "captured_unreplied_threads"
            dm_note = "X API DM lookup captured recent waiting-reply conversations. API events are limited by X API retention, permissions, and rate limits."
            dm_todo_detail = ""
        messages_page = {
            "kind": "messages",
            "url": f"{args.api_base}/dm_events",
            "items": [],
            "dm_status": dm_status,
            "dm_note": dm_note,
            "dm_threads": dm_summary["threads"],
            "dm_visible_thread_count": dm_summary["visible_count"],
            "dm_replied_thread_count": dm_summary["replied_count"],
            "dm_unreplied_thread_count": dm_summary["unreplied_count"],
            "dm_captured_message_count": dm_summary["captured_messages"],
        }
        if dm_todo_detail:
            messages_page["todo_items"] = [
                {
                    "source": "messages",
                    "status": dm_status,
                    "detail": dm_todo_detail,
                }
            ]
        if dm_errors:
            messages_page["collection_status"] = "error"
            messages_page["collection_error"] = "; ".join(dm_errors)
        pages.append(messages_page)

    return {
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "source": "api",
        "auth_method": "oauth2_user_context",
        "api_base": args.api_base,
        "profile_dir": "",
        "handle": handle,
        "user_id": user_id,
        "keywords": [k.strip() for k in args.keywords.split(",") if k.strip()],
        "pages": pages,
    }


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out).expanduser().resolve()
    try:
        data = collect_api(args)
    except Exception as exc:
        print(json.dumps({"source": "api", "collection_status": "error", "error": str(exc)[:1200]}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1) from exc
    write_digest_output(out_dir, data)
    print(json.dumps({"out_dir": str(out_dir), "source": "api", "pages": len(data["pages"])}, indent=2))


if __name__ == "__main__":
    main()
