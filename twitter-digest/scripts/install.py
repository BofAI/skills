#!/usr/bin/env python3
"""Install twitter-digest into a local Claude Code skills directory."""

from __future__ import annotations

import argparse
import datetime as dt
import shutil as shutil_module
import shutil
import sys
from pathlib import Path

from script_utils import display_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", default=str(Path.home() / ".claude" / "skills"))
    parser.add_argument("--copy", action="store_true", help="Copy files instead of creating a symlink. This is the default.")
    parser.add_argument("--symlink", action="store_true", help="Install as a symlink for local skill development.")
    parser.add_argument("--skip-browser-check", action="store_true", help="Skip checking for a supported Chromium browser.")
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


def move_to_hidden_backup(path: Path, skills_dir: Path, dry_run: bool) -> None:
    backup = backup_path(skills_dir, path.name)
    if dry_run:
        print(f"Would move existing install to hidden backup: {display_path(path)} -> {display_path(backup)}", flush=True)
        return
    backup.parent.mkdir(parents=True, exist_ok=True)
    path.rename(backup)
    disable_backup_skill_marker(backup)
    print(f"Existing install moved to hidden backup: {display_path(backup)}", flush=True)


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
            move_to_hidden_backup(target, skills_dir, dry_run=True)
        print(f"Would {action} skill to: {display_path(target)}", flush=True)
        return target
    skills_dir.mkdir(parents=True, exist_ok=True)
    cleanup_legacy_installs(skills_dir, dry_run=False)
    if target.is_symlink() or target.exists():
        if target.is_symlink() and target.resolve() == root and not copy:
            print(f"Skill already installed: {display_path(target)}", flush=True)
            return target
        move_to_hidden_backup(target, skills_dir, dry_run=False)
    if copy:
        shutil.copytree(root, target, ignore=shutil.ignore_patterns(".state", "__pycache__", "*.pyc"))
        print(f"Copied skill to: {display_path(target)}", flush=True)
    else:
        target.symlink_to(root, target_is_directory=True)
        print(f"Linked skill: {display_path(target)}", flush=True)
    return target


def main() -> None:
    args = parse_args()
    check_runtime(args.skip_browser_check)
    root = skill_root()
    copy = args.copy or not args.symlink
    target = install_skill(root, Path(args.skills_dir).expanduser(), copy, args.dry_run)
    if not args.dry_run:
        print(f"Installed skill path: {display_path(target)}", flush=True)


if __name__ == "__main__":
    main()
