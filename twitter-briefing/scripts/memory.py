#!/usr/bin/env python3
"""Local memory for X/Twitter briefing runs.

Long-term memory intentionally avoids storing raw DM text. The current run's
raw browser capture can stay in /tmp for summarization, while this module keeps
only identifiers, statuses, counts, and short public-post previews.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_MEMORY_DIR = Path.home() / ".twitter-briefing"
MEMORY_FILE = "memory.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    update = subparsers.add_parser("update", help="Update memory from a briefing-input.json file.")
    update.add_argument("--input", required=True, help="Path to briefing-input.json.")
    update.add_argument("--markdown", help="Path to briefing-input.md for daily sanitized archive context.")
    update.add_argument("--out-dir", required=True, help="Directory for memory-context output files.")
    update.add_argument("--memory-dir", default=str(DEFAULT_MEMORY_DIR))
    update.add_argument("--include-dms", action="store_true")
    update.add_argument("--dm-threads", type=int, default=5)
    return parser.parse_args()


def update_from_file(
    input_path: Path,
    out_dir: Path,
    memory_dir: Path = DEFAULT_MEMORY_DIR,
    markdown_path: Path | None = None,
    include_dms: bool = False,
    dm_threads: int = 5,
) -> dict[str, Any]:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    memory_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    memory = load_memory(memory_dir)
    summary = update_memory(memory, data, include_dms=include_dms, dm_threads=dm_threads)
    save_memory(memory_dir, memory)

    sanitized = sanitize_briefing(data)
    archive_daily(memory_dir, sanitized, markdown_path, summary)

    context_md = render_memory_context(summary)
    context_json = {
        "memory_file": str(memory_dir / MEMORY_FILE),
        "daily_dir": str(memory_dir / "daily"),
        "summary": summary,
    }
    (out_dir / "memory-context.md").write_text(context_md, encoding="utf-8")
    (out_dir / "memory-context.json").write_text(json.dumps(context_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return context_json


def load_memory(memory_dir: Path) -> dict[str, Any]:
    path = memory_dir / MEMORY_FILE
    if not path.exists():
        return {
            "version": 1,
            "created_at": now_iso(),
            "updated_at": None,
            "account": {},
            "preferences": {},
            "seen_posts": {},
            "dm_threads": {},
            "runs": [],
        }
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        backup = path.with_suffix(".json.invalid")
        path.replace(backup)
        return load_memory(memory_dir)


def save_memory(memory_dir: Path, memory: dict[str, Any]) -> None:
    memory["updated_at"] = now_iso()
    path = memory_dir / MEMORY_FILE
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(memory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def update_memory(memory: dict[str, Any], data: dict[str, Any], include_dms: bool, dm_threads: int) -> dict[str, Any]:
    generated_at = str(data.get("generated_at") or now_iso())
    run_date = generated_at[:10]
    handle = clean_handle(data.get("handle"))

    memory.setdefault("account", {})
    if handle:
        memory["account"]["handle"] = handle
    if data.get("profile_dir"):
        memory["account"]["profile_dir"] = str(data["profile_dir"])

    memory["preferences"] = {
        **memory.get("preferences", {}),
        "keywords": data.get("keywords") or [],
        "include_dms": bool(include_dms),
        "dm_threads": int(dm_threads),
        "language": "zh-CN",
        "raw_dm_persisted": False,
    }

    seen_posts = memory.setdefault("seen_posts", {})
    dm_memory = memory.setdefault("dm_threads", {})
    post_counts: dict[str, dict[str, int]] = {}
    new_posts: list[dict[str, Any]] = []
    repeated_posts: list[dict[str, Any]] = []
    dm_status = "not_requested"
    dm_thread_updates: list[dict[str, str]] = []

    for page in data.get("pages", []):
        kind = str(page.get("kind") or "unknown")
        items = page.get("items") if isinstance(page.get("items"), list) else []
        post_counts.setdefault(kind, {"total": 0, "new": 0, "repeat": 0})
        post_counts[kind]["total"] += len(items)

        if kind == "messages":
            dm_status = str(page.get("dm_status") or "unknown")
            for thread in page.get("dm_threads") or []:
                if not isinstance(thread, dict):
                    continue
                thread_key = str(thread.get("url") or stable_hash(str(thread.get("label") or "") + str(thread.get("text") or "")))
                text_signature = stable_hash(str(thread.get("text") or ""))
                previous = dm_memory.get(thread_key, {})
                changed = previous.get("last_text_signature") != text_signature
                dm_memory[thread_key] = {
                    "label": str(thread.get("label") or "")[:120],
                    "url": str(thread.get("url") or ""),
                    "first_seen_at": previous.get("first_seen_at") or generated_at,
                    "last_seen_at": generated_at,
                    "last_text_signature": text_signature,
                    "status": "new_or_changed" if changed else "unchanged",
                }
                dm_thread_updates.append(
                    {
                        "label": dm_memory[thread_key]["label"],
                        "url": dm_memory[thread_key]["url"],
                        "status": dm_memory[thread_key]["status"],
                    }
                )
            continue

        for item in items:
            if not isinstance(item, dict):
                continue
            key = post_key(item)
            if not key:
                continue
            text_preview = " ".join(str(item.get("text") or "").split())[:220]
            previous = seen_posts.get(key)
            entry = {
                "url": str(item.get("url") or ""),
                "author_url": str(item.get("authorUrl") or ""),
                "time": str(item.get("time") or ""),
                "first_seen_at": previous.get("first_seen_at") if isinstance(previous, dict) else generated_at,
                "last_seen_at": generated_at,
                "kinds": sorted(set((previous or {}).get("kinds", []) + [kind])) if isinstance(previous, dict) else [kind],
                "text_preview": text_preview,
            }
            if previous:
                post_counts[kind]["repeat"] += 1
                repeated_posts.append({"kind": kind, "url": entry["url"], "text_preview": text_preview})
            else:
                post_counts[kind]["new"] += 1
                new_posts.append({"kind": kind, "url": entry["url"], "text_preview": text_preview})
            seen_posts[key] = entry

    run_record = {
        "date": run_date,
        "generated_at": generated_at,
        "handle": handle,
        "post_counts": post_counts,
        "dm_status": dm_status,
        "new_posts": len(new_posts),
        "repeated_posts": len(repeated_posts),
        "dm_thread_updates": len(dm_thread_updates),
    }
    runs = memory.setdefault("runs", [])
    runs.append(run_record)
    del runs[:-60]

    return {
        "generated_at": generated_at,
        "date": run_date,
        "handle": handle,
        "post_counts": post_counts,
        "new_posts": new_posts[:30],
        "repeated_posts": repeated_posts[:30],
        "dm_status": dm_status,
        "dm_threads": dm_thread_updates,
        "memory_policy": "Long-term memory stores no raw DM text.",
    }


def sanitize_briefing(data: dict[str, Any]) -> dict[str, Any]:
    sanitized = copy.deepcopy(data)
    for page in sanitized.get("pages", []):
        if not isinstance(page, dict) or page.get("kind") != "messages":
            continue
        page.pop("visible_text", None)
        for thread in page.get("dm_threads") or []:
            if isinstance(thread, dict):
                thread["text"] = "[redacted: raw DM text is not persisted in memory]"
        page["privacy_note"] = "Raw DM text redacted from long-term daily archive."
    return sanitized


def archive_daily(memory_dir: Path, sanitized: dict[str, Any], markdown_path: Path | None, summary: dict[str, Any]) -> None:
    daily_dir = memory_dir / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    date = str(summary.get("date") or now_iso()[:10])
    payload = {"summary": summary, "briefing": sanitized}
    (daily_dir / f"{date}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if markdown_path and markdown_path.exists():
        md = markdown_path.read_text(encoding="utf-8")
        redacted_md = redact_messages_section(md)
        (daily_dir / f"{date}.md").write_text(redacted_md, encoding="utf-8")


def render_memory_context(summary: dict[str, Any]) -> str:
    lines = [
        "# X Briefing Memory Context",
        "",
        f"- date: `{summary.get('date')}`",
        f"- handle: `@{summary.get('handle') or ''}`",
        f"- memory policy: {summary.get('memory_policy')}",
        f"- DM status: `{summary.get('dm_status')}`",
        "",
        "## Page Counts",
        "",
        "| page | total | new | repeat |",
        "|---|---:|---:|---:|",
    ]
    for kind, counts in (summary.get("post_counts") or {}).items():
        lines.append(f"| {kind} | {counts.get('total', 0)} | {counts.get('new', 0)} | {counts.get('repeat', 0)} |")

    lines.extend(["", "## New Public Items", ""])
    for item in summary.get("new_posts", [])[:20]:
        lines.append(f"- `{item.get('kind')}` {item.get('url') or '[no url]'} — {item.get('text_preview')}")
    if not summary.get("new_posts"):
        lines.append("- None")

    lines.extend(["", "## DM Thread Memory", ""])
    for thread in summary.get("dm_threads", [])[:20]:
        label = thread.get("label") or thread.get("url") or "[unknown]"
        lines.append(f"- `{thread.get('status')}` {label}")
    if not summary.get("dm_threads"):
        lines.append("- No visible DM threads captured in this run.")
    return "\n".join(lines) + "\n"


def redact_messages_section(markdown: str) -> str:
    marker = "\n## messages\n"
    index = markdown.find(marker)
    if index < 0:
        return markdown
    next_index = markdown.find("\n## ", index + len(marker))
    if next_index < 0:
        next_index = len(markdown)
    replacement = (
        "\n## messages\n\n"
        "Long-term archive redacts raw DM text. Use the current run's /tmp output for one-time summarization.\n\n"
    )
    return markdown[:index] + replacement + markdown[next_index:]


def post_key(item: dict[str, Any]) -> str:
    url = str(item.get("url") or "").strip()
    if url:
        return url
    text = str(item.get("text") or "").strip()
    return stable_hash(text) if text else ""


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def clean_handle(value: Any) -> str:
    return str(value or "").strip().lstrip("@")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def main() -> None:
    args = parse_args()
    if args.command == "update":
        result = update_from_file(
            input_path=Path(args.input).expanduser().resolve(),
            markdown_path=Path(args.markdown).expanduser().resolve() if args.markdown else None,
            out_dir=Path(args.out_dir).expanduser().resolve(),
            memory_dir=Path(args.memory_dir).expanduser().resolve(),
            include_dms=args.include_dms,
            dm_threads=args.dm_threads,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
