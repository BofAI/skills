#!/usr/bin/env python3
"""Inspect current twitter-digest outputs without printing private message bodies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTEXT = ROOT / ".state" / "run" / "digest-context.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", default=str(DEFAULT_CONTEXT), help="Path to digest-context.json.")
    return parser.parse_args()


def safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def public_counts(items: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "unknown")
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def summarize_context(data: dict[str, Any]) -> dict[str, Any]:
    summary = safe_dict(data.get("summary"))
    facts = safe_dict(data.get("facts"))
    public = safe_dict(facts.get("public"))
    dms = safe_dict(facts.get("dms"))
    dm_threads = safe_list(dms.get("threads"))
    data_gaps = safe_list(facts.get("data_gaps"))
    public_items = safe_list(public.get("items"))
    return {
        "run": safe_dict(facts.get("run")),
        "account": safe_dict(facts.get("account")),
        "source": summary.get("source") or safe_dict(facts.get("run")).get("source") or "",
        "public": {
            "counts_from_pages": summary.get("post_counts") or public.get("counts") or {},
            "items_by_kind": public_counts(public_items),
            "item_count": len(public_items),
        },
        "dms": {
            "status": dms.get("status") or summary.get("dm_status") or "",
            "counts": dms.get("counts") or summary.get("dm_counts") or {},
            "thread_count": len(dm_threads),
            "threads_without_body": [
                {
                    "participant": thread.get("participant") or "",
                    "reply_state": thread.get("reply_state") or "",
                    "message_count": thread.get("message_count") or 0,
                    "should_summarize": bool(thread.get("should_summarize")),
                    "noise_reason": thread.get("noise_reason") or "",
                    "load": thread.get("load") or {},
                }
                for thread in dm_threads
                if isinstance(thread, dict)
            ],
        },
        "todo_count": len(safe_list(facts.get("todo_items"))),
        "data_gap_count": len(data_gaps),
        "data_gaps": [
            {
                "source": gap.get("source") or "",
                "status": gap.get("status") or "",
                "detail": gap.get("detail") or "",
            }
            for gap in data_gaps
            if isinstance(gap, dict)
        ],
    }


def main() -> None:
    path = Path(parse_args().context).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"digest context not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"digest context is not a JSON object: {path}")
    print(json.dumps(summarize_context(data), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
