#!/usr/bin/env python3
"""Configure X API credentials for twitter-digest through a chat-friendly prompt."""

from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import platform
import secrets
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path


STATE_DIR = Path(__file__).resolve().parents[1] / ".state"
API_CONFIG_PATH = STATE_DIR / "api_config.json"
DEFAULT_API_BASE = "https://api.x.com/2"
AUTHORIZE_URL = "https://x.com/i/oauth2/authorize"
TOKEN_URL = "https://api.x.com/2/oauth2/token"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8765/callback"
DEFAULT_SCOPES = "dm.read tweet.read users.read offline.access"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bearer-token", help="X API bearer token. Omit to prompt securely.")
    parser.add_argument("--oauth", action="store_true", help="Run OAuth 2.0 Authorization Code with PKCE to get a user-context access token.")
    parser.add_argument("--paste-token", action="store_true", help="Paste an existing user access token instead of running OAuth.")
    parser.add_argument("--client-id", default="")
    parser.add_argument("--client-secret", default="", help="Optional OAuth client secret for confidential apps.")
    parser.add_argument("--redirect-uri", default=DEFAULT_REDIRECT_URI)
    parser.add_argument("--scopes", default=DEFAULT_SCOPES)
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--user-id", default="")
    parser.add_argument("--handle", default="")
    parser.add_argument("--clear", action="store_true", help="Remove saved API credentials.")
    parser.add_argument("--show-status", action="store_true", help="Show whether API credentials are saved.")
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return "~/" + str(path.expanduser().resolve().relative_to(Path.home()))
    except ValueError:
        return str(path)


def apple_prompt(prompt: str, hidden: bool = False, buttons: list[str] | None = None) -> str | None:
    if platform.system() != "Darwin":
        return None
    button_list = buttons or ["Cancel", "Save"]
    script = [
        "display dialog",
        json.dumps(prompt),
        "default answer \"\"",
        "buttons {" + ", ".join(json.dumps(button) for button in button_list) + "}",
        "default button " + json.dumps(button_list[-1]),
    ]
    if hidden:
        script.append("with hidden answer")
    command = " ".join(script)
    try:
        result = subprocess.run(
        ["osascript", "-e", command, "-e", "text returned of result"],
            check=True,
            text=True,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def apple_choice(prompt: str, buttons: list[str]) -> str | None:
    if platform.system() != "Darwin":
        return None
    command = (
        "display dialog "
        + json.dumps(prompt)
        + " buttons {"
        + ", ".join(json.dumps(button) for button in buttons)
        + "} default button "
        + json.dumps(buttons[-1])
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", command, "-e", "button returned of result"],
            check=True,
            text=True,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def choose_mode() -> str:
    choice = apple_choice(
        "配置 X API。推荐选择 OAuth2：需要 X Developer App 的 Client ID，并在浏览器里授权账号。OAuth1 不再作为日报 API 路径使用，因为它不能可靠读取 DM。",
        ["取消", "粘贴 Token", "OAuth2"],
    )
    if choice == "OAuth2":
        return "oauth2"
    if choice == "粘贴 Token":
        return "paste"
    if choice == "取消":
        raise SystemExit("API configuration cancelled.")
    print("请选择 X API 配置方式：")
    print("1. OAuth 2.0 PKCE 授权：输入 Client ID，需要配置 callback，推荐")
    print("2. 粘贴已有 OAuth2/user bearer token")
    if not sys.stdin.isatty():
        raise SystemExit("当前没有可交互终端。请通过 run_daily_digest.py --configure-api 触发，它会打开 Terminal 窗口。")
    value = input("请选择 [默认 1]: ").strip()
    if value == "2":
        return "paste"
    return "oauth2"


def prompt_value(label: str, default: str = "", hidden: bool = False) -> str:
    prompt = f"{label}"
    if default and not hidden:
        prompt += f" [{default}]"
    value = apple_prompt(prompt, hidden=hidden)
    if value is not None:
        return value or default
    if not sys.stdin.isatty():
        raise SystemExit("当前没有可交互终端。请通过 run_daily_digest.py --configure-api 触发，它会打开 Terminal 窗口。")
    if hidden:
        value = getpass.getpass(f"{prompt}: ")
    else:
        value = input(f"{prompt}: ").strip()
    return value or default


def parse_redirect_uri(uri: str) -> tuple[str, int, str]:
    parsed = urllib.parse.urlparse(uri)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise SystemExit("OAuth redirect URI must be local, for example http://127.0.0.1:8765/callback.")
    return parsed.hostname, parsed.port or 80, parsed.path or "/"


def pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).decode("ascii").rstrip("=")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    server: "OAuthServer"

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        self.server.callback_params = {key: values[0] for key, values in params.items() if values}
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h2>X authorization received.</h2><p>You can close this window and return to the agent.</p></body></html>"
        )

    def log_message(self, *_args: object) -> None:
        return


class OAuthServer(HTTPServer):
    callback_params: dict[str, str]


def wait_for_callback(redirect_uri: str) -> dict[str, str]:
    host, port, _path = parse_redirect_uri(redirect_uri)
    server = OAuthServer((host, port), OAuthCallbackHandler)
    server.callback_params = {}
    try:
        server.handle_request()
        return server.callback_params
    finally:
        server.server_close()


