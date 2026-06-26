#!/usr/bin/env python3
"""Install twitter-digest into a local Claude Code skills directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", default=str(Path.home() / ".claude" / "skills"))
    parser.add_argument("--copy", action="store_true", help="Copy files instead of creating a symlink. This is the default.")
    parser.add_argument("--symlink", action="store_true", help="Install as a symlink for local skill development.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def display_path(path: Path) -> str:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        expanded = Path.cwd() / expanded
    try:
        return "~/" + str(expanded.relative_to(Path.home()))
    except ValueError:
        return str(expanded)


def install_skill(root: Path, skills_dir: Path, copy: bool, dry_run: bool) -> Path:
    target = skills_dir / root.name
    if dry_run:
        action = "copy" if copy else "symlink"
        print(f"Would {action} skill to: {display_path(target)}", flush=True)
        return target
    skills_dir.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or target.exists():
        if target.is_symlink() and target.resolve() == root and not copy:
            print(f"Skill already installed: {display_path(target)}", flush=True)
            return target
        backup = target.with_name(target.name + ".bak")
        if backup.exists() or backup.is_symlink():
            if backup.is_dir() and not backup.is_symlink():
                shutil.rmtree(backup)
            else:
                backup.unlink()
        target.rename(backup)
        print(f"Existing install moved to: {display_path(backup)}", flush=True)
    if copy:
        shutil.copytree(root, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        print(f"Copied skill to: {display_path(target)}", flush=True)
    else:
        target.symlink_to(root, target_is_directory=True)
        print(f"Linked skill: {display_path(target)}", flush=True)
    return target


def main() -> None:
    args = parse_args()
    root = skill_root()
    copy = args.copy or not args.symlink
    target = install_skill(root, Path(args.skills_dir).expanduser(), copy, args.dry_run)
    if not args.dry_run:
        print(f"Installed skill path: {display_path(target)}", flush=True)


if __name__ == "__main__":
    main()
