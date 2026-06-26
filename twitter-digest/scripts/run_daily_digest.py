#!/usr/bin/env python3
"""Chat-friendly wrapper for collecting X/Twitter daily digest input."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from digest_context import build_current_context_from_file


STATE_DIR = Path(__file__).resolve().parents[1] / ".state"
CONFIG_PATH = STATE_DIR / "config.json"
DEFAULT_OUT_DIR = STATE_DIR / "run"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handle")
    parser.add_argument("--account-name")
    parser.add_argument("--save-default", action="store_true", help="Save --handle/--account-name as the default account for future chat runs.")
    parser.add_argument("--configure-only", action="store_true", help="Only save default account config; do not collect data.")
    parser.add_argument("--keywords", default="", help="Optional comma-separated search queries. Default is empty; the daily digest focuses on timeline, mentions, and DMs.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--include-dms", action="store_true", help="Include visible DMs. This is already the default; kept for compatibility.")
    parser.add_argument("--no-dms", action="store_true", help="Skip X Messages collection for this run.")
    parser.add_argument("--dm-threads", type=int, default=5)
    parser.add_argument("--scrolls", type=int, default=4)
    parser.add_argument("--headless", action="store_true", help="Run browser collection headlessly. This is the default when login is already saved.")
    parser.add_argument("--headed", action="store_true", help="Force a visible browser window for debugging or manual login.")
    parser.add_argument("--non-interactive", action="store_true", help="Do not open a visible browser for DM passcode recovery; record a data gap instead.")
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
    script = Path(__file__).with_name("browser_x_digest.py")
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
    include_dms = not args.no_dms
    if args.include_dms:
        include_dms = True
    if include_dms:
        cmd.append("--include-dms")
    if args.headed:
        cmd.append("--headed")
    if args.headless:
        cmd.append("--headless")
    if args.non_interactive:
        cmd.append("--non-interactive")
    subprocess.run(cmd, check=True)
    out_dir = Path(args.out)
    build_current_context_from_file(
        input_path=out_dir / "digest-input.json",
        markdown_path=out_dir / "digest-input.md",
        out_dir=out_dir,
    )
    result = {
        "ai_input_markdown": str(out_dir / "digest-context.md"),
        "ai_input_json": str(out_dir / "digest-context.json"),
        "debug_raw_markdown": str(out_dir / "digest-input.md"),
        "debug_raw_json": str(out_dir / "digest-input.json"),
        "memory": "disabled",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
