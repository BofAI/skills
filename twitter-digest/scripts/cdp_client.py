"""Chrome DevTools Protocol helpers for browser-based X collection."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import socket
import struct
import time
import urllib.parse
import urllib.request
from typing import Any, Optional


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
    fallback: Optional[str] = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                targets = json.loads(response.read().decode("utf-8"))
        except Exception:
            time.sleep(0.2)
            continue
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
    if not isinstance(result, dict) or cdp_error(result):
        return None
    remote = result.get("result", {})
    if isinstance(remote, dict):
        return remote.get("value")
    return None

def cdp_error(result: Any) -> bool:
    return isinstance(result, dict) and isinstance(result.get("_cdp_error"), str)

def cdp_call(ws_url: str, method: str, params: Optional[dict[str, Any]] = None, retries: int = 2) -> Any:
    last_error = ""
    for _ in range(max(retries, 1)):
        sock: Optional[socket.socket] = None
        try:
            sock = websocket_connect(ws_url)
            websocket_send_json(sock, {"id": 1, "method": method, "params": params or {}})
            deadline = time.time() + 20
            while time.time() < deadline:
                message = websocket_recv_json(sock)
                if message.get("id") == 1:
                    if "error" in message:
                        return {"_cdp_error": json.dumps(message.get("error"), ensure_ascii=False)}
                    return message.get("result", {})
            last_error = f"Timed out waiting for CDP response to {method}"
        except Exception as exc:
            last_error = str(exc)
            time.sleep(0.4)
        finally:
            if sock is not None:
                sock.close()
    return {"_cdp_error": last_error or f"CDP call failed: {method}"}

def websocket_connect(ws_url: str) -> socket.socket:
    if not ws_url.startswith("ws://"):
        raise RuntimeError("Only local ws:// DevTools endpoints are supported.")
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
        raise RuntimeError("Could not open DevTools WebSocket.")
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
        raise ConnectionError("DevTools WebSocket closed.")
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
            raise ConnectionError("Unexpected end of DevTools WebSocket stream.")
        chunks.extend(chunk)
    return bytes(chunks)
