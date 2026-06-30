"""Browser process and login lifecycle helpers for X collection."""

from __future__ import annotations

import shutil
import socket
import subprocess
import time
from pathlib import Path

from cdp_client import cdp_get_all_cookies, wait_for_cdp, wait_for_cdp_page_ws


def find_chrome() -> str:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "microsoft-edge",
        "brave-browser",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.is_absolute() and path.exists():
            return candidate
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
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

def ensure_logged_in(profile_dir: Path, timeout_sec: int, force_headed: bool, non_interactive: bool) -> tuple[subprocess.Popen[bytes], int, bool, bool]:
    if force_headed:
        proc, port = launch_browser(profile_dir, "https://x.com/home", headless=False)
        wait_for_login(port, timeout_sec, interactive=True)
        return proc, port, False, True

    proc, port = launch_browser(profile_dir, "https://x.com/home", headless=True)
    if is_logged_in(port):
        print("X login detected in saved browser session. Continuing headless collection...")
        return proc, port, True, True

    if non_interactive:
        print("Saved X login was not available. Non-interactive mode will record a login data gap without opening a browser.")
        return proc, port, True, False

    print("Saved X login was not available. Opening a visible browser window for one-time login...")
    stop_browser(proc)
    proc, port = launch_browser(profile_dir, "https://x.com/home", headless=False)
    wait_for_login(port, timeout_sec, interactive=True)
    print("X login completed. Returning to headless collection...")
    stop_browser(proc)
    proc, port = launch_browser(profile_dir, "https://x.com/home", headless=True)
    wait_for_login(port, timeout_sec, interactive=False)
    return proc, port, True, True

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
