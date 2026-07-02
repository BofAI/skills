"""Small shared utilities for twitter-digest scripts."""

from __future__ import annotations

import datetime as dt
import os
import platform
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


def display_path(path: Path) -> str:
    try:
        return "~/" + str(path.expanduser().resolve().relative_to(Path.home()))
    except ValueError:
        return str(path)


def ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except PermissionError:
        pass


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat()


def now_stamp() -> str:
    return dt.datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def local_timezone_name() -> str:
    tz = dt.datetime.now().astimezone().tzinfo
    return str(tz) if tz else "local"


def format_local_time(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if parsed.tzinfo is None:
        return text
    local = parsed.astimezone()
    return local.strftime("%Y-%m-%d %H:%M:%S %Z")


def installed_skill_roots() -> list[Path]:
    codex = Path.home() / ".codex" / "skills" / "twitter-digest"
    claude = Path.home() / ".claude" / "skills" / "twitter-digest"
    if any(key.startswith("CODEX_") for key in os.environ):
        return [codex, claude]
    if any(key.startswith("CLAUDE") for key in os.environ):
        return [claude, codex]
    return [claude, codex]


def rerun_from_installed_if_needed(script_file: str, argv: Optional[list[str]] = None) -> None:
    if os.environ.get("TWITTER_DIGEST_NO_INSTALL_REDIRECT"):
        return
    current_script = Path(script_file).resolve()
    current_root = current_script.parents[1]
    for root in installed_skill_roots():
        if not root.exists():
            continue
        try:
            if root.resolve() == current_root:
                return
        except OSError:
            continue
        installed_script = root / "scripts" / current_script.name
        if installed_script.exists():
            print(f"Detected source checkout. Re-running installed twitter-digest script: {display_path(installed_script)}", flush=True)
            os.execv(sys.executable, [sys.executable, str(installed_script), *(argv if argv is not None else sys.argv[1:])])


def open_script_in_terminal(script: Path, args: list[str], cwd: Path, heading: str, description: str) -> bool:
    if platform.system() != "Darwin":
        return False
    command_path = Path(tempfile.gettempdir()) / f"{script.stem}-terminal.command"
    shell_command = "\n".join(
        [
            "#!/bin/zsh",
            "set +e",
            "terminal_tty=$(tty)",
            f"cd {shlex.quote(str(cwd))}",
            f"echo {shlex.quote(heading)}",
            f"echo {shlex.quote(description)}",
            "echo",
            " ".join([shlex.quote(sys.executable), shlex.quote(str(script)), *[shlex.quote(arg) for arg in args]]),
            "status=$?",
            "echo",
            "echo '流程已结束。Terminal 将自动关闭。'",
            "{ sleep 1; osascript <<OSA >/dev/null 2>&1",
            "set targetTTY to \"$terminal_tty\"",
            "tell application \"Terminal\"",
            "  repeat with w in windows",
            "    repeat with t in tabs of w",
            "      if ((tty of t) as string) is targetTTY then",
            "        close w saving no",
            "        return",
            "      end if",
            "    end repeat",
            "  end repeat",
            "  if (count of windows) > 0 then close front window saving no",
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
    return True
