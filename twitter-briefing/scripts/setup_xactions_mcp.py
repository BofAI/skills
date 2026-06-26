#!/usr/bin/env python3
"""Guided local setup for cookie-based Twitter/X MCP without exposing cookies."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import getpass
import json
import os
import socket
import ssl
import struct
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", choices=["codex", "claude-desktop", "generic"], default="codex")
    parser.add_argument("--token", help="Legacy X auth_token. Prefer --browser-login so ct0 and twid are captured too.")
    parser.add_argument("--cookies", help="TWITTER_COOKIES JSON array. Avoid this flag in shared terminals.")
    parser.add_argument("--browser-login", action="store_true", help="Launch an isolated browser, let the user log in to X, then capture required cookies locally.")
    parser.add_argument("--login-timeout-sec", type=int, default=300, help="How long to wait for browser login when --browser-login is used.")
    parser.add_argument("--dry-run", action="store_true", help="Print target path/config shape without writing secrets.")
    return parser.parse_args()


def toml_escape(value: str) -> str:
    return json.dumps(value)


def get_token(args: argparse.Namespace) -> str:
    if args.dry_run:
        return "REDACTED"
    if args.browser_login:
        cookies = get_cookies_from_browser_login(args.login_timeout_sec)
        if cookies:
            return cookies
        raise SystemExit("Could not find required X cookies after browser login.")
    if args.cookies:
        return args.cookies
    token = args.token or getpass.getpass("Paste X auth_token (hidden input): ").strip()
    if not token:
        raise SystemExit("No auth_token provided.")
    if any(ch.isspace() for ch in token):
        raise SystemExit("auth_token should not contain whitespace.")
    return json.dumps([f"auth_token={token}; Domain=.twitter.com"])


def find_chrome() -> str:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise SystemExit("No supported Chromium browser found. Install Chrome, Chromium, Edge, or Brave.")


def get_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def get_cookies_from_browser_login(timeout_sec: int) -> str | None:
    browser = find_chrome()
    port = get_free_port()
    profile = tempfile.TemporaryDirectory(prefix="xactions-login.")
    command = [
        browser,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile.name}",
        "--no-first-run",
        "--no-default-browser-check",
        "https://x.com",
    ]
    proc = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        print("A dedicated browser window opened at https://x.com.")
        wait_for_cdp(port)
        print(f"Log in to X in that window. Waiting up to {timeout_sec} seconds for login to complete...")
        deadline = time.time() + timeout_sec
        last_notice = 0.0
        while time.time() < deadline:
            ws_url = wait_for_cdp_page_ws(port)
            cookies = required_cookie_json(cdp_get_all_cookies(ws_url))
            if cookies:
                print("Detected required X cookies. Writing MCP config...")
                return cookies
            if time.time() - last_notice > 15:
                print("Still waiting for X login...")
                last_notice = time.time()
            time.sleep(2)
        return None
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        profile.cleanup()


def domain_matches_x(domain: str) -> bool:
    domain = domain.lstrip(".").lower()
    return domain == "x.com" or domain.endswith(".x.com") or domain == "twitter.com" or domain.endswith(".twitter.com")


def required_cookie_json(cookies: list[dict[str, object]]) -> str | None:
    required = {"auth_token": None, "ct0": None, "twid": None}
    for cookie in cookies:
        name = str(cookie.get("name") or "")
        if name in required and domain_matches_x(str(cookie.get("domain") or "")):
            value = str(cookie.get("value") or "")
            if value:
                required[name] = value
    if not all(required.values()):
        return None
    return json.dumps(
        [
            f"auth_token={required['auth_token']}; Domain=.twitter.com",
            f"ct0={required['ct0']}; Domain=.twitter.com",
            f"twid={required['twid']}; Domain=.twitter.com",
        ]
    )


def wait_for_cdp(port: int) -> None:
    url = f"http://127.0.0.1:{port}/json/version"
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                json.loads(response.read().decode("utf-8"))
                return
        except Exception:
            time.sleep(0.2)
    raise SystemExit("Timed out waiting for browser DevTools endpoint.")


def wait_for_cdp_page_ws(port: int) -> str:
    url = f"http://127.0.0.1:{port}/json/list"
    deadline = time.time() + 30
    fallback: str | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                targets = json.loads(response.read().decode("utf-8"))
            if isinstance(targets, list):
                for target in targets:
                    if not isinstance(target, dict):
                        continue
                    ws_url = target.get("webSocketDebuggerUrl")
                    target_url = str(target.get("url") or "")
                    target_type = target.get("type")
                    if isinstance(ws_url, str) and target_type == "page":
                        fallback = fallback or ws_url
                        if "x.com" in target_url or "twitter.com" in target_url:
                            return ws_url
                if fallback:
                    return fallback
        except Exception:
            time.sleep(0.2)
    raise SystemExit("Timed out waiting for browser page DevTools endpoint.")


def cdp_get_all_cookies(ws_url: str) -> list[dict[str, object]]:
    sock = websocket_connect(ws_url)
    try:
        websocket_send_json(sock, {"id": 1, "method": "Network.enable"})
        websocket_send_json(sock, {"id": 2, "method": "Network.getAllCookies"})
        websocket_send_json(sock, {"id": 3, "method": "Storage.getCookies"})
        deadline = time.time() + 10
        fallback_error = False
        while time.time() < deadline:
            message = websocket_recv_json(sock)
            if message.get("id") == 2:
                if "error" in message:
                    fallback_error = True
                    continue
                result = message.get("result", {})
                if isinstance(result, dict):
                    cookies = result.get("cookies", [])
                    if isinstance(cookies, list):
                        return [c for c in cookies if isinstance(c, dict)]
                return []
            if message.get("id") == 3 and fallback_error:
                result = message.get("result", {})
                if isinstance(result, dict):
                    cookies = result.get("cookies", [])
                    if isinstance(cookies, list):
                        return [c for c in cookies if isinstance(c, dict)]
                return []
        raise SystemExit("Timed out reading cookies from browser.")
    finally:
        sock.close()


def websocket_connect(ws_url: str) -> socket.socket:
    if not ws_url.startswith("ws://"):
        raise SystemExit("Only local ws:// DevTools endpoints are supported.")
    without_scheme = ws_url[len("ws://") :]
    host_port, path = without_scheme.split("/", 1)
    path = "/" + path
    host, port_s = host_port.rsplit(":", 1)
    raw_sock = socket.create_connection((host, int(port_s)), timeout=5)
    key = base64.b64encode(os.urandom(16)).decode("ascii")
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host_port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n"
    )
    raw_sock.sendall(request.encode("ascii"))
    response = raw_sock.recv(4096)
    if b" 101 " not in response.split(b"\r\n", 1)[0]:
        raw_sock.close()
        raise SystemExit("Could not open DevTools WebSocket.")
    return raw_sock


def websocket_send_json(sock: socket.socket, payload: dict[str, object]) -> None:
    data = json.dumps(payload).encode("utf-8")
    header = bytearray([0x81])
    if len(data) < 126:
        header.append(0x80 | len(data))
    elif len(data) < 65536:
        header.append(0x80 | 126)
        header.extend(struct.pack("!H", len(data)))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack("!Q", len(data)))
    mask = os.urandom(4)
    masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(data))
    sock.sendall(bytes(header) + mask + masked)


def websocket_recv_json(sock: socket.socket) -> dict[str, object]:
    first_two = recv_exact(sock, 2)
    opcode = first_two[0] & 0x0F
    if opcode == 0x8:
        raise SystemExit("DevTools WebSocket closed.")
    length = first_two[1] & 0x7F
    if length == 126:
        length = struct.unpack("!H", recv_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", recv_exact(sock, 8))[0]
    masked = bool(first_two[1] & 0x80)
    mask = recv_exact(sock, 4) if masked else b""
    data = recv_exact(sock, length)
    if masked:
        data = bytes(byte ^ mask[index % 4] for index, byte in enumerate(data))
    if opcode != 0x1:
        return {}
    return json.loads(data.decode("utf-8"))


def recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        chunk = sock.recv(size - len(chunks))
        if not chunk:
            raise SystemExit("Unexpected end of DevTools WebSocket stream.")
        chunks.extend(chunk)
    return bytes(chunks)


def backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_suffix(path.suffix + f".bak-xactions-{stamp}")
    backup_path.write_bytes(path.read_bytes())
    return backup_path


def remove_toml_section(text: str, section: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    skipping = False
    headers = {f"[{section}]", f"[{section}.env]"}
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            skipping = stripped in headers
        if not skipping:
            out.append(line)
    return "\n".join(out).rstrip() + "\n"


def setup_codex(token: str, dry_run: bool) -> None:
    path = Path.home() / ".codex" / "config.toml"
    block = f"""
