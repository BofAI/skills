#!/usr/bin/env python3
"""Chat-friendly wrapper for collecting X/Twitter daily digest input."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from api_config_store import load_api_config, refresh_oauth_token_if_needed
from chat_config_store import CHAT_RUNTIME_DIR, chat_configured, chat_runtime_status, load_chat_config
from collector_commands import (
    api_collector_command,
    friendly_chat_collection_error,
    parse_structured_api_error,
    summarize_collector_error,
)
from digest_context import build_current_context_from_file
from digest_io import write_digest_output
from script_utils import ensure_private_dir, open_script_in_terminal, rerun_from_installed_if_needed, write_private_text


STATE_DIR = Path(__file__).resolve().parents[1] / ".state"
CONFIG_PATH = STATE_DIR / "config.json"
DEFAULT_OUT_DIR = STATE_DIR / "run"
DEFAULT_API_PUBLIC_ITEMS = 300
UNSUPPORTED_OPTION_MESSAGE = "Source selection is no longer supported. twitter-digest uses API only."
REQUIRED_CHAT_SCOPES = {"dm.read", "users.read", "tweet.read"}
CHAT_RETRY_MAX_AGE_SECONDS = 15 * 60
CHAT_AUTH_FAILURE = "X Chat 授权已失效。请运行统一配置后重新生成日报。"
CHAT_SCAN_PROFILES = {
    "recent": {"max_conversations": 10, "event_requests": 10, "event_pages": 1},
    "more": {"max_conversations": 50, "event_requests": 20, "event_pages": 3},
}


class ChatCollectionError(RuntimeError):
    """A sanitized X Chat child-process failure."""


def format_chat_collection_failure(summary: str) -> str:
    if summary == CHAT_AUTH_FAILURE:
        return summary
    if parse_structured_api_error(summary):
        return friendly_chat_collection_error(summary)
    return f"X Chat collection failed; digest was not generated: {summary}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handle")
    parser.add_argument("--account-name")
    parser.add_argument("--save-default", action="store_true", help="Save --handle/--account-name as the default account for future chat runs.")
    parser.add_argument("--configure-only", action="store_true", help="Only save default account config; do not collect data.")
    parser.add_argument("--keywords", default="", help="Optional comma-separated search queries. Default is empty; the daily digest focuses on timeline and mentions.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--configure", action="store_true", help="Configure required X API and X Chat access in one secure Terminal flow, then exit.")
    parser.add_argument("--chat-status", action="store_true", help="Show whether required X Chat collection is configured, then exit.")
    parser.add_argument("--disable-chat", action="store_true", help="Disable X Chat collection and remove the saved local key blob, then exit.")
    parser.add_argument("--api-base", default=os.environ.get("X_API_BASE_URL") or "")
    parser.add_argument("--user-id", default=os.environ.get("X_USER_ID") or os.environ.get("TWITTER_USER_ID") or "")
    parser.add_argument("--bearer-token", default="", help=argparse.SUPPRESS)
    parser.add_argument("--scrolls", type=int, default=40, help=argparse.SUPPRESS)
    parser.add_argument("--min-public-scrolls", type=int, default=5, help=argparse.SUPPRESS)
    parser.add_argument(
        "--max-public-items",
        type=int,
        default=None,
        help="Override maximum public post items for API collection. Default: API 300.",
    )
    parser.add_argument("--public-window-hours", type=int, default=24, help="Stop loading older public timeline items once posts beyond this window are detected.")
    parser.add_argument("--chat-window-hours", type=int, default=24, help="Collect X Chat messages from this many recent hours. Default: 24; use 168 for seven days.")
    parser.add_argument(
        "--chat-scan",
        choices=("recent", "more"),
        default="recent",
        help="X Chat scan depth. Default: recent (10 conversations); use more only when explicitly requested.",
    )
    parser.add_argument("--headless", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--headed", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--non-interactive", action="store_true", help=argparse.SUPPRESS)
    args, unknown = parser.parse_known_args()
    if args.bearer_token:
        raise SystemExit("Direct bearer-token overrides are disabled; twitter-digest requires its verified read-only OAuth configuration.")
    if "--source" in unknown or any(arg.startswith("--source=") for arg in unknown):
        raise SystemExit(UNSUPPORTED_OPTION_MESSAGE)
    if unknown:
        parser.error(f"unrecognized arguments: {' '.join(unknown)}")
    return args


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not read saved twitter-digest config {CONFIG_PATH}: {exc}", flush=True)
        return {}


def save_config(handle: Optional[str], account_name: Optional[str]) -> None:
    ensure_private_dir(CONFIG_PATH.parent)
    config = load_config()
    if handle:
        config["handle"] = handle.lstrip("@")
    if account_name:
        config["account_name"] = account_name
    write_private_text(CONFIG_PATH, json.dumps(config, ensure_ascii=False, indent=2) + "\n")


def open_required_config_in_terminal(reason: str) -> bool:
    opened = open_script_in_terminal(
        script=Path(__file__).with_name("configure_all.py"),
        args=[],
        cwd=Path(__file__).resolve().parents[1],
        heading="X 日报统一配置向导",
        description=f"{reason}。请在此窗口完成 X API 授权和 X Chat 配置；如果尚未设置 passcode，会引导你到 X「消息」页面。",
    )
    if not opened:
        return False
    print("已打开一个 Terminal 窗口，用于一次性完成 X API 和 X Chat 配置。", flush=True)
    print(
        json.dumps(
            {
                "status": "configuration_required",
                "terminal_opened": True,
                "next_step": "请在刚打开的 Terminal 窗口完成全部配置。完成后回到当前对话重新生成日报。不要在聊天里粘贴 Client Secret 或 X Chat passcode。",
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )
    return True


def api_configured(bearer_token: str) -> bool:
    return bool(bearer_token)


def api_configuration_present(api_config: dict, bearer_token: str) -> bool:
    return bool(
        bearer_token
        or api_config.get("bearer_token")
        or api_config.get("refresh_token")
        or api_config.get("client_id")
    )


def summarize_child_error(error: subprocess.CalledProcessError) -> str:
    text = "\n".join(part for part in [error.stdout or "", error.stderr or ""] if part)
    return summarize_collector_error(text, returncode=error.returncode)


def api_public_item_limit(args: argparse.Namespace) -> int:
    return max(1, int(args.max_public_items if args.max_public_items is not None else DEFAULT_API_PUBLIC_ITEMS))


def clear_current_run(out_dir: Path) -> None:
    if not out_dir.exists():
        return
    for path in out_dir.glob("digest-*"):
        if path.is_file():
            path.unlink()


def chat_retry_path(out_dir: Path) -> Path:
    return out_dir / "chat-retry.json"


def public_collection_signature(args: argparse.Namespace, api_base: str, user_id: str, handle: str) -> dict[str, object]:
    return {
        "api_base": api_base,
        "user_id": user_id,
        "handle": handle,
        "keywords": args.keywords,
        "max_public_items": api_public_item_limit(args),
        "public_window_hours": max(1, int(args.public_window_hours)),
    }


def mark_chat_retry(out_dir: Path, signature: dict[str, object]) -> None:
    ensure_private_dir(out_dir)
    write_private_text(
        chat_retry_path(out_dir),
        json.dumps({"created_at": time.time(), "public_signature": signature}, ensure_ascii=False, indent=2) + "\n",
    )


def can_resume_public_collection(out_dir: Path, signature: dict[str, object], now: float | None = None) -> bool:
    marker = chat_retry_path(out_dir)
    input_path = out_dir / "digest-input.json"
    if not marker.exists() or not input_path.exists():
        return False
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
        age = (time.time() if now is None else now) - float(data.get("created_at") or 0)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False
    return 0 <= age <= CHAT_RETRY_MAX_AGE_SECONDS and data.get("public_signature") == signature


def clear_chat_retry(out_dir: Path) -> None:
    marker = chat_retry_path(out_dir)
    if marker.exists():
        marker.unlink()


def api_command(args: argparse.Namespace, out_dir: str, api_base: str, user_id: str, handle: str) -> list[str]:
    return api_collector_command(
        sys.executable,
        Path(__file__).resolve().parent,
        out_dir,
        keywords=args.keywords,
        max_public_items=api_public_item_limit(args),
        public_window_hours=args.public_window_hours,
        api_base=api_base,
        user_id=user_id,
        handle=handle,
    )

def run_api_command(cmd: list[str], env: dict[str, str]) -> None:
    completed = subprocess.run(cmd, check=True, env=env, capture_output=True, text=True)
    if completed.stdout:
        print(completed.stdout.strip(), flush=True)


def run_chat_command(cmd: list[str], env: dict[str, str]) -> None:
    try:
        subprocess.run(cmd, check=True, env=env, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        detail = summarize_collector_error("\n".join([exc.stdout or "", exc.stderr or ""]), exc.returncode)
        if api_auth_needs_reconfigure(detail):
            raise ChatCollectionError(CHAT_AUTH_FAILURE) from exc
        raise ChatCollectionError(detail or f"chat collector exited with code {exc.returncode}") from exc

def run_full_configuration(reason: str) -> None:
    print(f"{reason} Starting unified X API and X Chat configuration...", flush=True)
    if not sys.stdin.isatty():
        if open_required_config_in_terminal(reason):
            raise SystemExit(0)
        raise SystemExit("当前没有可交互终端，且无法自动打开 Terminal。请在 Terminal 中运行本命令完成 X API 配置。")
    subprocess.run([sys.executable, str(Path(__file__).with_name("configure_all.py"))], check=True)


def run_chat_configuration(extra_args: list[str]) -> None:
    script = Path(__file__).with_name("configure_chat.py")
    if not sys.stdin.isatty() and not extra_args:
        opened = open_script_in_terminal(
            script=script,
            args=[],
            cwd=Path(__file__).resolve().parents[1],
            heading="X Chat 配置向导",
            description="如果 X Chat 尚未设置 passcode，会引导你先到 X「消息」页面完成设置；已有 passcode 则只在本机解锁，不会保存。",
        )
        if opened:
            print("已打开 Terminal 窗口用于配置 X Chat。", flush=True)
            return
    subprocess.run([sys.executable, str(script), *extra_args], check=True)


def chat_scan_profile(scan: str, hours: int) -> dict[str, int]:
    selected = "more" if int(hours) >= 168 else scan
    return dict(CHAT_SCAN_PROFILES[selected])


def chat_collector_command(
    runtime_python: Path,
    script: Path,
    out_path: Path,
    hours: int,
    scan: str,
) -> list[str]:
    profile = chat_scan_profile(scan, hours)
    return [
        str(runtime_python),
        str(script),
        "--hours", str(max(1, hours)),
        "--out", str(out_path),
        "--max-conversations", str(profile["max_conversations"]),
        "--max-event-requests", str(profile["event_requests"]),
        "--max-event-pages", str(profile["event_pages"]),
    ]


def collect_chat(out_dir: Path, env: dict[str, str], hours: int, scan: str = "recent") -> None:
    runtime_python = CHAT_RUNTIME_DIR / "bin" / "python"
    runtime_ready, runtime_error = chat_runtime_status()
    if not runtime_ready:
        raise SystemExit(f"{runtime_error} Run --configure again.")
    chat_page_path = out_dir / "chat-page.json"
    cmd = chat_collector_command(
        runtime_python,
        Path(__file__).with_name("chat_x_digest.py"),
        chat_page_path,
        hours,
        scan,
    )
    try:
        run_chat_command(cmd, env)
        data = json.loads((out_dir / "digest-input.json").read_text(encoding="utf-8"))
        chat_page = json.loads(chat_page_path.read_text(encoding="utf-8"))
        pages = data.get("pages") if isinstance(data.get("pages"), list) else []
        data["pages"] = [page for page in pages if not (isinstance(page, dict) and page.get("kind") == "messages")]
        data["pages"].append(chat_page)
        data["chat_source"] = "x_chat_api_chatxdk"
        write_digest_output(out_dir, data)
        print("Collected and decrypted required X Chat data.", flush=True)
    except (ChatCollectionError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(format_chat_collection_failure(str(exc))) from exc
    finally:
        if chat_page_path.exists():
            chat_page_path.unlink()


def load_fresh_api_state(args: argparse.Namespace, config: dict) -> tuple[dict, str, str, str, str, str]:
    raw_api_config = load_api_config()
    api_config = refresh_oauth_token_if_needed(raw_api_config)
    refresh_error = str(api_config.get("refresh_error") or "")
    saved_bearer_token = "" if refresh_error and not args.bearer_token else str(api_config.get("bearer_token") or "")
    bearer_token = args.bearer_token or saved_bearer_token
    api_base = args.api_base or str(api_config.get("api_base") or "https://api.x.com/2")
    user_id = args.user_id or str(api_config.get("user_id") or "")
    handle = (args.handle or api_config.get("handle") or config.get("handle") or "").lstrip("@")
    return api_config, refresh_error, bearer_token, api_base, user_id, handle


def api_auth_needs_reconfigure(summary: str) -> bool:
    lowered = summary.lower()
    markers = (
        "unauthorized",
        "http 401",
        "no saved api bearer token",
        "no bearer token",
        "token refresh failed",
        "invalid token",
        "expired token",
    )
    return any(marker in lowered for marker in markers)


def main() -> None:
    rerun_from_installed_if_needed(__file__)
    args = parse_args()
    if args.configure:
        run_full_configuration("User requested configuration.")
        return
    if args.chat_status:
        run_chat_configuration(["--status"])
        return
    if args.disable_chat:
        run_chat_configuration(["--clear"])
        return
    if args.save_default:
        save_config(args.handle, args.account_name)
    if args.configure_only:
        print(json.dumps({"config": str(CONFIG_PATH), "saved": bool(args.save_default)}, ensure_ascii=False, indent=2))
        return
    config = load_config()
    explicit_bearer_token = bool(args.bearer_token)
    api_config, refresh_error, bearer_token, api_base, user_id, handle = load_fresh_api_state(args, config)
    refresh_error = str(api_config.get("refresh_error") or "")
    saved_scopes = set(str(api_config.get("scopes") or "").split())
    if not saved_scopes:
        run_full_configuration("Saved X OAuth token has no scope metadata; read-only reauthorization is required")
        raise SystemExit(0)
    if not explicit_bearer_token and "dm.write" in saved_scopes:
        run_full_configuration("Saved X OAuth token can write DMs and must be replaced with a read-only token")
        raise SystemExit(0)
    missing_chat_scopes = REQUIRED_CHAT_SCOPES - saved_scopes if saved_scopes else set()
    if not explicit_bearer_token and missing_chat_scopes:
        run_full_configuration(
            "Saved X OAuth token is missing required X Chat scopes: " + ", ".join(sorted(missing_chat_scopes))
        )
        raise SystemExit(0)
    if not explicit_bearer_token and (refresh_error or not api_configured(bearer_token)):
        reason = "X API 配置是必需项，但当前缺失或已失效" if not refresh_error else f"X API token refresh failed: {refresh_error}"
        run_full_configuration(reason)
        api_config, refresh_error, bearer_token, api_base, user_id, handle = load_fresh_api_state(args, config)
        if refresh_error or not api_configured(bearer_token):
            raise SystemExit("X API configuration did not produce a usable token. Re-run configuration and try again.")
    if refresh_error and not explicit_bearer_token:
        raise SystemExit("Saved X OAuth token refresh failed. Re-run --configure.")
    chat_config = load_chat_config()
    if not chat_configured():
        run_full_configuration("X Chat configuration is required before a complete digest can be generated.")
        raise SystemExit(0)
    if user_id and str(chat_config.get("user_id") or "") != user_id:
        raise SystemExit("Saved X Chat keys belong to a different X account. Run --disable-chat, then --configure for the current account.")
    out_dir = Path(args.out)
    signature = public_collection_signature(args, api_base, user_id, handle)
    resume_public = can_resume_public_collection(out_dir, signature)
    cmd = api_command(args, args.out, api_base, user_id, handle)
    child_env = os.environ.copy()
    if bearer_token:
        child_env["X_BEARER_TOKEN"] = bearer_token
    if resume_public:
        print("Reusing public data from the immediately preceding failed X Chat run; retrying X Chat only.", flush=True)
    else:
        clear_chat_retry(out_dir)
        clear_current_run(out_dir)
        print("Collecting X digest data via API.", flush=True)
        retried_after_reconfigure = False
        while True:
            try:
                run_api_command(cmd, child_env)
                break
            except subprocess.CalledProcessError as exc:
                summary = summarize_child_error(exc)
                if not explicit_bearer_token and not retried_after_reconfigure and api_auth_needs_reconfigure(summary):
                    retried_after_reconfigure = True
                    run_full_configuration(f"X API authentication failed: {summary}")
                    api_config, refresh_error, bearer_token, api_base, user_id, handle = load_fresh_api_state(args, config)
                    if refresh_error or not api_configured(bearer_token):
                        raise SystemExit("X API reconfiguration did not produce a usable token.") from exc
                    cmd = api_command(args, args.out, api_base, user_id, handle)
                    child_env = os.environ.copy()
                    child_env["X_BEARER_TOKEN"] = bearer_token
                    continue
                print(f"API collection failed: {summary}", file=sys.stderr, flush=True)
                raise SystemExit(exc.returncode) from exc
        mark_chat_retry(out_dir, signature)
    collect_chat(out_dir, child_env, args.chat_window_hours, args.chat_scan)
    clear_chat_retry(out_dir)
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
        "source": "api",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