def exchange_code_for_token(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code_verifier: str,
) -> dict[str, object]:
    form = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }
    body = urllib.parse.urlencode(form).encode("utf-8")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if client_secret:
        encoded = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {encoded}"
    request = urllib.request.Request(TOKEN_URL, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise SystemExit(f"OAuth token exchange failed: {exc}") from exc


def run_oauth_flow(args: argparse.Namespace, existing: dict[str, str]) -> dict[str, str]:
    client_id = args.client_id or prompt_value("请输入 X OAuth Client ID", default=str(existing.get("client_id") or ""))
    if not client_id:
        raise SystemExit("Client ID is required for OAuth authorization.")
    client_secret = args.client_secret or prompt_value(
        "请输入 X OAuth Client Secret，可选；public PKCE app 可留空",
        default=str(existing.get("client_secret") or ""),
        hidden=True,
    )
    redirect_uri = args.redirect_uri or DEFAULT_REDIRECT_URI
    scopes = args.scopes or DEFAULT_SCOPES
    code_verifier, code_challenge = pkce_pair()
    state = secrets.token_urlsafe(24)
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scopes,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    authorize_url = AUTHORIZE_URL + "?" + urllib.parse.urlencode(params)
    print("正在打开 X OAuth 授权页面...", flush=True)
    print(f"请确认 X Developer App 已配置这个 Redirect URI：{redirect_uri}", flush=True)
    webbrowser.open(authorize_url)
    callback = wait_for_callback(redirect_uri)
    if callback.get("state") != state:
        raise SystemExit("OAuth state mismatch. API configuration was not saved.")
    if callback.get("error"):
        raise SystemExit(f"OAuth authorization failed: {callback.get('error_description') or callback.get('error')}")
    code = callback.get("code")
    if not code:
        raise SystemExit("OAuth callback did not include an authorization code.")
    token = exchange_code_for_token(code, client_id, client_secret, redirect_uri, code_verifier)
    access_token = str(token.get("access_token") or "")
    if not access_token:
        raise SystemExit(f"OAuth token response did not include access_token: {token}")
    return {
        "bearer_token": access_token,
        "refresh_token": str(token.get("refresh_token") or ""),
        "token_type": str(token.get("token_type") or "bearer"),
        "expires_in": str(token.get("expires_in") or ""),
        "issued_at": str(int(time.time())),
        "expires_at": str(int(time.time()) + int(token.get("expires_in") or 0)) if token.get("expires_in") else "",
        "auth_method": "oauth2_pkce_user_context",
        "client_id": client_id.strip(),
        "redirect_uri": redirect_uri.strip(),
        "scopes": scopes.strip(),
    }


def save_api_config(config: dict[str, str]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        STATE_DIR.chmod(0o700)
    except PermissionError:
        pass
    API_CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        API_CONFIG_PATH.chmod(0o600)
    except PermissionError:
        pass


def load_api_config() -> dict[str, str]:
    if not API_CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(API_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def clear_api_config() -> None:
    if API_CONFIG_PATH.exists():
        API_CONFIG_PATH.unlink()


def main() -> None:
    args = parse_args()
    if args.clear:
        clear_api_config()
        print(json.dumps({"api_config": str(API_CONFIG_PATH), "configured": False, "cleared": True}, ensure_ascii=False, indent=2))
        return
    if args.show_status:
        config = load_api_config()
        print(
            json.dumps(
                {
                    "api_config": str(API_CONFIG_PATH),
                    "configured": bool(config.get("bearer_token")),
                    "auth_method": config.get("auth_method") or "",
                    "api_base": config.get("api_base") or "",
                    "handle": config.get("handle") or "",
                    "user_id": config.get("user_id") or "",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    existing = load_api_config()
    mode = (
        "oauth2"
        if args.oauth
        else "paste"
        if args.paste_token or args.bearer_token
        else choose_mode()
    )
    if mode == "oauth2":
        token_config = run_oauth_flow(args, existing)
        bearer_token = token_config["bearer_token"]
    else:
        bearer_token = args.bearer_token or prompt_value("请粘贴 OAuth user access token", hidden=True)
        if not bearer_token:
            raise SystemExit("No access token provided. API configuration was not changed.")
        token_config = {"bearer_token": bearer_token.strip(), "auth_method": "pasted_user_access_token"}
    api_base = args.api_base or existing.get("api_base") or DEFAULT_API_BASE
    handle = args.handle or str(token_config.get("handle") or existing.get("handle") or "")
    user_id = args.user_id or str(token_config.get("user_id") or existing.get("user_id") or "")
    config = {
        **token_config,
        "api_base": api_base.strip() or DEFAULT_API_BASE,
        "handle": handle.strip().lstrip("@"),
        "user_id": user_id.strip(),
    }
    save_api_config(config)
    print(
        json.dumps(
            {
                "api_config": str(API_CONFIG_PATH),
                "configured": True,
                "auth_method": config.get("auth_method") or "",
                "api_base": config["api_base"],
                "handle": config["handle"],
                "user_id": config["user_id"],
                "next_step": "Run scripts/run_daily_digest.py; --source auto will use the saved API token.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print(f"Saved API credentials to {display_path(API_CONFIG_PATH)} with owner-only permissions.", flush=True)


if __name__ == "__main__":
    main()
