#!/usr/bin/env python3
"""Configure X API credentials for twitter-digest through a chat-friendly prompt."""

from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import platform
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from typing import Optional

from api_config_store import API_CONFIG_PATH, DEFAULT_API_BASE, clear_api_config, load_api_config, refresh_oauth_token_if_needed, save_api_config
from script_utils import display_path, open_script_in_terminal, rerun_from_installed_if_needed

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
    parser.add_argument("--verify", action="store_true", help="Verify the saved API token with /users/me and backfill handle/user_id.")
    return parser.parse_args()


def apple_prompt(prompt: str, hidden: bool = False, buttons: Optional[list[str]] = None) -> Optional[str]:
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


def prompt_value(label: str, default: str = "", hidden: bool = False) -> str:
    prompt = f"{label}"
    if default and not hidden:
        prompt += f" [{default}]"
    value = apple_prompt(prompt, hidden=hidden)
    if value is not None:
        return value or default
    if not sys.stdin.isatty():
        raise SystemExit("当前没有可交互终端。请通过已安装 skill 的 run_daily_digest.py --configure-api 触发，或在 Terminal 中运行本命令。")
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
    token_config = {
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
    if client_secret:
        token_config["client_secret"] = client_secret.strip()
    return token_config


def summarize_http_error(exc: BaseException) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        compact = " ".join(body.split())[:300]
        return f"HTTP {exc.code}: {compact}" if compact else f"HTTP {exc.code}"
    return str(exc)


def verify_api_config(config: dict[str, object], save: bool = True) -> dict[str, object]:
    config = refresh_oauth_token_if_needed(dict(config))
    token = str(config.get("bearer_token") or "")
    if not token:
        return {"verified": False, "error": "No saved API bearer token."}
    base = str(config.get("api_base") or DEFAULT_API_BASE).rstrip("/")
    request = urllib.request.Request(
        f"{base}/users/me?user.fields=username,name",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"verified": False, "error": summarize_http_error(exc)}
    user = payload.get("data") if isinstance(payload, dict) else {}
    if not isinstance(user, dict):
        return {"verified": False, "error": "users/me response did not include data."}
    updated = dict(config)
    if user.get("username"):
        updated["handle"] = str(user.get("username") or "").lstrip("@")
    if user.get("id"):
        updated["user_id"] = str(user.get("id") or "")
    if save:
        save_api_config(updated)
    return {
        "verified": True,
        "handle": updated.get("handle") or "",
        "user_id": updated.get("user_id") or "",
        "name": user.get("name") or "",
    }


def main() -> None:
    rerun_from_installed_if_needed(__file__)
    args = parse_args()
    needs_prompt = not (args.clear or args.show_status or args.verify or args.bearer_token)
    if needs_prompt and not sys.stdin.isatty():
        opened = open_script_in_terminal(
            script=Path(__file__).resolve(),
            args=sys.argv[1:],
            cwd=Path(__file__).resolve().parents[1],
            heading="X API 配置向导",
            description="请在这个 Terminal 窗口里输入 Client ID / Secret，并在浏览器里完成 X OAuth2 授权。",
        )
        if opened:
            print("已打开 Terminal 窗口用于配置 X API。", flush=True)
            print(f"配置会保存到：{display_path(API_CONFIG_PATH)}", flush=True)
            return
        raise SystemExit("当前没有可交互终端，且无法自动打开 Terminal。请在 Terminal 中运行该配置命令。")
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
    if args.verify:
        config = load_api_config()
        result = verify_api_config(config, save=True)
        result.update(
            {
                "api_config": str(API_CONFIG_PATH),
                "configured": bool(config.get("bearer_token")),
                "auth_method": config.get("auth_method") or "",
            }
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    existing = load_api_config()
    mode = "paste" if args.paste_token or args.bearer_token else "oauth2"
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
    verification = verify_api_config(config, save=True)
    saved = load_api_config()
    print(
        json.dumps(
            {
                "api_config": str(API_CONFIG_PATH),
                "configured": True,
                "auth_method": saved.get("auth_method") or config.get("auth_method") or "",
                "api_base": saved.get("api_base") or config["api_base"],
                "handle": saved.get("handle") or config["handle"],
                "user_id": saved.get("user_id") or config["user_id"],
                "verification": verification,
                "next_step": "Normal scripts/run_daily_digest.py runs now use the saved API token. Use --source browser only when you explicitly want browser collection.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print(f"Saved API credentials to {display_path(API_CONFIG_PATH)} with owner-only permissions.", flush=True)


if __name__ == "__main__":
    main()
