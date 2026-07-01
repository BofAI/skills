#!/usr/bin/env python3
"""Chat-friendly wrapper for collecting X/Twitter daily digest input."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from api_config_store import API_CONFIG_PATH, load_api_config, refresh_oauth_token_if_needed
from collector_commands import api_collector_command, browser_collector_command, summarize_collector_error
from digest_context import build_current_context_from_file
from script_utils import display_path, open_script_in_terminal, rerun_from_installed_if_needed


STATE_DIR = Path(__file__).resolve().parents[1] / ".state"
CONFIG_PATH = STATE_DIR / "config.json"
DEFAULT_OUT_DIR = STATE_DIR / "run"
DEFAULT_API_PUBLIC_ITEMS = 300
DEFAULT_BROWSER_PUBLIC_ITEMS = 100


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handle")
    parser.add_argument("--account-name")
    parser.add_argument("--save-default", action="store_true", help="Save --handle/--account-name as the default account for future chat runs.")
    parser.add_argument("--configure-only", action="store_true", help="Only save default account config; do not collect data.")
    parser.add_argument("--keywords", default="", help="Optional comma-separated search queries. Default is empty; the daily digest focuses on timeline, mentions, and DMs.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--source", choices=("auto", "browser", "api"), default="auto", help="Data collection source. Default auto: API when configured, otherwise browser. Use browser to force local browser collection.")
    parser.add_argument("--configure-api", action="store_true", help="Open a secure prompt to save X API credentials, then exit.")
    parser.add_argument("--configure-api-token", action="store_true", help="Open a secure prompt to paste an existing X user access token, then exit.")
    parser.add_argument("--api-base", default=os.environ.get("X_API_BASE_URL") or "")
    parser.add_argument("--user-id", default=os.environ.get("X_USER_ID") or os.environ.get("TWITTER_USER_ID") or "")
    parser.add_argument("--bearer-token", default=os.environ.get("X_BEARER_TOKEN") or os.environ.get("TWITTER_BEARER_TOKEN") or "")
    parser.add_argument("--include-dms", action="store_true", help="Include visible DMs. This is already the default; kept for compatibility.")
    parser.add_argument("--no-dms", action="store_true", help="Skip X Messages collection for this run.")
    parser.add_argument("--dm-threads", type=int, default=5)
    parser.add_argument("--dm-list-scrolls", type=int, default=20, help="Maximum downward scroll rounds used to scan today's DM conversation list.")
    parser.add_argument("--dm-scrolls", type=int, default=200, help="Maximum upward scroll rounds per opened DM thread.")
    parser.add_argument("--dm-max-messages", type=int, default=2000, help="Maximum message bubbles kept per opened DM thread.")
    parser.add_argument("--dm-max-events", type=int, default=300, help="Maximum Direct Message API events kept per run.")
    parser.add_argument("--dm-window-hours", type=int, default=0, help="Stop loading older DM history once messages beyond this window are detected. 0 means load full available thread history.")
    parser.add_argument("--scrolls", type=int, default=40, help="Maximum scroll rounds per public page.")
    parser.add_argument("--min-public-scrolls", type=int, default=5, help="Minimum public-page scroll rounds before early stop rules can end collection.")
    parser.add_argument(
        "--max-public-items",
        type=int,
        default=None,
        help="Override maximum public post items for both collectors. Defaults: API 300, browser 100.",
    )
    parser.add_argument("--public-window-hours", type=int, default=24, help="Stop loading older public timeline items once posts beyond this window are detected.")
    parser.add_argument("--headless", action="store_true", help="Run browser collection headlessly. This is the default when login is already saved.")
    parser.add_argument("--headed", action="store_true", help="Force a visible browser window for debugging or manual login.")
    parser.add_argument("--non-interactive", action="store_true", help="Do not open a visible browser for DM passcode recovery; record a data gap instead.")
    return parser.parse_args()


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not read saved twitter-digest config {CONFIG_PATH}: {exc}", flush=True)
        return {}


def save_config(handle: str | None, account_name: str | None) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    config = load_config()
    if handle:
        config["handle"] = handle.lstrip("@")
    if account_name:
        config["account_name"] = account_name
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def open_config_in_terminal(extra_args: list[str]) -> bool:
    script = Path(__file__).with_name("configure_api.py")
    opened = open_script_in_terminal(
        script=script,
        args=extra_args,
        cwd=Path(__file__).resolve().parents[1],
        heading="X API 配置向导",
        description="使用 OAuth2 PKCE，需要 X Developer App 的 Client ID，并通过浏览器授权账号。",
    )
    if not opened:
        return False
    print("已打开 Terminal 窗口用于配置 X API。", flush=True)
    print(f"配置会保存到：{display_path(Path(__file__).resolve().parents[1] / '.state' / 'api_config.json')}", flush=True)
    return True


def api_configured(bearer_token: str) -> bool:
    return bool(bearer_token)


def has_saved_api_credentials(config: dict) -> bool:
    return any(str(config.get(key) or "") for key in ("bearer_token", "refresh_token", "client_id"))


def summarize_child_error(error: subprocess.CalledProcessError) -> str:
    text = "\n".join(part for part in [error.stdout or "", error.stderr or ""] if part)
    return summarize_collector_error(text, returncode=error.returncode)


def api_public_item_limit(args: argparse.Namespace) -> int:
    return max(1, int(args.max_public_items if args.max_public_items is not None else DEFAULT_API_PUBLIC_ITEMS))


def browser_public_item_limit(args: argparse.Namespace) -> int:
    return max(1, int(args.max_public_items if args.max_public_items is not None else DEFAULT_BROWSER_PUBLIC_ITEMS))


def api_command(args: argparse.Namespace, out_dir: str, api_base: str, user_id: str, handle: str) -> list[str]:
    return api_collector_command(
        sys.executable,
        Path(__file__).resolve().parent,
        out_dir,
        keywords=args.keywords,
        max_public_items=api_public_item_limit(args),
        public_window_hours=args.public_window_hours,
        dm_max_events=args.dm_max_events,
        api_base=api_base,
        user_id=user_id,
        handle=handle,
    )


def browser_command(args: argparse.Namespace, out_dir: str, handle: str, include_dms: bool, dm_only: bool = False) -> list[str]:
    return browser_collector_command(
        sys.executable,
        Path(__file__).resolve().parent,
        out_dir,
        keywords=args.keywords,
        max_public_items=browser_public_item_limit(args),
        public_window_hours=args.public_window_hours,
        min_public_scrolls=args.min_public_scrolls,
        scrolls=args.scrolls,
        dm_threads=args.dm_threads,
        dm_list_scrolls=args.dm_list_scrolls,
        dm_scrolls=args.dm_scrolls,
        dm_max_messages=args.dm_max_messages,
        dm_window_hours=args.dm_window_hours,
        handle=handle,
        include_dms=include_dms,
        dm_only=dm_only,
        headed=args.headed,
        headless=args.headless,
        non_interactive=args.non_interactive,
    )


def run_api_command(cmd: list[str], env: dict[str, str]) -> None:
    completed = subprocess.run(cmd, check=True, env=env, capture_output=True, text=True)
    if completed.stdout:
        print(completed.stdout.strip(), flush=True)


def run_browser_command(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> None:
    rerun_from_installed_if_needed(__file__)
    args = parse_args()
    if args.configure_api:
        if not sys.stdin.isatty() and open_config_in_terminal(["--oauth"]):
            return
        subprocess.run([sys.executable, str(Path(__file__).with_name("configure_api.py")), "--oauth"], check=True)
        return
    if args.configure_api_token:
        if not sys.stdin.isatty() and open_config_in_terminal(["--paste-token"]):
            return
        subprocess.run([sys.executable, str(Path(__file__).with_name("configure_api.py")), "--paste-token"], check=True)
        return
    if args.save_default:
        save_config(args.handle, args.account_name)
    if args.configure_only:
        print(json.dumps({"config": str(CONFIG_PATH), "saved": bool(args.save_default)}, ensure_ascii=False, indent=2))
        return
    config = load_config()
    raw_api_config = load_api_config()
    saved_api_configured = has_saved_api_credentials(raw_api_config)
    api_config = refresh_oauth_token_if_needed(raw_api_config)
    explicit_bearer_token = bool(args.bearer_token)
    refresh_error = str(api_config.get("refresh_error") or "")
    if refresh_error and not explicit_bearer_token:
        print(
            f"Saved X OAuth token refresh failed: {refresh_error}. Run --configure-api to reauthorize, or pass X_BEARER_TOKEN to override.",
            flush=True,
        )
    saved_bearer_token = "" if refresh_error and not explicit_bearer_token else str(api_config.get("bearer_token") or "")
    bearer_token = args.bearer_token or saved_bearer_token
    api_base = args.api_base or str(api_config.get("api_base") or "https://api.x.com/2")
    user_id = args.user_id or str(api_config.get("user_id") or "")
    handle = (args.handle or api_config.get("handle") or config.get("handle") or "").lstrip("@")
    source = args.source
    if source == "auto":
        source = "api" if (explicit_bearer_token or saved_api_configured or api_configured(bearer_token)) else "browser"
    if source == "api" and refresh_error and not explicit_bearer_token:
        raise SystemExit("Saved X OAuth token refresh failed. Re-run --configure-api or pass X_BEARER_TOKEN to use API source. Browser collection will not be opened while API is configured.")
    include_dms = not args.no_dms
    if args.include_dms:
        include_dms = True
    if source == "api":
        cmd = api_command(args, args.out, api_base, user_id, handle)
        child_env = os.environ.copy()
        if bearer_token:
            child_env["X_BEARER_TOKEN"] = bearer_token
    else:
        cmd = browser_command(args, args.out, handle, include_dms)
        child_env = None
    if source == "api" and include_dms:
        print("API source selected. Browser DM collection is not run for API source; use --source browser when DMs are required.", flush=True)
    print(f"Collecting X digest data via {source} source.", flush=True)
    try:
        if source == "api":
            run_api_command(cmd, child_env)
        else:
            run_browser_command(cmd)
    except subprocess.CalledProcessError as exc:
        summary = summarize_child_error(exc)
        source_label = "API" if source == "api" else source.capitalize()
        print(f"{source_label} collection failed: {summary}", file=sys.stderr, flush=True)
        raise SystemExit(exc.returncode) from exc
    out_dir = Path(args.out)
    build_current_context_from_file(
        input_path=out_dir / "digest-input.json",
        markdown_path=out_dir / "digest-input.md",
        out_dir=out_dir,
    )
    result = {
        "ai_input_markdown": str(out_dir / "digest-context.md"),
        "ai_input_json": str(out_dir / "digest-context.json"),
        "ai_input_slices": {
            "timeline": str(out_dir / "digest-context-timeline.md"),
            "mentions": str(out_dir / "digest-context-mentions.md"),
            "dm": str(out_dir / "digest-context-dm.md"),
        },
        "debug_raw_markdown": str(out_dir / "digest-input.md"),
        "debug_raw_json": str(out_dir / "digest-input.json"),
        "memory": "disabled",
        "source": source,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
