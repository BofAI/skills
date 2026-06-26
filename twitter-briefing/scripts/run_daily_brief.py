#!/usr/bin/env python3
"""Chat-friendly wrapper for collecting X/Twitter daily briefing input."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from memory import DEFAULT_MEMORY_DIR, update_from_file


CONFIG_PATH = Path.home() / ".twitter-briefing" / "config.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handle")
    parser.add_argument("--account-name")
    parser.add_argument("--save-default", action="store_true", help="Save --handle/--account-name as the default account for future chat runs.")
    parser.add_argument("--configure-only", action="store_true", help="Only save default account config; do not collect data.")
    parser.add_argument("--keywords", default="", help="Optional comma-separated search queries. Default is empty; the daily brief focuses on timeline, mentions, and DMs.")
    parser.add_argument("--out", default="/tmp/x-briefing")
    parser.add_argument("--include-dms", action="store_true")
    parser.add_argument("--dm-threads", type=int, default=5)
    parser.add_argument("--scrolls", type=int, default=4)
    parser.add_argument("--memory-dir", default=str(DEFAULT_MEMORY_DIR))
    parser.add_argument("--no-memory", action="store_true", help="Do not update local briefing memory after collection.")
    return parser.parse_args()


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(handle: str | None, account_name: str | None) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    config = load_config()
    if handle:
        config["handle"] = handle.lstrip("@")
    if account_name:
        config["account_name"] = account_name
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.save_default:
        save_config(args.handle, args.account_name)
    if args.configure_only:
        print(json.dumps({"config": str(CONFIG_PATH), "saved": bool(args.save_default)}, ensure_ascii=False, indent=2))
        return
    config = load_config()
    handle = (args.handle or config.get("handle") or "").lstrip("@")
    script = Path(__file__).with_name("browser_x_briefing.py")
    cmd = [
        sys.executable,
        str(script),
        "--keywords",
        args.keywords,
        "--out",
        args.out,
        "--scrolls",
        str(args.scrolls),
        "--dm-threads",
        str(args.dm_threads),
    ]
    if args.handle:
        cmd.extend(["--handle", handle])
    elif handle:
        cmd.extend(["--handle", handle])
    if args.include_dms:
        cmd.append("--include-dms")
    subprocess.run(cmd, check=True)
    out_dir = Path(args.out)
    memory_result = None
    if not args.no_memory:
        memory_result = update_from_file(
            input_path=out_dir / "briefing-input.json",
            markdown_path=out_dir / "briefing-input.md",
            out_dir=out_dir,
            memory_dir=Path(args.memory_dir).expanduser().resolve(),
            include_dms=args.include_dms,
            dm_threads=args.dm_threads,
        )
    result = {
        "briefing_markdown": str(out_dir / "briefing-input.md"),
        "briefing_json": str(out_dir / "briefing-input.json"),
        "memory_context_markdown": str(out_dir / "memory-context.md"),
        "memory_context_json": str(out_dir / "memory-context.json"),
        "memory_file": None if memory_result is None else memory_result.get("memory_file"),
        "daily_archive_dir": None if memory_result is None else memory_result.get("daily_dir"),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
