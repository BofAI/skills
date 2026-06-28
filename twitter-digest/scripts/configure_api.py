#!/usr/bin/env python3
"""Configure X API credentials for twitter-digest through a chat-friendly prompt."""

from __future__ import annotations

import argparse
import base64
import getpass
import hmac
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
OAUTH1_REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
OAUTH1_AUTHORIZE_URL = "https://api.twitter.com/oauth/authorize"
OAUTH1_ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8765/callback"
DEFAULT_SCOPES = "tweet.read users.read follows.read offline.access"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bearer-token", help="X API bearer token. Omit to prompt securely.")
    parser.add_argument("--oauth", action="store_true", help="Run OAuth 2.0 Authorization Code with PKCE to get a user-context access token.")
    parser.add_argument("--oauth1", action="store_true", help="Run OAuth 1.0a PIN authorization to get user access token and token secret.")
    parser.add_argument("--paste-token", action="store_true", help="Paste an existing user access token instead of running OAuth.")
    parser.add_argument("--paste-oauth1", action="store_true", help="Paste existing OAuth 1.0a consumer/user tokens.")
    parser.add_argument("--client-id", default="")
    parser.add_argument("--client-secret", default="", help="Optional OAuth client secret for confidential apps.")
    parser.add_argument("--consumer-key", default="")
    parser.add_argument("--consumer-secret", default="")
    parser.add_argument("--access-token", default="")
    parser.add_argument("--access-token-secret", default="")
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
        "配置 X API。推荐选择 OAuth1 PIN：用户只需要准备 X Developer App 的 API Key 和 API Key Secret。",
        ["取消", "粘贴 Token", "OAuth2", "OAuth1 PIN"],
    )
    if choice == "OAuth1 PIN":
        return "oauth1"
    if choice == "OAuth2":
        return "oauth2"
    if choice == "粘贴 Token":
        return "paste"
    if choice == "取消":
        raise SystemExit("API configuration cancelled.")
    print("请选择 X API 配置方式：")
    print("1. OAuth 1.0a PIN 授权：输入 API Key / API Key Secret，推荐")
    print("2. OAuth 2.0 PKCE 授权：输入 Client ID，需要配置 callback")
    print("3. 粘贴已有 OAuth2/user bearer token")
    print("4. 粘贴已有 OAuth1 四件套")
    if not sys.stdin.isatty():
        raise SystemExit("当前没有可交互终端。请通过 run_daily_digest.py --configure-api 触发，它会打开 Terminal 窗口。")
    value = input("请选择 [默认 1]: ").strip()
    if value == "2":
        return "oauth2"
    if value == "3":
        return "paste"
    if value == "4":
        return "paste_oauth1"
    return "oauth1"


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


def quote(value: str) -> str:
    return urllib.parse.quote(str(value), safe="~")


def oauth1_header(
    method: str,
    url: str,
    consumer_key: str,
    consumer_secret: str,
    token: str = "",
    token_secret: str = "",
    extra_params: dict[str, str] | None = None,
) -> str:
    params = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": secrets.token_urlsafe(24),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_version": "1.0",
    }
    if token:
        params["oauth_token"] = token
    if extra_params:
        params.update(extra_params)
    parsed = urllib.parse.urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    signing_pairs = query_pairs + sorted(params.items())
    normalized = "&".join(f"{quote(k)}={quote(v)}" for k, v in sorted(signing_pairs))
    signature_base = "&".join([method.upper(), quote(base_url), quote(normalized)])
    signing_key = f"{quote(consumer_secret)}&{quote(token_secret)}"
    signature = base64.b64encode(hmac.new(signing_key.encode("utf-8"), signature_base.encode("utf-8"), hashlib.sha1).digest()).decode("ascii")
    params["oauth_signature"] = signature
    return "OAuth " + ", ".join(f'{quote(k)}="{quote(v)}"' for k, v in sorted(params.items()))


