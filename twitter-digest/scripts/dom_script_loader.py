"""Load browser-side DOM extraction scripts."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


DOM_SCRIPT_DIR = Path(__file__).with_name("dom_scripts")


@lru_cache(maxsize=64)
def load_dom_script(name: str) -> str:
    path = DOM_SCRIPT_DIR / name
    return path.read_text(encoding="utf-8")
