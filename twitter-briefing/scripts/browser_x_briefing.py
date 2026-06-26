#!/usr/bin/env python3
"""Collect X/Twitter briefing input through a persistent local browser session."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import socket
import struct
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handle", help="Your X handle, with or without @. If omitted, the script tries to detect it from the logged-in page.")
    parser.add_argument("--keywords", default="", help="Comma-separated keywords or queries for hotspot search.")
    parser.add_argument("--out", default="x-browser-briefing-output", help="Output directory.")
    parser.add_argument("--profile-dir", default=str(Path.home() / ".twitter-briefing" / "chrome-profile"))
    parser.add_argument("--scrolls", type=int, default=4, help="Scroll rounds per page.")
    parser.add_argument("--login-timeout-sec", type=int, default=300)
    parser.add_argument("--include-dms", action="store_true", help="Also visit X messages and capture visible conversation text.")
    parser.add_argument("--dm-threads", type=int, default=5, help="Maximum recent DM threads to open when --include-dms is set.")
    parser.add_argument("--headless", action="store_true", help="Run without a visible browser window. This is the default after first login.")
    parser.add_argument("--headed", action="store_true", help="Force a visible browser window for debugging or manual login.")
    parser.add_argument("--keep-browser-open", action="store_true")
    return parser.parse_args()


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


def launch_browser(profile_dir: Path, start_url: str, headless: bool) -> tuple[subprocess.Popen[bytes], int]:
    profile_dir.mkdir(parents=True, exist_ok=True)
    port = get_free_port()
    command = [
        find_chrome(),
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        start_url,
    ]
    if headless:
        command.extend(["--headless=new", "--disable-gpu", "--window-size=1440,1200"])
    proc = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wait_for_cdp(port)
    return proc, port


def ensure_logged_in(profile_dir: Path, timeout_sec: int, force_headed: bool) -> tuple[subprocess.Popen[bytes], int, bool]:
    if force_headed:
        proc, port = launch_browser(profile_dir, "https://x.com/home", headless=False)
        wait_for_login(port, timeout_sec, interactive=True)
        return proc, port, False

    proc, port = launch_browser(profile_dir, "https://x.com/home", headless=True)
    if is_logged_in(port):
        print("X login detected in saved browser session. Continuing headless collection...")
        return proc, port, True

    print("Saved X login was not available. Opening a visible browser window for one-time login...")
    stop_browser(proc)
    proc, port = launch_browser(profile_dir, "https://x.com/home", headless=False)
    wait_for_login(port, timeout_sec, interactive=True)
    return proc, port, False


def is_logged_in(port: int) -> bool:
    try:
        ws_url = wait_for_cdp_page_ws(port)
        return has_x_login_cookie(ws_url)
    except Exception:
        return False


def wait_for_login(port: int, timeout_sec: int, interactive: bool) -> None:
    if interactive:
        print("Waiting for X login in the opened browser window...")
    else:
        print("Waiting for X login...")
    deadline = time.time() + timeout_sec
    last_notice = 0.0
    while time.time() < deadline:
        try:
            ws_url = wait_for_cdp_page_ws(port)
            if has_x_login_cookie(ws_url):
                print("X login detected. Continuing with browser collection...")
                return
        except Exception:
            pass
        if time.time() - last_notice > 15:
            if interactive:
                print("Still waiting for X login. Log in once in the opened browser window.")
            else:
                print("Still waiting for X login.")
            last_notice = time.time()
        time.sleep(2)
    raise SystemExit("Timed out waiting for X login.")


def stop_browser(proc: subprocess.Popen[bytes]) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def has_x_login_cookie(ws_url: str) -> bool:
    for cookie in cdp_get_all_cookies(ws_url):
        if cookie.get("name") == "auth_token" and domain_matches_x(str(cookie.get("domain") or "")):
            return True
    return False


def domain_matches_x(domain: str) -> bool:
    domain = domain.lstrip(".").lower()
    return domain == "x.com" or domain.endswith(".x.com") or domain == "twitter.com" or domain.endswith(".twitter.com")


def build_pages(handle: str | None, keywords: str, include_dms: bool) -> list[dict[str, str]]:
    pages = [{"kind": "home", "url": "https://x.com/home"}]
    if handle:
        clean = handle.lstrip("@")
        query = urllib.parse.quote(f"@{clean}")
        pages.append({"kind": "own_profile", "url": f"https://x.com/{clean}"})
        pages.append({"kind": "mentions_search", "url": f"https://x.com/search?q={query}&src=typed_query&f=live"})
        pages.append({"kind": "mentions_notifications", "url": "https://x.com/notifications/mentions"})
    for index, keyword in enumerate([k.strip() for k in keywords.split(",") if k.strip()], start=1):
        pages.append(
            {
                "kind": f"keyword_{index}",
                "url": f"https://x.com/search?q={urllib.parse.quote(keyword)}&src=typed_query&f=live",
            }
        )
    if include_dms:
        pages.append({"kind": "messages", "url": "https://x.com/messages"})
    return pages


def collect_page(port: int, page: dict[str, str], scrolls: int, dm_threads: int = 5) -> dict[str, Any]:
    ws_url = wait_for_cdp_page_ws(port)
    cdp_call(ws_url, "Page.enable")
    cdp_call(ws_url, "Runtime.enable")
    cdp_call(ws_url, "Page.navigate", {"url": page["url"]})
    time.sleep(5)
    posts: list[dict[str, Any]] = []
    for _ in range(max(scrolls, 1)):
        posts.extend(extract_articles(ws_url))
        cdp_eval(ws_url, "window.scrollBy(0, Math.max(900, window.innerHeight * 0.9));")
        time.sleep(2)
    posts.extend(extract_articles(ws_url))
    extra: dict[str, Any] = {}
    if page["kind"] == "messages":
        extra["visible_text"] = extract_main_text(ws_url)
        extra.update(collect_dm_threads(ws_url, max_threads=dm_threads))
    return {"kind": page["kind"], "url": page["url"], "items": dedupe_items(posts), **extra}


def collect_dm_threads(ws_url: str, max_threads: int) -> dict[str, Any]:
    main_text = extract_main_text(ws_url)
    if "Create Passcode" in main_text or "Set Passcode" in main_text:
        return {
            "dm_status": "blocked_by_x_chat_passcode",
            "dm_note": "X Chat is showing an end-to-end encryption passcode setup screen before message content is visible.",
            "dm_threads": [],
        }

    thread_links = extract_dm_thread_links(ws_url)
    if not thread_links:
        return {
            "dm_status": "no_visible_threads",
            "dm_note": "No DM conversation links were visible on the messages page.",
            "dm_threads": [],
        }

    threads: list[dict[str, Any]] = []
    for link in thread_links[: max(max_threads, 0)]:
        cdp_call(ws_url, "Page.navigate", {"url": link["url"]})
        time.sleep(4)
        for _ in range(2):
            cdp_eval(ws_url, "window.scrollBy(0, -Math.max(700, window.innerHeight * 0.8));")
            time.sleep(1)
        threads.append(
            {
                "url": link["url"],
                "label": link.get("label") or "",
                "text": extract_main_text(ws_url),
            }
        )

    return {
        "dm_status": "captured_threads" if threads else "no_visible_threads",
        "dm_note": f"Opened up to {max_threads} visible DM thread(s) and captured on-screen text only.",
        "dm_threads": threads,
    }


def extract_dm_thread_links(ws_url: str) -> list[dict[str, str]]:
    script = r"""
