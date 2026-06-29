#!/usr/bin/env python3
"""Chat-friendly wrapper for collecting X/Twitter daily digest input."""

from __future__ import annotations

import argparse
import base64
import json
import os
import platform
import subprocess
import shlex
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

from digest_context import build_current_context_from_file


STATE_DIR = Path(__file__).resolve().parents[1] / ".state"
CONFIG_PATH = STATE_DIR / "config.json"
API_CONFIG_PATH = STATE_DIR / "api_config.json"
DEFAULT_OUT_DIR = STATE_DIR / "run"
TOKEN_URL = "https://api.x.com/2/oauth2/token"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handle")
    parser.add_argument("--account-name")
    parser.add_argument("--save-default", action="store_true", help="Save --handle/--account-name as the default account for future chat runs.")
    parser.add_argument("--configure-only", action="store_true", help="Only save default account config; do not collect data.")
    parser.add_argument("--keywords", default="", help="Optional comma-separated search queries. Default is empty; the daily digest focuses on timeline, mentions, and DMs.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--source", choices=("auto", "browser", "api"), default="auto", help="Data collection source. auto uses API when configured, otherwise browser.")
    parser.add_argument("--configure-api", action="store_true", help="Open a secure prompt to save X API credentials, then exit.")
    parser.add_argument("--configure-api-token", action="store_true", help="Open a secure prompt to paste an existing X user access token, then exit.")
    parser.add_argument("--api-base", default=os.environ.get("X_API_BASE_URL") or "")
    parser.add_argument("--user-id", default=os.environ.get("X_USER_ID") or os.environ.get("TWITTER_USER_ID") or "")
    parser.add_argument("--bearer-token", default=os.environ.get("X_BEARER_TOKEN") or os.environ.get("TWITTER_BEARER_TOKEN") or "")
    parser.add_argument("--include-dms", action="store_true", help="Include visible DMs. This is already the default; kept for compatibility.")
    parser.add_argument("--no-dms", action="store_true", help="Skip X Messages collection for this run.")
    parser.add_argument("--dm-threads", type=int, default=5)
    parser.add_argument("--dm-scrolls", type=int, default=200, help="Maximum upward scroll rounds per opened DM thread.")
    parser.add_argument("--dm-max-messages", type=int, default=2000, help="Maximum message bubbles kept per opened DM thread.")
    parser.add_argument("--dm-max-events", type=int, default=300, help="Maximum Direct Message API events kept per run.")
    parser.add_argument("--dm-window-hours", type=int, default=0, help="Stop loading older DM history once messages beyond this window are detected. 0 means load full available thread history.")
    parser.add_argument("--scrolls", type=int, default=40, help="Maximum scroll rounds per public page.")
    parser.add_argument("--max-public-items", type=int, default=300, help="Maximum public post items kept per run.")
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
    except Exception:
        return {}


