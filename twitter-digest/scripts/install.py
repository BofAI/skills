#!/usr/bin/env python3
"""Install twitter-digest into the active agent client's local skills directory."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil as shutil_module
import shutil
import sys
from pathlib import Path

from script_utils import display_path


def detect_client() -> str:
    if any(key.startswith("CODEX_") for key in os.environ):
        return "codex"
    if any(key.startswith("CLAUDE") for key in os.environ):
        return "claude"
    codex_dir = Path.home() / ".codex" / "skills"
    claude_dir = Path.home() / ".claude" / "skills"
    if codex_dir.exists() and not claude_dir.exists():
        return "codex"
    if claude_dir.exists() and not codex_dir.exists():
        return "claude"
    return "claude"


def default_skills_dir(client: str) -> Path:
    if client == "codex":
        return Path.home() / ".codex" / "skills"
    return Path.home() / ".claude" / "skills"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", choices=("auto", "codex", "claude"), default="auto", help="Target agent client. auto installs into the detected current tool's skills directory.")
    parser.add_argument("--skills-dir", default="", help="Override the target skills directory.")
    parser.add_argument("--copy", action="store_true", help="Copy files instead of creating a symlink. This is the default.")
    parser.add_argument("--symlink", action="store_true", help="Install as a symlink for local skill development.")
    parser.add_argument("--skip-browser-check", action="store_true", help="Skip checking for a supported Chromium browser.")
    parser.add_argument(
        "--allow-claude-commands",
        action="store_true",
        help=(
            "Opt in to adding a Claude Code global Bash allow rule for the installed run_daily_digest.py command. "
            "This only applies when installing for Claude Code."
        ),
    )
    parser.add_argument(
        "--allow-claude-state-read",
        action="store_true",
        help=(
            "Opt in to adding the installed twitter-digest .state directory to Claude Code additionalDirectories "
            "so analysis can read digest-context.md without a file-access prompt."
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def browser_candidates() -> list[str]:
    return [
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


def find_supported_browser() -> str | None:
    for candidate in browser_candidates():
        path = Path(candidate).expanduser()
        if path.is_absolute() and path.exists():
            return str(path)
        resolved = shutil_module.which(candidate)
        if resolved:
            return resolved
    return None


def check_runtime(skip_browser_check: bool) -> None:
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10+ is required to run twitter-digest.")
    if skip_browser_check:
        print("Skipped browser check. Runtime still requires Chrome, Chromium, Edge, or Brave.", flush=True)
        return
    browser = find_supported_browser()
    if not browser:
        raise SystemExit(
            "No supported Chromium browser found. Install one of: Google Chrome, Chromium, Microsoft Edge, or Brave. "
            "Then rerun the installer. Use --skip-browser-check only if the browser will be installed later."
        )
    print(f"Supported browser found: {display_path(Path(browser))}", flush=True)


def backup_path(skills_dir: Path, name: str) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backups_dir = skills_dir / ".backups"
    candidate = backups_dir / f"{name}-{stamp}"
    suffix = 1
    while candidate.exists() or candidate.is_symlink():
        suffix += 1
        candidate = backups_dir / f"{name}-{stamp}-{suffix}"
    return candidate


def disable_backup_skill_marker(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        return
    marker = path / "SKILL.md"
    if marker.exists():
        marker.rename(path / "SKILL.md.disabled")


def move_to_hidden_backup(path: Path, skills_dir: Path, dry_run: bool) -> Path:
    backup = backup_path(skills_dir, path.name)
    if dry_run:
        print(f"Would move existing install to hidden backup: {display_path(path)} -> {display_path(backup)}", flush=True)
        return backup
    backup.parent.mkdir(parents=True, exist_ok=True)
    path.rename(backup)
    disable_backup_skill_marker(backup)
    print(f"Existing install moved to hidden backup: {display_path(backup)}", flush=True)
    return backup


def restore_state_from_backup(backup: Path | None, target: Path) -> None:
    if not backup:
        return
    state_dir = backup / ".state"
    if not state_dir.exists() or not state_dir.is_dir():
        return
    shutil.copytree(state_dir, target / ".state", dirs_exist_ok=True)
    print(f"Preserved existing state: {display_path(target / '.state')}", flush=True)


def cleanup_legacy_installs(skills_dir: Path, dry_run: bool) -> None:
    for legacy_name in ("twitter-briefing", "twitter-briefing.bak"):
        legacy = skills_dir / legacy_name
        if legacy.exists() or legacy.is_symlink():
            move_to_hidden_backup(legacy, skills_dir, dry_run)


def install_skill(root: Path, skills_dir: Path, copy: bool, dry_run: bool) -> Path:
    target = skills_dir / root.name
    if dry_run:
        action = "copy" if copy else "symlink"
        cleanup_legacy_installs(skills_dir, dry_run=True)
        if target.exists() or target.is_symlink():
            backup = move_to_hidden_backup(target, skills_dir, dry_run=True)
            if copy and (target / ".state").exists():
                print(f"Would preserve existing state from: {display_path(backup / '.state')}", flush=True)
        print(f"Would {action} skill to: {display_path(target)}", flush=True)
        return target
    skills_dir.mkdir(parents=True, exist_ok=True)
    cleanup_legacy_installs(skills_dir, dry_run=False)
    existing_backup: Path | None = None
    if target.is_symlink() or target.exists():
        if target.is_symlink() and target.resolve() == root and not copy:
            print(f"Skill already installed: {display_path(target)}", flush=True)
            return target
        existing_backup = move_to_hidden_backup(target, skills_dir, dry_run=False)
    if copy:
        shutil.copytree(root, target, ignore=shutil.ignore_patterns(".state", "__pycache__", "*.pyc"))
        restore_state_from_backup(existing_backup, target)
        print(f"Copied skill to: {display_path(target)}", flush=True)
    else:
        target.symlink_to(root, target_is_directory=True)
        print(f"Linked skill: {display_path(target)}", flush=True)
    return target


def claude_bash_allow_rule(target: Path) -> str:
    script = target.expanduser() / "scripts" / "run_daily_digest.py"
    try:
        command_path = "~/" + str(script.relative_to(Path.home()))
    except ValueError:
        command_path = str(script)
    return f"Bash(python3 {command_path}:*)"


def claude_state_read_directory(target: Path) -> str:
    state_dir = target.expanduser() / ".state"
    try:
        return "~/" + str(state_dir.relative_to(Path.home()))
    except ValueError:
        return str(state_dir)


def load_claude_settings(settings_path: Path) -> dict[str, object]:
    if not settings_path.exists():
        return {}
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot update Claude Code settings because {display_path(settings_path)} is not valid JSON: {exc}") from exc
    if not isinstance(settings, dict):
        raise SystemExit(f"Cannot update Claude Code settings because {display_path(settings_path)} does not contain a JSON object.")
    return settings


def save_claude_settings(settings_path: Path, settings: dict[str, object]) -> None:
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        settings_path.chmod(0o600)
    except PermissionError:
        pass


def add_list_setting(settings: dict[str, object], key: str, value: str) -> bool:
    existing = settings.get(key)
    if existing is None:
        existing = []
        settings[key] = existing
    if not isinstance(existing, list):
        raise SystemExit(f"Cannot update Claude Code settings because {key} is not a list.")
    if value in existing:
        return False
    existing.append(value)
    return True


def add_claude_bash_allow_rule(settings: dict[str, object], rule: str) -> bool:
    permissions = settings.get("permissions")
    if not isinstance(permissions, dict):
        permissions = {}
        settings["permissions"] = permissions
    allow = permissions.get("allow")
    if allow is None:
        allow = []
        permissions["allow"] = allow
    if not isinstance(allow, list):
        raise SystemExit("Cannot update Claude Code settings because permissions.allow is not a list.")
    if rule in allow:
        return False
    allow.append(rule)
    return True


def write_claude_settings(target: Path, dry_run: bool, allow_commands: bool, allow_state_read: bool) -> None:
    settings_path = Path.home() / ".claude" / "settings.json"
    rule = claude_bash_allow_rule(target)
    state_dir = claude_state_read_directory(target)
    if dry_run:
        if allow_commands:
            print(f"Would add Claude Code Bash allow rule to {display_path(settings_path)}: {rule}", flush=True)
        if allow_state_read:
            print(f"Would add Claude Code additional directory to {display_path(settings_path)}: {state_dir}", flush=True)
        return

    settings = load_claude_settings(settings_path)
    changed = False
    if allow_commands:
        if add_claude_bash_allow_rule(settings, rule):
            changed = True
            print(f"Added Claude Code Bash allow rule: {rule}", flush=True)
        else:
            print(f"Claude Code Bash allow rule already present: {rule}", flush=True)
    if allow_state_read:
        if add_list_setting(settings, "additionalDirectories", state_dir):
            changed = True
            print(f"Added Claude Code additional directory: {state_dir}", flush=True)
        else:
            print(f"Claude Code additional directory already present: {state_dir}", flush=True)
    if changed:
        save_claude_settings(settings_path, settings)


def main() -> None:
    args = parse_args()
    check_runtime(args.skip_browser_check)
    root = skill_root()
    copy = args.copy or not args.symlink
    client = detect_client() if args.client == "auto" else args.client
    skills_dir = Path(args.skills_dir).expanduser() if args.skills_dir else default_skills_dir(client)
    print(f"Target client: {client}", flush=True)
    print(f"Target skills dir: {display_path(skills_dir)}", flush=True)
    target = install_skill(root, skills_dir, copy, args.dry_run)
    if args.allow_claude_commands or args.allow_claude_state_read:
        if client != "claude":
            print("Claude Code settings update requested, but target client is not Claude Code; skipping Claude Code settings update.", flush=True)
        else:
            write_claude_settings(target, args.dry_run, args.allow_claude_commands, args.allow_claude_state_read)
    if not args.dry_run:
        print(f"Installed skill path: {display_path(target)}", flush=True)


if __name__ == "__main__":
    main()