(() => {
  const seen = new Set();
  return Array.from(document.querySelectorAll('a[href^="/messages/"], a[href*="x.com/messages/"]')).map((a) => {
    const url = new URL(a.getAttribute('href'), location.href);
    url.search = '';
    url.hash = '';
    return { url: url.href, label: (a.innerText || a.getAttribute('aria-label') || '').trim() };
  }).filter((item) => {
    if (!/^https:\/\/(x|twitter)\.com\/messages\/[^/]+/.test(item.url)) return false;
    if (seen.has(item.url)) return false;
    seen.add(item.url);
    return true;
  });
})()
"""
    value = cdp_eval(ws_url, script)
    if not isinstance(value, list):
        return []
    out: list[dict[str, str]] = []
    for item in value:
        if isinstance(item, dict) and isinstance(item.get("url"), str):
            out.append({"url": str(item["url"]), "label": str(item.get("label") or "")})
    return out


def extract_articles(ws_url: str) -> list[dict[str, Any]]:
    script = r"""
(() => {
  const statusUrl = (href) => {
    try {
      const url = new URL(href, location.href);
      return /\/status\/\d+/.test(url.pathname) ? url.href : null;
    } catch { return null; }
  };
  return Array.from(document.querySelectorAll('article')).map((article) => {
    const text = (article.innerText || '').trim();
    const links = Array.from(article.querySelectorAll('a[href]')).map(a => a.href).filter(Boolean);
    const status = links.map(statusUrl).find(Boolean) || null;
    const times = Array.from(article.querySelectorAll('time')).map(t => t.getAttribute('datetime')).filter(Boolean);
    const authorLinks = links.filter(h => {
      try {
        const p = new URL(h).pathname;
        return /^\/[^/]+$/.test(p) && !p.includes('/i/');
      } catch { return false; }
    });
    return { text, url: status, links, time: times[0] || null, authorUrl: authorLinks[0] || null };
  }).filter(item => item.text);
})()
"""
    value = cdp_eval(ws_url, script)
    return value if isinstance(value, list) else []


def extract_main_text(ws_url: str) -> str:
    script = r"""