def oauth1_post_form(
    url: str,
    consumer_key: str,
    consumer_secret: str,
    token: str = "",
    token_secret: str = "",
    extra_params: dict[str, str] | None = None,
) -> dict[str, str]:
    headers = {
        "Authorization": oauth1_header("POST", url, consumer_key, consumer_secret, token, token_secret, extra_params),
        "User-Agent": "twitter-digest/1.0",
    }
    request = urllib.request.Request(url, data=b"", headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            text = response.read().decode("utf-8")
    except Exception as exc:
        raise SystemExit(f"OAuth1 request failed: {exc}") from exc
    return {key: values[0] for key, values in urllib.parse.parse_qs(text).items() if values}


def run_oauth1_pin_flow(args: argparse.Namespace, existing: dict[str, str]) -> dict[str, str]:
    consumer_key = args.consumer_key or prompt_value("请输入 X API Key / Consumer Key", default=str(existing.get("consumer_key") or ""))
    consumer_secret = args.consumer_secret or prompt_value("请输入 X API Key Secret / Consumer Secret", hidden=True)
    if not consumer_key or not consumer_secret:
        raise SystemExit("Consumer key and consumer secret are required for OAuth1 authorization.")
    request_token = oauth1_post_form(
        OAUTH1_REQUEST_TOKEN_URL,
        consumer_key,
        consumer_secret,
        extra_params={"oauth_callback": "oob"},
    )
    resource_token = str(request_token.get("oauth_token") or "")
    resource_secret = str(request_token.get("oauth_token_secret") or "")
    if not resource_token or not resource_secret:
        raise SystemExit(f"OAuth1 request token response was incomplete: {request_token}")
    authorization_url = OAUTH1_AUTHORIZE_URL + "?" + urllib.parse.urlencode({"oauth_token": resource_token})
    print("正在打开 X OAuth1 授权页面...", flush=True)
    print(f"如果浏览器没有自动打开，请手动访问：{authorization_url}", flush=True)
    webbrowser.open(authorization_url)
    pin = prompt_value("授权完成后，请粘贴 X 页面显示的 PIN")
    if not pin:
        raise SystemExit("No OAuth verifier PIN provided. API configuration was not changed.")
    access = oauth1_post_form(
        OAUTH1_ACCESS_TOKEN_URL,
        consumer_key,
        consumer_secret,
        token=resource_token,
        token_secret=resource_secret,
        extra_params={"oauth_verifier": pin.strip()},
    )
    access_token = str(access.get("oauth_token") or "")
    access_token_secret = str(access.get("oauth_token_secret") or "")
    if not access_token or not access_token_secret:
        raise SystemExit(f"OAuth1 access token response was incomplete: {access}")
    return {
        "auth_method": "oauth1a_user_context",
        "consumer_key": consumer_key.strip(),
        "consumer_secret": consumer_secret.strip(),
        "access_token": access_token,
        "access_token_secret": access_token_secret,
        "user_id": str(access.get("user_id") or ""),
        "handle": str(access.get("screen_name") or ""),
    }


def paste_oauth1_tokens(args: argparse.Namespace, existing: dict[str, str]) -> dict[str, str]:
    consumer_key = args.consumer_key or prompt_value("X API Key / Consumer Key", default=str(existing.get("consumer_key") or ""))
    consumer_secret = args.consumer_secret or prompt_value("X API Key Secret / Consumer Secret", hidden=True)
    access_token = args.access_token or prompt_value("User access token", default=str(existing.get("access_token") or ""), hidden=True)
    access_token_secret = args.access_token_secret or prompt_value("User access token secret", hidden=True)
    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        raise SystemExit("Consumer key, consumer secret, access token, and access token secret are required.")
    return {
        "auth_method": "oauth1a_user_context",
        "consumer_key": consumer_key.strip(),
        "consumer_secret": consumer_secret.strip(),
        "access_token": access_token.strip(),
        "access_token_secret": access_token_secret.strip(),
    }


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
                    "configured": bool(config.get("bearer_token") or (config.get("access_token") and config.get("access_token_secret"))),
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
        "oauth1"
        if args.oauth1
        else "oauth2"
        if args.oauth
        else "paste_oauth1"
        if args.paste_oauth1
        else "paste"
        if args.paste_token or args.bearer_token
        else choose_mode()
    )
    if mode == "oauth1":
        token_config = run_oauth1_pin_flow(args, existing)
    elif mode == "oauth2":
        token_config = run_oauth_flow(args, existing)
        bearer_token = token_config["bearer_token"]
    elif mode == "paste_oauth1":
        token_config = paste_oauth1_tokens(args, existing)
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