[mcp_servers.twitter]
command = "npx"
args = ["-y", "agent-twitter-client-mcp"]

[mcp_servers.twitter.env]
AUTH_METHOD = "cookies"
TWITTER_COOKIES = {toml_escape(token)}
""".strip()
    if dry_run:
        print(f"Would update: {path}")
        print(block.replace(token, "REDACTED"))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    updated = remove_toml_section(original, "mcp_servers.xactions")
    updated = remove_toml_section(updated, "mcp_servers.twitter").rstrip() + "\n\n" + block + "\n"
    backup_path = backup(path)
    path.write_text(updated, encoding="utf-8")
    print(f"Updated Codex MCP config: {path}")
    if backup_path:
        print(f"Backup written: {backup_path}")
    print("Restart Codex so it reloads MCP servers, then verify the `twitter` tools are available.")


def setup_claude_desktop(token: str, dry_run: bool) -> None:
    path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    server = {
        "command": "npx",
        "args": ["-y", "agent-twitter-client-mcp"],
        "env": {"AUTH_METHOD": "cookies", "TWITTER_COOKIES": token},
    }
    if dry_run:
        print(f"Would update: {path}")
        print(json.dumps({"mcpServers": {"xactions": server}}, indent=2).replace(token, "REDACTED"))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        config = json.loads(path.read_text(encoding="utf-8") or "{}")
    else:
        config = {}
    servers = config.setdefault("mcpServers", {})
    servers.pop("xactions", None)
    servers["twitter"] = server
    backup_path = backup(path)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"Updated Claude Desktop MCP config: {path}")
    if backup_path:
        print(f"Backup written: {backup_path}")
    print("Restart Claude Desktop so it reloads MCP servers, then verify the `twitter` tools are available.")


def setup_generic(token: str, dry_run: bool) -> None:
    config = {
        "mcpServers": {
            "twitter": {
                "command": "npx",
                "args": ["-y", "agent-twitter-client-mcp"],
                "env": {"AUTH_METHOD": "cookies", "TWITTER_COOKIES": token},
            }
        }
    }
    rendered = json.dumps(config, indent=2)
    print(rendered.replace(token, "REDACTED" if dry_run else "PASTE_AUTH_TOKEN_IN_LOCAL_CONFIG_ONLY"))
    print("Use this shape in your MCP client. Store the real token locally, not in chat or git.")


def main() -> None:
    args = parse_args()
    token = get_token(args)
    if args.client == "codex":
        setup_codex(token, args.dry_run)
    elif args.client == "claude-desktop":
        setup_claude_desktop(token, args.dry_run)
    else:
        setup_generic(token, args.dry_run)


if __name__ == "__main__":
    main()
