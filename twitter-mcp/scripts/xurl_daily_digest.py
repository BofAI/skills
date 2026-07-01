#!/usr/bin/env python3
"""Collect X daily digest inputs through the local xurl CLI."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = SKILL_DIR / ".state" / "xurl-run"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect X digest context through xurl CLI.")
    parser.add_argument("--app", default=os.environ.get("X_MCP_APP_NAME") or "", help="xurl app name. Defaults to xurl's configured default app.")
    parser.add_argument("--handle", default="", help="Authenticated account handle, without @. Auto-detected from xurl whoami when possible.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output directory for digest context files.")
    parser.add_argument("--max-results", type=int, default=100, help="Maximum items requested per xurl read command.")
    parser.add_argument("--xurl-command", default=os.environ.get("XURL_COMMAND") or "xurl", help="xurl executable path or command name.")
    parser.add_argument("--include-dms", action=argparse.BooleanOptionalAction, default=True, help="Collect recent DMs through xurl dms.")
    parser.add_argument("--timeout", type=int, default=90, help="Timeout per xurl command in seconds.")
    return parser.parse_args()


def secure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass


def write_private(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def command_display(argv: list[str]) -> str:
    return " ".join(json.dumps(part) if any(ch.isspace() for ch in part) else part for part in argv)


def run_xurl(xurl: str, app: str, args: list[str], timeout: int) -> dict[str, Any]:
    argv = [xurl]
    if app:
        argv.extend(["--app", app])
    argv.extend(args)
    try:
        completed = subprocess.run(argv, check=False, capture_output=True, text=True, timeout=timeout)
        return {
            "name": args[0] if args else "xurl",
            "argv": argv,
            "display": command_display(argv),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except FileNotFoundError:
        return {
            "name": args[0] if args else "xurl",
            "argv": argv,
            "display": command_display(argv),
            "returncode": 127,
            "stdout": "",
            "stderr": f"xurl command not found: {xurl}\n",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "name": args[0] if args else "xurl",
            "argv": argv,
            "display": command_display(argv),
            "returncode": 124,
            "stdout": exc.stdout or "",
            "stderr": (exc.stderr or "") + f"\nTimed out after {timeout} seconds.\n",
        }


def extract_handle(whoami_output: str) -> str:
    try:
        data = json.loads(whoami_output)
        node: Any = data
        if isinstance(node, dict) and isinstance(node.get("data"), dict):
            node = node["data"]
        username = node.get("username") if isinstance(node, dict) else ""
        if isinstance(username, str) and username:
            return username.lstrip("@")
    except json.JSONDecodeError:
        pass
    patterns = [
        r'"username"\s*:\s*"([A-Za-z0-9_]{1,15})"',
        r"(?:username|handle)\s*[:=]\s*@?([A-Za-z0-9_]{1,15})",
        r"@([A-Za-z0-9_]{1,15})",
    ]
    for pattern in patterns:
        match = re.search(pattern, whoami_output, flags=re.IGNORECASE)
        if match:
            return match.group(1).lstrip("@")
    return ""


def markdown_section(result: dict[str, Any]) -> str:
    status = "ok" if result["returncode"] == 0 else f"exit {result['returncode']}"
    chunks = [
        f"## {result['name']} ({status})",
        "",
        f"Command: `{result['display']}`",
        "",
        "### stdout",
        "",
        "```text",
        result["stdout"].rstrip(),
        "```",
    ]
    if result["stderr"].strip():
        chunks.extend(["", "### stderr", "", "```text", result["stderr"].rstrip(), "```"])
    return "\n".join(chunks)


def main() -> int:
    args = parse_args()
    xurl = shutil.which(args.xurl_command) or args.xurl_command
    out_dir = Path(args.out).expanduser().resolve()
    secure_dir(out_dir)

    max_results = max(1, min(args.max_results, 100))
    collected: list[dict[str, Any]] = []

    whoami = run_xurl(xurl, args.app, ["whoami"], args.timeout)
    collected.append(whoami)
    handle = args.handle.lstrip("@") or extract_handle(whoami.get("stdout") or "")

    read_commands: list[tuple[str, list[str]]] = [
        ("timeline", ["timeline", "-n", str(max_results)]),
        ("mentions", ["mentions", "-n", str(max(5, max_results))]),
    ]
    if handle:
        read_commands.extend(
            [
                ("posts", ["posts", handle, "-n", str(max(5, max_results))]),
                ("search_from", ["search", f"from:{handle}", "-n", str(max(10, max_results))]),
                ("search_mentions", ["search", f"@{handle}", "-n", str(max(10, max_results))]),
                ("search_to", ["search", f"to:{handle}", "-n", str(max(10, max_results))]),
            ]
        )
    if args.include_dms:
        read_commands.append(("dms", ["dms", "-n", str(max_results)]))

    for name, command_args in read_commands:
        result = run_xurl(xurl, args.app, command_args, args.timeout)
        result["name"] = name
        collected.append(result)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "xurl-cli",
        "app": args.app or None,
        "handle": handle or None,
        "xurl": xurl,
        "commands": collected,
    }
    write_private(out_dir / "digest-input.json", json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    lines = [
        "# X Daily Digest Context",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        "- source: `xurl-cli`",
        f"- app: `{args.app or 'xurl default'}`",
        f"- handle: `{handle or 'unknown'}`",
        "",
        "Use this file as the source for the Chinese X daily digest. Treat DM sections as private.",
        "",
    ]
    lines.extend(markdown_section(result) for result in collected)
    write_private(out_dir / "digest-context.md", "\n\n".join(lines) + "\n")

    failures = [result for result in collected if result["returncode"] != 0]
    print(json.dumps({
        "source": "xurl-cli",
        "out_dir": str(out_dir),
        "context": str(out_dir / "digest-context.md"),
        "json": str(out_dir / "digest-input.json"),
        "handle": handle or None,
        "commands": len(collected),
        "failures": [{"name": item["name"], "returncode": item["returncode"]} for item in failures],
    }, ensure_ascii=False, indent=2))
    return 0 if len(failures) < len(collected) else 1


if __name__ == "__main__":
    raise SystemExit(main())
