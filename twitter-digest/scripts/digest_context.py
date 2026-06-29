#!/usr/bin/env python3
"""Build current-run X/Twitter digest context without long-term memory."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to digest-input.json.")
    parser.add_argument("--markdown", help="Path to rewrite digest-input.md.")
    parser.add_argument("--out-dir", required=True, help="Directory for digest-context output files.")
    return parser.parse_args()


def build_current_context_from_file(input_path: Path, out_dir: Path, markdown_path: Path | None = None) -> dict[str, Any]:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        out_dir.chmod(0o700)
    except PermissionError:
        pass

    summary = summarize_current_run(data)
    input_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if markdown_path:
        markdown_path.write_text(render_digest_input(data), encoding="utf-8")

    facts = build_digest_facts(data, summary)
    context_json = {"summary": summary, "facts": facts, "memory": "disabled"}
    (out_dir / "digest-context.md").write_text(render_digest_context(summary, facts), encoding="utf-8")
    (out_dir / "digest-context.json").write_text(json.dumps(context_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return context_json


def summarize_current_run(data: dict[str, Any]) -> dict[str, Any]:
    generated_at = str(data.get("generated_at") or now_iso())
    post_counts: dict[str, dict[str, int]] = {}
    dm_status = "not_requested"
    dm_counts = {"visible": 0, "last_from_me": 0, "waiting_reply": 0, "captured_messages": 0}

    for page in data.get("pages", []):
        if not isinstance(page, dict):
            continue
        kind = str(page.get("kind") or "unknown")
        items = page.get("items") if isinstance(page.get("items"), list) else []
        post_counts[kind] = {"total": len(items)}
        if kind == "messages":
            dm_status = str(page.get("dm_status") or "unknown")
            dm_counts = {
                "visible": int(page.get("dm_visible_thread_count") or 0),
                "last_from_me": int(page.get("dm_replied_thread_count") or 0),
                "waiting_reply": int(page.get("dm_unreplied_thread_count") or 0),
                "captured_messages": int(page.get("dm_captured_message_count") or 0),
            }

    return {
        "generated_at": generated_at,
        "date": generated_at[:10],
        "source": str(data.get("source") or "browser"),
        "handle": clean_handle(data.get("handle")),
        "post_counts": post_counts,
        "dm_status": dm_status,
        "dm_counts": dm_counts,
        "context_policy": "No long-term memory. Final summary uses only this run's current collector capture.",
    }


def build_digest_facts(data: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "schema_version": 1,
        "run": {
            "generated_at": data.get("generated_at"),
            "date": summary.get("date"),
            "source": summary.get("source"),
            "timezone": local_timezone_name(),
        },
        "account": {
            "handle": summary.get("handle") or clean_handle(data.get("handle")),
            "profile_dir": data.get("profile_dir"),
        },
        "summary_inputs": {
            "primary": "digest-context.md#Final Summary Facts",
            "raw_capture_for_debug_only": "digest-input.md",
            "rules": [
                "Use only this run's digest context as content.",
                "Do not use historical memory or older runs.",
                "Use DM conversation counts and message counts as separate units.",
                "Only threads whose latest preview is not from the user are opened for content.",
                "Do not treat embedded post authors as DM senders.",
                "Count low-value waiting-reply DMs but do not expand spam, phishing, generic promotions, or repeated junk.",
            ],
        },
        "public": {"counts": summary.get("post_counts") or {}, "items": []},
        "dms": {
            "status": summary.get("dm_status"),
            "counts": summary.get("dm_counts") or {},
            "threads": [],
        },
        "todo_items": [],
        "data_gaps": [],
    }

    for page in data.get("pages", []):
        if not isinstance(page, dict):
            continue
        kind = str(page.get("kind") or "unknown")
        if page.get("collection_error"):
            facts["data_gaps"].append(
                {
                    "source": kind,
                    "status": page.get("collection_status") or "error",
                    "detail": str(page.get("collection_error") or ""),
                }
            )
        if kind == "messages":
            if page.get("dm_note"):
                facts["dms"]["note"] = str(page.get("dm_note") or "")
            for todo in page.get("todo_items") or []:
                if isinstance(todo, dict):
                    facts["todo_items"].append(
                        {
                            "source": str(todo.get("source") or kind),
                            "status": str(todo.get("status") or page.get("dm_status") or "todo"),
                            "detail": str(todo.get("detail") or page.get("dm_note") or ""),
                        }
                    )
            for thread in page.get("dm_threads") or []:
                if not isinstance(thread, dict):
                    continue
                assessment = assess_dm_thread(thread)
                facts["dms"]["threads"].append(
                    {
                        "participant": thread.get("participant") or thread.get("label") or thread.get("url") or "",
                        "url": thread.get("url") or "",
                        "label": thread.get("label") or "",
                        "reply_state": "last_from_me" if thread.get("replied") else "waiting_reply",
                        "message_count": int(thread.get("message_count") or 0),
                        "should_summarize": assessment["should_summarize"],
                        "noise_reason": assessment["noise_reason"],
                        "text_excerpt": compact_text(thread.get("text"))[:1200],
                        "messages": normalize_dm_messages(thread.get("messages"))[-2000:],
                        "conversation_context": dm_conversation_context(thread),
                        "load": {
                            "scrolls_used": int(thread.get("dm_scrolls_used") or 0),
                            "load_complete": bool(thread.get("dm_load_complete")),
                            "window_exceeded": bool(thread.get("dm_window_exceeded")),
                            "hit_message_cap": bool(thread.get("dm_hit_message_cap")),
                        },
                    }
                )
                if not bool(thread.get("dm_load_complete")):
                    facts["data_gaps"].append(
                        {
                            "source": "messages",
                            "status": "dm_thread_incomplete",
                            "detail": (
                                f"DM thread {thread.get('participant') or thread.get('label') or thread.get('url') or '[unknown]'} "
                                "may not be fully loaded. "
                                f"scrolls_used={int(thread.get('dm_scrolls_used') or 0)}, "
                                f"hit_message_cap={bool(thread.get('dm_hit_message_cap'))}, "
                                f"window_exceeded={bool(thread.get('dm_window_exceeded'))}."
                            ),
                        }
                    )
            continue
        for item in page.get("items") or []:
            if not isinstance(item, dict):
                continue
            facts["public"]["items"].append(
                {
                    "kind": kind,
                    "time": item.get("time") or "",
                    "url": item.get("url") or "",
                    "author_url": item.get("authorUrl") or "",
                    "text_excerpt": compact_text(item.get("text"))[:700],
                    "external_links": normalize_context_assets(item.get("externalLinks")),
                    "media": normalize_context_assets(item.get("media")),
                    "cards": normalize_context_assets(item.get("cards")),
                }
            )
    if (summary.get("dm_status") or "") in {"blocked_by_x_chat_passcode", "visible_threads_unopened", "no_visible_threads", "api_dm_unavailable", "api_dm_error", "api_dm_todo"}:
        facts["data_gaps"].append(
            {
                "source": "messages",
                "status": summary.get("dm_status"),
                "detail": facts["dms"].get("note") or "DM content was incomplete or unavailable.",
            }
        )
    if (summary.get("dm_status") or "") == "api_dm_todo" and not facts["todo_items"]:
        facts["todo_items"].append(
            {
                "source": "messages",
                "status": "api_dm_todo",
                "detail": facts["dms"].get("note") or "API DM was inconclusive; use browser DM collection before making a final DM claim.",
            }
        )
    return facts


def assess_dm_thread(thread: dict[str, Any]) -> dict[str, Any]:
    text = compact_text(thread.get("text") or thread.get("label")).lower()
    if not text:
        return {"should_summarize": False, "noise_reason": "empty_thread_text"}
    if bool(thread.get("replied")):
        return {"should_summarize": False, "noise_reason": "last_message_from_me"}
    spam_patterns = [
        r"airdrop",
        r"giveaway",
        r"claim",
        r"free\s+(token|mint|nft|crypto)",
        r"private key",
        r"seed phrase",
        r"wallet",
        r"telegram|whatsapp",
        r"follow-up visit",
    ]
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in spam_patterns):
        return {"should_summarize": False, "noise_reason": "spam_or_suspicious_link"}
    if re.search(r"(t\.co|bit\.ly)/\S+", text, re.IGNORECASE) and len(text) < 180:
        return {"should_summarize": False, "noise_reason": "low_context_link"}
    return {"should_summarize": True, "noise_reason": ""}


def normalize_dm_messages(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    messages: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        text = compact_text(item.get("text"))
        if not text:
            continue
        messages.append(
            {
                "sender": "me" if item.get("sender") == "me" else "other",
                "time": compact_text(item.get("time")),
                "text": text[:1000],
                "links": normalize_context_assets(item.get("links")),
                "media": normalize_context_assets(item.get("media")),
            }
        )
    return messages


def dm_conversation_context(thread: dict[str, Any], max_messages: int = 2000, max_chars: int = 120000) -> str:
    messages = normalize_dm_messages(thread.get("messages"))[-max_messages:]
    if messages:
        lines = []
        for message in messages:
            timestamp = f" {message['time']}" if message.get("time") else ""
            lines.append(f"{message['sender']}{timestamp}: {message['text']}")
            for link in message.get("links") or []:
                label = f" {link.get('label')}" if link.get("label") else ""
                lines.append(f"  link: {link.get('url')}{label}")
            for media in message.get("media") or []:
                alt = f" alt={media.get('alt')}" if media.get("alt") else ""
                poster = f" poster={media.get('poster')}" if media.get("poster") else ""
                lines.append(f"  media: {media.get('type') or 'media'} {media.get('url')}{poster}{alt}".rstrip())
        return "\n".join(lines)[-max_chars:]
    return str(thread.get("text") or "")[-max_chars:]


def normalize_context_assets(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        url = compact_text(item.get("url"))
        if not url:
            continue
        asset = {"url": url[:1200]}
        for key in ("label", "type", "alt", "poster", "text"):
            if item.get(key):
                asset[key] = compact_text(item.get(key))[:700]
        out.append(asset)
    return out[:12]


def render_digest_input(data: dict[str, Any]) -> str:
    lines = [
        "# X 浏览器采集输入",
        "",
        f"- 生成时间: `{data.get('generated_at')}`",
        f"- 浏览器 profile: `{data.get('profile_dir')}`",
        f"- 当前账号: `{data.get('handle') or ''}`",
        "",
    ]
    for page in data.get("pages", []):
        if not isinstance(page, dict):
            continue
        lines.extend([f"## {page.get('kind')}", "", f"Source: {page.get('url')}", ""])
        items = page.get("items") if isinstance(page.get("items"), list) else []
        lines.extend([f"采集条数: `{len(items)}`", ""])
        for item in items[:80]:
            if not isinstance(item, dict):
                continue
            lines.append(f"- [current] `{item.get('time') or ''}` {item.get('url') or ''}")
            lines.append(f"  {compact_text(item.get('text'))[:1000]}")
        if page.get("visible_text"):
            lines.extend(["", "页面可见文本摘录:", "", str(page["visible_text"])[:3000]])
        if page.get("dm_status"):
            lines.extend(["", f"DM 状态: `{page['dm_status']}`"])
            lines.append(
                "DM 会话统计: "
                f"今日可见 `{int(page.get('dm_visible_thread_count') or 0)}` / "
                f"最后我发出 `{int(page.get('dm_replied_thread_count') or 0)}` / "
                f"等我回复 `{int(page.get('dm_unreplied_thread_count') or 0)}`"
            )
            lines.append(f"DM 消息统计: 已打开等我回复会话中捕获消息气泡 `{int(page.get('dm_captured_message_count') or 0)}`")
            if page.get("dm_note"):
                lines.append(str(page["dm_note"]))
        if page.get("collection_error"):
            lines.extend(["", f"采集错误: `{page['collection_error']}`"])
        for thread in page.get("dm_threads", [])[:20]:
            if not isinstance(thread, dict):
                continue
            participant = thread.get("participant") or thread.get("label") or thread.get("url")
            lines.extend(["", f"### DM thread [current]: {participant}", ""])
            lines.append(f"会话对象: `{participant}`")
            lines.append(f"会话状态: `{'最后我发出' if thread.get('replied') else '等我回复'}`")
            lines.append(f"消息数量: `{int(thread.get('message_count') or 0)}`")
            lines.append("发信人判断: 使用会话对象/消息气泡判断；引用帖、转发卡片或链接预览里的作者不是 DM 发信人。")
            lines.extend(["", str(thread.get("text") or "")[:3000]])
        lines.append("")
    lines.extend(
        [
            "## 数据缺口",
            "",
            "- 浏览器采集依赖 X 页面结构和已加载的可见内容。",
            "- 公开内容标记为 `[current]`，最终日报只依赖本次采集。",
            "- DM 属于私密内容，不写长期 memory 或 daily archive。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_digest_context(summary: dict[str, Any], facts: dict[str, Any]) -> str:
    lines = ["# X Digest Context", "", "## Final Summary Facts", ""]
    lines.extend(render_digest_facts(facts).splitlines()[2:])
    lines.extend(
        [
            "",
            "## Run Metadata",
            "",
            "This section is only for provenance. Do not use historical memory or older runs as content.",
            "",
            f"- date: `{summary.get('date')}`",
            f"- handle: `@{summary.get('handle') or ''}`",
            f"- source: `{summary.get('source') or 'browser'}`",
            f"- context policy: {summary.get('context_policy')}",
            f"- DM status: `{summary.get('dm_status')}`",
            (
                "- DM counts: "
                f"today visible `{(summary.get('dm_counts') or {}).get('visible', 0)}`, "
                f"last_from_me `{(summary.get('dm_counts') or {}).get('last_from_me', 0)}`, "
                f"waiting_reply `{(summary.get('dm_counts') or {}).get('waiting_reply', 0)}`, "
                f"captured messages `{(summary.get('dm_counts') or {}).get('captured_messages', 0)}`"
            ),
            "",
            "### Page Counts",
            "",
            "| page | total |",
            "|---|---:|",
        ]
    )
    for kind, counts in (summary.get("post_counts") or {}).items():
        lines.append(f"| {kind} | {counts.get('total', 0)} |")
    return "\n".join(lines) + "\n"


def render_digest_facts(facts: dict[str, Any]) -> str:
    dms = facts.get("dms") or {}
    dm_counts = dms.get("counts") or {}
    lines = [
        "# X Digest Facts",
        "",
        "Use this section as the only content input for the final Chinese X daily digest. Use raw capture only to verify details.",
        "",
        "## Run",
        "",
        f"- date: `{(facts.get('run') or {}).get('date')}`",
        f"- generated_at: `{(facts.get('run') or {}).get('generated_at')}`",
        f"- source: `{(facts.get('run') or {}).get('source') or 'browser'}`",
        f"- timezone: `{(facts.get('run') or {}).get('timezone')}`",
        f"- account: `@{(facts.get('account') or {}).get('handle') or ''}`",
        "",
        "## DM Facts",
        "",
        f"- status: `{dms.get('status')}`",
        (
            "- counts: "
            f"today visible `{dm_counts.get('visible', 0)}`, "
            f"last_from_me `{dm_counts.get('last_from_me', 0)}`, "
            f"waiting_reply `{dm_counts.get('waiting_reply', 0)}`, "
            f"captured messages `{dm_counts.get('captured_messages', 0)}`"
        ),
        "- rule: summarize only `waiting_reply` threads with `should_summarize: true`; count noise but do not expand it.",
    ]
    if dms.get("note"):
        lines.append(f"- note: {dms.get('note')}")
    lines.extend(["", "| participant | reply_state | messages | summarize | noise_reason | excerpt |", "|---|---|---:|---|---|---|"])
    for thread in dms.get("threads") or []:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(thread.get("participant") or ""),
                    md_cell(thread.get("reply_state") or ""),
                    str(int(thread.get("message_count") or 0)),
                    "yes" if thread.get("should_summarize") else "no",
                    md_cell(thread.get("noise_reason") or ""),
                    md_cell(thread.get("text_excerpt") or ""),
                ]
            )
            + " |"
        )
    if not dms.get("threads"):
        lines.append("| none | - | 0 | no | no_opened_unreplied_threads | |")

    lines.extend(["", "## TODO List", ""])
    for todo in facts.get("todo_items") or []:
        lines.append(f"- `{todo.get('source')}` `{todo.get('status')}`: {todo.get('detail')}")
    if not facts.get("todo_items"):
        lines.append("- None")

    context_threads = [
        thread
        for thread in dms.get("threads") or []
        if thread.get("reply_state") == "waiting_reply" and thread.get("should_summarize") and thread.get("conversation_context")
    ]
    if context_threads:
        lines.extend(
            [
                "",
                "### DM Thread Context",
                "",
                "Use this recent loaded history to understand what the waiting-reply DM is about before drafting the daily digest. Sender is based on message bubble direction; quoted-post authors are not DM senders.",
            ]
        )
        for index, thread in enumerate(context_threads, start=1):
            messages = thread.get("messages") if isinstance(thread.get("messages"), list) else []
            shown_messages = len(messages[-2000:]) if messages else int(thread.get("message_count") or 0)
            load = thread.get("load") if isinstance(thread.get("load"), dict) else {}
            lines.extend(
                [
                    "",
                    f"#### DM {index}: {thread.get('participant') or '[unknown]'}",
                    "",
                    f"- reply_state: `{thread.get('reply_state')}`",
                    f"- raw_label: `{md_inline(thread.get('label') or '')}`",
                    f"- url: `{md_inline(thread.get('url') or '')}`",
                    f"- loaded message bubbles in context: `{shown_messages}` of `{int(thread.get('message_count') or 0)}`",
                    f"- load: scrolls_used `{int(load.get('scrolls_used') or 0)}`, load_complete `{bool(load.get('load_complete'))}`, window_exceeded `{bool(load.get('window_exceeded'))}`, hit_message_cap `{bool(load.get('hit_message_cap'))}`",
                    "",
                    "```text",
                    str(thread.get("conversation_context") or "")[:120000],
                    "```",
                ]
            )

    lines.extend(["", "## Public Counts", "", "| page | total |", "|---|---:|"])
    for kind, counts in ((facts.get("public") or {}).get("counts") or {}).items():
        lines.append(f"| {md_cell(kind)} | {counts.get('total', 0)} |")

    lines.extend(["", "## Public Items", ""])
    for item in ((facts.get("public") or {}).get("items") or [])[:300]:
        lines.append(f"- `{item.get('kind')}` `{item.get('time')}` {item.get('url') or '[no url]'} - {item.get('text_excerpt')}")
        for asset in item.get("media") or []:
            alt = f" alt={asset.get('alt')}" if asset.get("alt") else ""
            poster = f" poster={asset.get('poster')}" if asset.get("poster") else ""
            lines.append(f"  - media: {asset.get('type') or 'media'} {asset.get('url')}{poster}{alt}".rstrip())
        for link in item.get("external_links") or []:
            label = f" {link.get('label')}" if link.get("label") else ""
            lines.append(f"  - link: {link.get('url')}{label}")
        for card in item.get("cards") or []:
            text = f" {card.get('text')}" if card.get("text") else ""
            lines.append(f"  - card: {card.get('url')}{text}")
    if not ((facts.get("public") or {}).get("items") or []):
        lines.append("- None")

    lines.extend(["", "## Data Gaps", ""])
    for gap in facts.get("data_gaps") or []:
        lines.append(f"- `{gap.get('source')}` `{gap.get('status')}`: {gap.get('detail')}")
    if not facts.get("data_gaps"):
        lines.append("- None")
    return "\n".join(lines) + "\n"


def compact_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def md_cell(value: Any) -> str:
    return compact_text(str(value or "").replace("|", "\\|"))[:500]


def md_inline(value: Any) -> str:
    return compact_text(str(value or "").replace("`", "'"))[:1000]


def clean_handle(value: Any) -> str:
    return str(value or "").strip().lstrip("@")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def local_timezone_name() -> str:
    tz = dt.datetime.now().astimezone().tzinfo
    return str(tz) if tz else "local"


def main() -> None:
    args = parse_args()
    result = build_current_context_from_file(
        input_path=Path(args.input).expanduser().resolve(),
        markdown_path=Path(args.markdown).expanduser().resolve() if args.markdown else None,
        out_dir=Path(args.out_dir).expanduser().resolve(),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