def load_api_config() -> dict:
    if not API_CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(API_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    user_id = str(data.get("user_id") or "")
    if user_id and not user_id.isdigit() and not data.get("handle"):
        data["handle"] = user_id.lstrip("@")
        data["user_id"] = ""
    return data


def save_api_config(config: dict) -> None:
    API_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        API_CONFIG_PATH.parent.chmod(0o700)
    except PermissionError:
        pass
    API_CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        API_CONFIG_PATH.chmod(0o600)
    except PermissionError:
        pass


def refresh_oauth_token_if_needed(config: dict) -> dict:
    refresh_token = str(config.get("refresh_token") or "")
    client_id = str(config.get("client_id") or "")
    if not refresh_token or not client_id:
        return config
    try:
        expires_at = int(str(config.get("expires_at") or "0"))
    except ValueError:
        expires_at = 0
    if expires_at and expires_at - int(time.time()) > 300:
        return config
    form = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }
    body = urllib.parse.urlencode(form).encode("utf-8")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    client_secret = str(config.get("client_secret") or "")
    if client_secret:
        encoded = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {encoded}"
    request = urllib.request.Request(TOKEN_URL, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            token = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(f"Saved OAuth token could not be refreshed: {exc}. Falling back to current token.", flush=True)
        return config
    access_token = str(token.get("access_token") or "")
    if not access_token:
        return config
    now = int(time.time())
    updated = dict(config)
    updated["bearer_token"] = access_token
    if token.get("refresh_token"):
        updated["refresh_token"] = str(token.get("refresh_token"))
    updated["token_type"] = str(token.get("token_type") or updated.get("token_type") or "bearer")
    updated["expires_in"] = str(token.get("expires_in") or "")
    updated["issued_at"] = str(now)
    updated["expires_at"] = str(now + int(token.get("expires_in") or 0)) if token.get("expires_in") else ""
    save_api_config(updated)
    print("Refreshed saved X OAuth access token.", flush=True)
    return updated


def save_config(handle: str | None, account_name: str | None) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    config = load_config()
    if handle:
        config["handle"] = handle.lstrip("@")
    if account_name:
        config["account_name"] = account_name
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return "~/" + str(path.expanduser().resolve().relative_to(Path.home()))
    except ValueError:
        return str(path)


def open_config_in_terminal(extra_args: list[str]) -> bool:
    if platform.system() != "Darwin":
        return False
    script = Path(__file__).with_name("configure_api.py")
    command_path = Path(tempfile.gettempdir()) / "twitter-digest-config.command"
    shell_command = "\n".join(
        [
            "#!/bin/zsh",
            "set +e",
            "terminal_tty=$(tty)",
            f"cd {shlex.quote(str(Path(__file__).resolve().parents[1]))}",
            "echo 'X API 配置向导'",
            "echo '使用 OAuth2 PKCE，需要 X Developer App 的 Client ID，并通过浏览器授权账号。'",
            "echo",
            " ".join([shlex.quote(sys.executable), shlex.quote(str(script)), *[shlex.quote(arg) for arg in extra_args]]),
            "status=$?",
            "echo",
            "echo '配置流程已结束。Terminal 将自动关闭。'",
            "{ sleep 0.5; osascript <<OSA >/dev/null 2>&1",
            "set targetTTY to \"$terminal_tty\"",
            "tell application \"Terminal\"",
            "  repeat with w in windows",
            "    repeat with t in tabs of w",
            "      if (tty of t) is targetTTY then",
            "        close w",
            "        return",
            "      end if",
            "    end repeat",
            "  end repeat",
            "end tell",
            "OSA",
            "} >/dev/null 2>&1 &",
            "disown",
            "exit $status",
        ]
    )
    try:
        command_path.write_text(shell_command, encoding="utf-8")
        command_path.chmod(0o700)
        subprocess.run(["open", "-a", "Terminal", str(command_path)], check=True)
    except (OSError, subprocess.CalledProcessError):
        return False
    print("已打开 Terminal 窗口用于配置 X API。", flush=True)
    print(f"配置会保存到：{display_path(Path(__file__).resolve().parents[1] / '.state' / 'api_config.json')}", flush=True)
    return True


def api_configured(bearer_token: str) -> bool:
    return bool(bearer_token)


def summarize_child_error(error: subprocess.CalledProcessError) -> str:
    text = "\n".join(part for part in [error.stdout or "", error.stderr or ""] if part)
    if not text:
        return f"collector exited with code {error.returncode}"
    markers = [
        "client-not-enrolled",
        "Appropriate Level of API Access",
        "Forbidden",
        "Unauthorized",
        "HTTP 403",
        "HTTP 401",
    ]
    matched = [marker for marker in markers if marker in text]
    if matched:
        return "; ".join(dict.fromkeys(matched))
    compact = " ".join(text.split())
    return compact[:500]


def api_command(args: argparse.Namespace, out_dir: str, api_base: str, user_id: str, handle: str) -> list[str]:
    cmd = [
        sys.executable,
        str(Path(__file__).with_name("api_x_digest.py")),
        "--keywords",
        args.keywords,
        "--out",
        out_dir,
        "--max-public-items",
        str(args.max_public_items),
        "--public-window-hours",
        str(args.public_window_hours),
        "--api-base",
        api_base,
        "--dm-max-events",
        str(args.dm_max_events),
    ]
    if user_id:
        cmd.extend(["--user-id", user_id])
    if handle:
        cmd.extend(["--handle", handle])
    return cmd


def browser_command(args: argparse.Namespace, out_dir: str, handle: str, include_dms: bool, dm_only: bool = False) -> list[str]:
    cmd = [
        sys.executable,
        str(Path(__file__).with_name("browser_x_digest.py")),
        "--keywords",
        args.keywords,
        "--out",
        out_dir,
        "--max-public-items",
        "1" if dm_only else str(args.max_public_items),
        "--public-window-hours",
        str(args.public_window_hours),
        "--scrolls",
        "0" if dm_only else str(args.scrolls),
        "--dm-threads",
        str(args.dm_threads),
        "--dm-scrolls",
        str(args.dm_scrolls),
        "--dm-max-messages",
        str(args.dm_max_messages),
        "--dm-window-hours",
        str(args.dm_window_hours),
    ]
    if handle:
        cmd.extend(["--handle", handle])
    if include_dms:
        cmd.append("--include-dms")
    if args.headed:
        cmd.append("--headed")
    if args.headless:
        cmd.append("--headless")
    if args.non_interactive:
        cmd.append("--non-interactive")
    return cmd


def run_api_command(cmd: list[str], env: dict[str, str]) -> None:
    completed = subprocess.run(cmd, check=True, env=env, capture_output=True, text=True)
    if completed.stdout:
        print(completed.stdout.strip(), flush=True)


def run_browser_command(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def merge_api_public_with_browser_dm(api_out: Path, browser_out: Path, final_out: Path) -> None:
    api_data = json.loads((api_out / "digest-input.json").read_text(encoding="utf-8"))
    browser_data = json.loads((browser_out / "digest-input.json").read_text(encoding="utf-8"))
    browser_messages = [page for page in browser_data.get("pages", []) if isinstance(page, dict) and page.get("kind") == "messages"]
    if not browser_messages:
        browser_messages = [
            {
                "kind": "messages",
                "url": "https://x.com/messages",
                "items": [],
                "dm_status": "no_visible_threads",
                "dm_note": "Browser DM collection completed but did not produce a messages page.",
                "dm_threads": [],
                "dm_visible_thread_count": 0,
                "dm_replied_thread_count": 0,
                "dm_unreplied_thread_count": 0,
                "dm_captured_message_count": 0,
            }
        ]
    merged_pages = [page for page in api_data.get("pages", []) if not (isinstance(page, dict) and page.get("kind") == "messages")]
    merged_pages.extend(browser_messages)
    api_data["pages"] = merged_pages
    api_data["source"] = "api+browser_dm"
    api_data["dm_source"] = "browser"
    final_out.mkdir(parents=True, exist_ok=True)
    (final_out / "digest-input.json").write_text(json.dumps(api_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
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
    api_config = refresh_oauth_token_if_needed(load_api_config())
    bearer_token = args.bearer_token or str(api_config.get("bearer_token") or "")
    api_base = args.api_base or str(api_config.get("api_base") or "https://api.x.com/2")
    user_id = args.user_id or str(api_config.get("user_id") or "")
    handle = (args.handle or api_config.get("handle") or config.get("handle") or "").lstrip("@")
    source = args.source if args.source != "auto" else ("api" if api_configured(bearer_token) else "browser")
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
        print("API source selected for public data. Browser collection will be used for X Chat/DM.", flush=True)
    print(f"Collecting X digest data via {source} source.", flush=True)
    try:
        if source == "api":
            if include_dms:
                with tempfile.TemporaryDirectory(prefix="x-digest-api-") as api_tmp, tempfile.TemporaryDirectory(prefix="x-digest-browser-dm-") as browser_tmp:
                    run_api_command(api_command(args, api_tmp, api_base, user_id, handle), child_env)
                    print("Collecting X Chat/DM via browser source.", flush=True)
                    run_browser_command(browser_command(args, browser_tmp, handle, include_dms=True, dm_only=True))
                    merge_api_public_with_browser_dm(Path(api_tmp), Path(browser_tmp), Path(args.out))
                    source = "api+browser_dm"
            else:
                run_api_command(cmd, child_env)
        else:
            run_browser_command(cmd)
    except subprocess.CalledProcessError as exc:
        summary = summarize_child_error(exc)
        if args.source == "auto" and source == "api":
            print(f"API collection unavailable ({summary}). Falling back to browser collection.", flush=True)
            source = "browser"
            run_browser_command(browser_command(args, args.out, handle, include_dms))
        else:
            print(f"API collection failed: {summary}", file=sys.stderr, flush=True)
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
        "debug_raw_markdown": str(out_dir / "digest-input.md"),
        "debug_raw_json": str(out_dir / "digest-input.json"),
        "memory": "disabled",
        "source": source,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
