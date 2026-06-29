"""Small shared utilities for twitter-digest scripts."""

from __future__ import annotations

import datetime as dt
from pathlib import Path


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
