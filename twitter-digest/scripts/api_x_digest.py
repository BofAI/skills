#!/usr/bin/env python3
"""Collect X/Twitter digest input through the official API when configured."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from browser_x_digest import write_digest_output


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
    parser.add_argument("--max-public-items", type=int, default=300)
    parser.add_argument("--public-window-hours", type=int, default=24)
    parser.add_argument("--scrolls", type=int, default=0, help=argparse.SUPPRESS)
    return parser.parse_args()


def api_is_configured() -> bool:
    return bool(os.environ.get("X_BEARER_TOKEN") or os.environ.get("TWITTER_BEARER_TOKEN"))


def api_get(base_url: str, token: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None and v != ""})
    url = base_url.rstrip("/") + path
    if query:
        url += "?" + query
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": "twitter-digest/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GET {path} failed with HTTP {exc.code}: {body[:1000]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GET {path} failed: {exc}") from exc


def resolve_user(base_url: str, token: str, handle: str | None, user_id: str | None) -> dict[str, str]:
    if user_id:
        result = api_get(base_url, token, f"/users/{user_id}", {"user.fields": "username,name"})
        data = result.get("data") if isinstance(result, dict) else None
        if isinstance(data, dict):
            return {"id": str(data.get("id") or user_id), "username": str(data.get("username") or handle or ""), "name": str(data.get("name") or "")}
    if handle:
        clean = handle.lstrip("@")
        result = api_get(base_url, token, f"/users/by/username/{urllib.parse.quote(clean)}", {"user.fields": "username,name"})
        data = result.get("data") if isinstance(result, dict) else None
        if isinstance(data, dict):
            return {"id": str(data.get("id") or ""), "username": str(data.get("username") or clean), "name": str(data.get("name") or "")}
    result = api_get(base_url, token, "/users/me", {"user.fields": "username,name"})
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


def collect_paginated(
    base_url: str,
    token: str,
    path: str,
    params: dict[str, Any],
    max_items: int,
    page_token_name: str = "pagination_token",
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    items: list[dict[str, Any]] = []
    includes: dict[str, Any] = {"users": [], "media": [], "tweets": []}
    errors: list[str] = []
    next_token = ""
    while len(items) < max_items:
        page_params = dict(params)
        if next_token:
            page_params[page_token_name] = next_token
        try:
            result = api_get(base_url, token, path, page_params)
        except RuntimeError as exc:
            errors.append(str(exc))
            break
        data = result.get("data") if isinstance(result, dict) else None
        if isinstance(data, list):
            items.extend([item for item in data if isinstance(item, dict)])
        inc = result.get("includes") if isinstance(result, dict) else None
        if isinstance(inc, dict):
            for key in includes:
                value = inc.get(key)
                if isinstance(value, list):
                    includes[key].extend(item for item in value if isinstance(item, dict))
        meta = result.get("meta") if isinstance(result, dict) else {}
        next_token = str(meta.get("next_token") or "") if isinstance(meta, dict) else ""
        if not next_token or not data:
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
        if metrics:
            text += " " + " ".join(f"{key}={value}" for key, value in metrics.items())
        out.append(
            {
                "api_source": source_kind,
                "text": text,
                "url": url,
                "links": [link.get("url") for link in external_links],
                "externalLinks": external_links,
                "media": media_items,
                "cards": cards,
                "time": tweet.get("created_at"),
                "authorUrl": f"https://x.com/{username}" if username else "",
            }
        )
    return out


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
        raise SystemExit("X API is not configured. Set X_BEARER_TOKEN or TWITTER_BEARER_TOKEN.")
    user = resolve_user(args.api_base, args.bearer_token, args.handle, args.user_id)
    handle = user.get("username") or (args.handle or "").lstrip("@")
    user_id = user.get("id") or args.user_id
    max_items = max(1, int(args.max_public_items))
    hours = max(1, int(args.public_window_hours))
    pages: list[dict[str, Any]] = []

    mentions_raw, mentions_includes, mentions_errors = collect_paginated(
        args.api_base,
        args.bearer_token,
        f"/users/{user_id}/mentions",
        tweet_params(max_items, hours),
        max_items,
    )
    pages.append(page("mentions_notifications", f"{args.api_base}/users/{user_id}/mentions", normalize_tweets(mentions_raw, mentions_includes, "mentions"), error="; ".join(mentions_errors)))

    tweets_raw, tweets_includes, tweets_errors = collect_paginated(
        args.api_base,
        args.bearer_token,
        f"/users/{user_id}/tweets",
        tweet_params(max_items, hours),
        max_items,
    )
    pages.append(page("own_profile", f"{args.api_base}/users/{user_id}/tweets", normalize_tweets(tweets_raw, tweets_includes, "own_profile"), error="; ".join(tweets_errors)))

    search_query = f"@{handle} -from:{handle}" if handle else ""
    if search_query:
        search_raw, search_includes, search_errors = collect_paginated(
            args.api_base,
            args.bearer_token,
            "/tweets/search/recent",
            {**tweet_params(max_items, hours), "query": search_query},
            max_items,
        )
        pages.append(page("mentions_search", f"{args.api_base}/tweets/search/recent?q={urllib.parse.quote(search_query)}", normalize_tweets(search_raw, search_includes, "mentions_search"), error="; ".join(search_errors)))
    else:
        pages.append(page("mentions_search", "", [], note="Skipped because handle was unavailable."))

    home_raw, home_includes, home_errors = collect_paginated(
        args.api_base,
        args.bearer_token,
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
            args.api_base,
            args.bearer_token,
            "/tweets/search/recent",
            {**tweet_params(max_items, hours), "query": keyword},
            max_items,
        )
        pages.append(page(f"keyword_{index}", f"{args.api_base}/tweets/search/recent?q={urllib.parse.quote(keyword)}", normalize_tweets(raw, includes, f"keyword_{index}"), error="; ".join(errors)))

    if args.include_dms:
        pages.append(
            {
                "kind": "messages",
                "url": "api://messages",
                "items": [],
                "dm_status": "api_dm_unavailable",
                "dm_note": "DM collection through API is not configured in this script. Use browser source for X Chat.",
                "dm_threads": [],
                "dm_visible_thread_count": 0,
                "dm_replied_thread_count": 0,
                "dm_unreplied_thread_count": 0,
                "dm_captured_message_count": 0,
            }
        )

    return {
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "source": "api",
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
    data = collect_api(args)
    write_digest_output(out_dir, data)
    print(json.dumps({"out_dir": str(out_dir), "source": "api", "pages": len(data["pages"])}, indent=2))


if __name__ == "__main__":
    main()
