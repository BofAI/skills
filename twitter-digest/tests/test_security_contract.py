from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import configure_api  # noqa: E402
import configure_all  # noqa: E402
import install  # noqa: E402
import run_daily_digest  # noqa: E402
import script_utils  # noqa: E402


class SecurityContractTests(unittest.TestCase):
    def test_default_oauth_scopes_are_read_only(self) -> None:
        scopes = set(configure_api.DEFAULT_SCOPES.split())
        self.assertIn("dm.read", scopes)
        self.assertFalse(any(scope.endswith(".write") for scope in scopes))

    def test_collectors_do_not_require_dm_write(self) -> None:
        self.assertNotIn("dm.write", configure_all.REQUIRED_CHAT_SCOPES)
        self.assertNotIn("dm.write", run_daily_digest.REQUIRED_CHAT_SCOPES)

    def test_claude_can_read_only_generated_run_output(self) -> None:
        target = Path.home() / ".claude" / "skills" / "twitter-digest"
        directory = install.claude_state_read_directory(target)
        self.assertTrue(directory.endswith("/.state/run"))
        self.assertFalse(directory.endswith("/.state"))

    def test_installed_claude_script_does_not_redirect_to_codex(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            codex = base / ".codex" / "skills" / "twitter-digest"
            claude = base / ".claude" / "skills" / "twitter-digest"
            script = claude / "scripts" / "configure_all.py"
            (codex / "scripts").mkdir(parents=True)
            script.parent.mkdir(parents=True)
            script.touch()
            with mock.patch.object(script_utils, "installed_skill_roots", return_value=[codex, claude]):
                script_utils.rerun_from_installed_if_needed(str(script))


if __name__ == "__main__":
    unittest.main()
