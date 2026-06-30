#!/usr/bin/env python3
"""Validate DOM JavaScript snippets after applying runtime template values."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DOM_DIR = SCRIPT_DIR / "dom_scripts"
TEMPLATE_VALUES = {
    "dm_loaded_beyond_window.js": (24,),
    "extract_dm_messages.js": (2000,),
}


def rendered_source(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    values = TEMPLATE_VALUES.get(path.name)
    if values:
        source = source % values
    return source


def main() -> int:
    failures: list[str] = []
    for path in sorted(DOM_DIR.glob("*.js")):
        source = rendered_source(path)
        with tempfile.NamedTemporaryFile("w", suffix=f"-{path.name}", encoding="utf-8", delete=False) as tmp:
            tmp.write(source)
            tmp_path = Path(tmp.name)
        try:
            result = subprocess.run(["node", "--check", str(tmp_path)], text=True, capture_output=True)
        except FileNotFoundError:
            print("node is required to validate DOM scripts.", file=sys.stderr)
            return 2
        finally:
            try:
                tmp_path.unlink()
            except OSError:
                pass
        if result.returncode != 0:
            failures.append(f"{path}: {result.stderr.strip() or result.stdout.strip()}")
    if failures:
        print("\n\n".join(failures), file=sys.stderr)
        return 1
    print(f"Validated {len(list(DOM_DIR.glob('*.js')))} DOM scripts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
