from __future__ import annotations

import sys
import subprocess
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

    def test_saved_default_config_is_owner_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / ".state" / "config.json"
            with mock.patch.object(run_daily_digest, "CONFIG_PATH", config_path):
                run_daily_digest.save_config("owner", "Owner")
            self.assertEqual(config_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(config_path.parent.stat().st_mode & 0o777, 0o700)

    def test_copy_install_excludes_development_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "twitter-digest"
            (source / "scripts").mkdir(parents=True)
            (source / "tests").mkdir()
            (source / "SKILL.md").write_text("skill", encoding="utf-8")
            (source / "README.md").write_text("docs", encoding="utf-8")
            (source / "tests" / "test_sample.py").write_text("", encoding="utf-8")
            (source / "scripts" / "run.py").write_text("", encoding="utf-8")
            target = install.install_skill(source, base / "installed", copy=True, dry_run=False)
            self.assertTrue((target / "SKILL.md").exists())
            self.assertTrue((target / "scripts" / "run.py").exists())
            self.assertFalse((target / "README.md").exists())
            self.assertFalse((target / "tests").exists())

    def test_failed_chat_retry_reuses_matching_recent_public_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out_dir = Path(directory)
            signature = {"user_id": "1", "public_window_hours": 24}
            (out_dir / "digest-input.json").write_text("{}", encoding="utf-8")
            with mock.patch.object(run_daily_digest.time, "time", return_value=1000):
                run_daily_digest.mark_chat_retry(out_dir, signature)
            self.assertTrue(run_daily_digest.can_resume_public_collection(out_dir, signature, now=1100))
            self.assertFalse(run_daily_digest.can_resume_public_collection(out_dir, signature, now=2000))
            self.assertFalse(run_daily_digest.can_resume_public_collection(out_dir, {"user_id": "2"}, now=1100))

    def test_x_chat_401_is_retried_only_once(self) -> None:
        error = subprocess.CalledProcessError(
            1,
            ["chat"],
            output="",
            stderr="GET /chat/conversations failed with HTTP 401: Unauthorized",
        )
        success = mock.Mock(stdout="", stderr="")
        with (
            mock.patch.object(run_daily_digest.subprocess, "run", side_effect=[error, success]) as run,
            mock.patch.object(run_daily_digest.time, "sleep") as sleep,
        ):
            run_daily_digest.run_chat_command(["chat"], {})

        self.assertEqual(run.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_x_chat_non_auth_failure_is_not_retried(self) -> None:
        error = subprocess.CalledProcessError(1, ["chat"], output="", stderr="HTTP 429 Too Many Requests")
        with mock.patch.object(run_daily_digest.subprocess, "run", side_effect=error) as run:
            with self.assertRaises(run_daily_digest.ChatCollectionError):
                run_daily_digest.run_chat_command(["chat"], {})
        self.assertEqual(run.call_count, 1)


if __name__ == "__main__":
    unittest.main()
