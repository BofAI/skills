#!/usr/bin/env python3
"""Parse an official X/Twitter archive into briefing-ready JSON and Markdown."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any


ASSIGNMENT_RE = re.compile(r"^\s*window\.YTD\.[^=]+=\s*", re.S)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="Path to an X archive .zip or extracted archive directory")
    parser.add_argument("--days", type=int, default=1, help="Number of recent days to include")
    parser.add_argument("--since", help="Start date/time, e.g. 2026-06-25 or 2026-06-25T00:00:00")
    parser.add_argument("--out", default="x-briefing-output", help="Output directory")
    return parser.parse_args()


def parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    value = value.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = dt.datetime.strptime(value, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return parsed.astimezone(dt.timezone.utc)
        except ValueError:
            pass
    raise SystemExit(f"Could not parse date/time: {value}")


def parse_x_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    value = value.strip()
    for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return dt.datetime.strptime(value, fmt).astimezone(dt.timezone.utc)
        except ValueError:
            pass
    return parse_time(value)


def load_archive_root(path: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if path.is_dir():
        return path, None
    if not zipfile.is_zipfile(path):
        raise SystemExit(f"Not a directory or zip file: {path}")
    tmp = tempfile.TemporaryDirectory(prefix="x-archive.")
    with zipfile.ZipFile(path) as zf:
        zf.extractall(tmp.name)
    return Path(tmp.name), tmp


def read_ytd_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    text = ASSIGNMENT_RE.sub("", text, count=1).strip()
    if text.endswith(";"):
        text = text[:-1]
    return json.loads(text)


def find_data_files(root: Path, patterns: list[str]) -> list[Path]:
    files: set[Path] = set()
    for data_dir in [root / "data", *root.glob("*/data")]:
        if data_dir.is_dir():
            for pattern in patterns:
                files.update(data_dir.glob(pattern))
    return sorted(files)


def within_window(created_at: str | None, since: dt.datetime) -> bool:
    parsed = parse_x_time(created_at)
    return bool(parsed and parsed >= since)


def collect_tweets(root: Path, since: dt.datetime) -> list[dict[str, Any]]:
    tweets: list[dict[str, Any]] = []
    for path in find_data_files(root, ["tweets*.js", "tweet*.js"]):
        for row in read_ytd_json(path):
            tweet = row.get("tweet", row) if isinstance(row, dict) else {}
            if not isinstance(tweet, dict):
                continue
            if not within_window(tweet.get("created_at"), since):
                continue
            tweets.append(
                {
                    "id": tweet.get("id_str") or tweet.get("id"),
                    "created_at": tweet.get("created_at"),
                    "text": tweet.get("full_text") or tweet.get("text", ""),
                    "favorite_count": safe_int(tweet.get("favorite_count")),
                    "retweet_count": safe_int(tweet.get("retweet_count")),
                    "reply_to": tweet.get("in_reply_to_screen_name"),
                }
            )
    return sorted(tweets, key=lambda x: x.get("created_at") or "", reverse=True)


def collect_dms(root: Path, since: dt.datetime) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for path in find_data_files(root, ["direct-message*.js", "direct_messages*.js", "direct-messages*.js"]):
        for row in read_ytd_json(path):
            conversation = row.get("dmConversation", row) if isinstance(row, dict) else {}
            if not isinstance(conversation, dict):
                continue
            conversation_id = conversation.get("conversationId")
            for msg_row in conversation.get("messages", []):
                msg = msg_row.get("messageCreate", msg_row) if isinstance(msg_row, dict) else {}
                if not isinstance(msg, dict):
                    continue
                created_at = millis_to_iso(msg.get("createdAt"))
                if not within_window(created_at, since):
                    continue
                messages.append(
                    {
                        "conversation_id": conversation_id,
                        "created_at": created_at,
                        "sender_id": msg.get("senderId"),
                        "recipient_id": msg.get("recipientId"),
                        "text": msg.get("text", ""),
                    }
                )
    return sorted(messages, key=lambda x: x.get("created_at") or "", reverse=True)


def safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def millis_to_iso(value: Any) -> str | None:
    if value is None:
        return None
    try:
        timestamp = int(value) / 1000
    except (TypeError, ValueError):
        return str(value)
    return dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc).isoformat()


def render_markdown(data: dict[str, Any]) -> str:
    lines = [
        f"# X Archive Briefing Input",
        "",
        f"- Window start: `{data['window']['since']}`",
        f"- Source: `{data['source']}`",
        f"- Own posts found: `{len(data['own_posts'])}`",
        f"- DM messages found: `{len(data['direct_messages'])}`",
        "",
        "## Own Posts",
    ]
    for tweet in data["own_posts"][:50]:
        lines.extend(
            [
                "",
                f"- `{tweet.get('created_at')}` id `{tweet.get('id')}`",
                f"  {one_line(tweet.get('text', ''))}",
            ]
        )
    lines.extend(["", "## Direct Messages"])
    for msg in data["direct_messages"][:100]:
        lines.extend(
            [
                "",
                f"- `{msg.get('created_at')}` conversation `{msg.get('conversation_id')}` sender `{msg.get('sender_id')}`",
                f"  {one_line(msg.get('text', ''))}",
            ]
        )
    lines.extend(
        [
            "",
            "## Data Gaps",
            "",
            "- Official archives are snapshots, not live monitoring.",
            "- Use a live MCP/search connector for public mentions and hotspots.",
            "- Use this archive output for DMs and historical own-account context.",
        ]
    )
    return "\n".join(lines) + "\n"


def one_line(text: str) -> str:
    return " ".join(str(text).split())


def main() -> None:
    args = parse_args()
    archive_path = Path(args.archive).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    now = dt.datetime.now(dt.timezone.utc)
    since = parse_time(args.since) if args.since else now - dt.timedelta(days=args.days)
    root, tmp = load_archive_root(archive_path)
    try:
        data = {
            "source": str(archive_path),
            "window": {"since": since.isoformat(), "generated_at": now.isoformat()},
            "own_posts": collect_tweets(root, since),
            "direct_messages": collect_dms(root, since),
        }
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "briefing-input.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        (out_dir / "briefing-input.md").write_text(render_markdown(data), encoding="utf-8")
        print(json.dumps({"out_dir": str(out_dir), "own_posts": len(data["own_posts"]), "direct_messages": len(data["direct_messages"])}, indent=2))
    finally:
        if tmp is not None:
            tmp.cleanup()


if __name__ == "__main__":
    main()