(() => {
  const main = document.querySelector('main') || document.body;
  return (main.innerText || '').trim().slice(0, 12000);
})()
"""
    value = cdp_eval(ws_url, script)
    return str(value or "")


def detect_handle(port: int) -> str | None:
    ws_url = wait_for_cdp_page_ws(port)
    cdp_call(ws_url, "Page.enable")
    cdp_call(ws_url, "Runtime.enable")
    cdp_call(ws_url, "Page.navigate", {"url": "https://x.com/home"})
    time.sleep(5)
    script = r"""
(() => {
  const account = document.querySelector('[data-testid="SideNav_AccountSwitcher_Button"]');
  const accountText = account ? account.innerText : '';
  const accountMatch = accountText.match(/@([A-Za-z0-9_]{1,15})/);
  if (accountMatch) return accountMatch[1];
  const profileLink = document.querySelector('[data-testid="AppTabBar_Profile_Link"]');
  const profileHref = profileLink ? profileLink.getAttribute('href') : '';
  const profileMatch = profileHref.match(/^\/([A-Za-z0-9_]{1,15})$/);
  if (profileMatch) return profileMatch[1];
  const labels = Array.from(document.querySelectorAll('[aria-label]')).map(el => el.getAttribute('aria-label') || '');
  for (const label of labels) {
    const match = label.match(/@([A-Za-z0-9_]{1,15})/);
    if (match && /account|profile|账号|帳號|账户/i.test(label)) return match[1];
  }
  return null;
})()
"""
    value = cdp_eval(ws_url, script)
    return str(value).lstrip("@") if value else None


def dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = str(item.get("url") or item.get("text") or "")[:500]
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def render_markdown(data: dict[str, Any]) -> str:
    lines = [
        "# X 浏览器采集输入",
        "",
        f"- 生成时间: `{data['generated_at']}`",
        f"- 浏览器 profile: `{data['profile_dir']}`",
        f"- 当前账号: `{data.get('handle') or ''}`",
        "",
    ]
    for page in data["pages"]:
        lines.extend([f"## {page['kind']}", "", f"Source: {page['url']}", ""])
        lines.append(f"采集条数: `{len(page.get('items', []))}`")
        lines.append("")
        for item in page["items"][:80]:
            text = " ".join(str(item.get("text") or "").split())
            url = item.get("url") or ""
            timestamp = item.get("time") or ""
            lines.append(f"- `{timestamp}` {url}")
            lines.append(f"  {text[:1000]}")
        if page.get("visible_text"):
            lines.extend(["", "页面可见文本摘录:", "", str(page["visible_text"])[:3000]])
        if page.get("dm_status"):
            lines.extend(["", f"DM 状态: `{page['dm_status']}`"])
            if page.get("dm_note"):
                lines.append(str(page["dm_note"]))
        for thread in page.get("dm_threads", [])[:20]:
            lines.extend(["", f"### DM thread: {thread.get('label') or thread.get('url')}", ""])
            lines.append(str(thread.get("text") or "")[:3000])
        lines.append("")
    lines.extend(
        [
            "## 数据缺口",
            "",
            "- 浏览器采集依赖 X 页面结构和已加载的可见内容。",
            "- 日报默认使用较小滚动次数；需要更全覆盖时再提高 `--scrolls`。",
            "- DM 属于私密内容。只有用户明确同意本地读取时才使用 `--include-dms`。",
        ]
    )
    return "\n".join(lines) + "\n"


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
        with urllib.request.urlopen(url, timeout=1) as response:
            targets = json.loads(response.read().decode("utf-8"))
        if isinstance(targets, list):
            for target in targets:
                if not isinstance(target, dict):
                    continue
                ws_url = target.get("webSocketDebuggerUrl")
                target_type = target.get("type")
                if isinstance(ws_url, str) and target_type == "page":
                    fallback = fallback or ws_url
                    target_url = str(target.get("url") or "")
                    if "x.com" in target_url or "twitter.com" in target_url:
                        return ws_url
            if fallback:
                return fallback
        time.sleep(0.2)
    raise SystemExit("Timed out waiting for browser page DevTools endpoint.")


def cdp_get_all_cookies(ws_url: str) -> list[dict[str, object]]:
    result = cdp_call(ws_url, "Network.getAllCookies")
    if isinstance(result, dict) and isinstance(result.get("cookies"), list):
        return [c for c in result["cookies"] if isinstance(c, dict)]
    result = cdp_call(ws_url, "Storage.getCookies")
    if isinstance(result, dict) and isinstance(result.get("cookies"), list):
        return [c for c in result["cookies"] if isinstance(c, dict)]
    return []


def cdp_eval(ws_url: str, expression: str) -> Any:
    result = cdp_call(ws_url, "Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True})
    if not isinstance(result, dict):
        return None
    remote = result.get("result", {})
    if isinstance(remote, dict):
        return remote.get("value")
    return None


def cdp_call(ws_url: str, method: str, params: dict[str, Any] | None = None) -> Any:
    sock = websocket_connect(ws_url)
    try:
        websocket_send_json(sock, {"id": 1, "method": method, "params": params or {}})
        deadline = time.time() + 20
        while time.time() < deadline:
            message = websocket_recv_json(sock)
            if message.get("id") == 1:
                if "error" in message:
                    return {}
                return message.get("result", {})
    finally:
        sock.close()
    return {}


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


def main() -> None:
    args = parse_args()
    profile_dir = Path(args.profile_dir).expanduser().resolve()
    force_headed = bool(args.headed and not args.headless)
    proc, port, headless = ensure_logged_in(profile_dir, args.login_timeout_sec, force_headed)
    try:
        handle = args.handle.lstrip("@") if args.handle else detect_handle(port)
        if handle:
            print(f"Using X handle: @{handle}")
        else:
            print("Could not auto-detect X handle. Mention search will be skipped unless --handle is provided.")
        pages = build_pages(handle, args.keywords, args.include_dms)
        data = {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "profile_dir": str(profile_dir),
            "handle": handle,
            "keywords": [k.strip() for k in args.keywords.split(",") if k.strip()],
            "pages": [],
        }
        for page in pages:
            print(f"Collecting {page['kind']}: {page['url']}")
            data["pages"].append(collect_page(port, page, args.scrolls, args.dm_threads))
        out_dir = Path(args.out).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "briefing-input.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        (out_dir / "briefing-input.md").write_text(render_markdown(data), encoding="utf-8")
        print(json.dumps({"out_dir": str(out_dir), "pages": len(data["pages"]), "headless": headless}, indent=2))
    finally:
        if not args.keep_browser_open:
            stop_browser(proc)


if __name__ == "__main__":
    main()
