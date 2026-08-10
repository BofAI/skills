from __future__ import annotations

import os
import sys
import io
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
    def run_shell_installer_args(self, configure_after_install: str | None = None) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fake_bin = base / "bin"
            fake_bin.mkdir()
            capture = base / "python-args.txt"
            fake_git = fake_bin / "git"
            fake_git.write_text(
                "#!/bin/sh\n"
                "for argument in \"$@\"; do clone_dir=\"$argument\"; done\n"
                "mkdir -p \"$clone_dir/twitter-digest/scripts\"\n"
                ": > \"$clone_dir/twitter-digest/scripts/install.py\"\n",
                encoding="utf-8",
            )
            fake_python = fake_bin / "python3"
            fake_python.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' \"$@\" > \"$TWITTER_DIGEST_TEST_CAPTURE\"\n",
                encoding="utf-8",
            )
            fake_git.chmod(0o700)
            fake_python.chmod(0o700)
            env = dict(os.environ)
            env["PATH"] = f"{fake_bin}{os.pathsep}{os.defpath}"
            env["TWITTER_DIGEST_OPEN_TERMINAL"] = "0"
            env["TWITTER_DIGEST_TEST_CAPTURE"] = str(capture)
            if configure_after_install is not None:
                env["TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL"] = configure_after_install

            subprocess.run(
                ["/bin/sh", str(SCRIPTS.parent / "install.sh")],
                check=True,
                env=env,
                capture_output=True,
                text=True,
            )

            return capture.read_text(encoding="utf-8").splitlines()

    def capture_terminal_installer_command(self, configure_after_install: str) -> str:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fake_bin = base / "bin"
            fake_bin.mkdir()
            capture = base / "terminal-command.txt"
            fake_osascript = fake_bin / "osascript"
            fake_osascript.write_text(
                "#!/bin/sh\n"
                "cat > \"$TWITTER_DIGEST_TEST_CAPTURE\"\n",
                encoding="utf-8",
            )
            fake_osascript.chmod(0o700)
            env = dict(os.environ)
            env["PATH"] = f"{fake_bin}{os.pathsep}{os.defpath}"
            env["TWITTER_DIGEST_OPEN_TERMINAL"] = "1"
            env["TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL"] = configure_after_install
            env["TWITTER_DIGEST_TEST_CAPTURE"] = str(capture)

            subprocess.run(
                ["/bin/sh", str(SCRIPTS.parent / "install.sh")],
                check=True,
                env=env,
                capture_output=True,
                text=True,
            )

            return capture.read_text(encoding="utf-8")

    def test_chat_scan_profiles_are_bounded_and_seven_days_expands(self) -> None:
        self.assertEqual(
            run_daily_digest.chat_scan_profile("recent", 24),
            {"max_conversations": 10, "event_requests": 10, "event_pages": 1},
        )
        self.assertEqual(
            run_daily_digest.chat_scan_profile("more", 24),
            {"max_conversations": 50, "event_requests": 20, "event_pages": 3},
        )
        self.assertEqual(run_daily_digest.chat_scan_profile("recent", 168)["max_conversations"], 50)

    def test_chat_collector_command_passes_selected_profile(self) -> None:
        command = run_daily_digest.chat_collector_command(
            Path("/python"), Path("/chat.py"), Path("/out.json"), 24, "recent"
        )
        self.assertEqual(command[-6:], ["--max-conversations", "10", "--max-event-requests", "10", "--max-event-pages", "1"])
    def test_beta13_installer_and_docs_are_pinned(self) -> None:
        root = SCRIPTS.parent
        self.assertIn("v1.5.14-beta.13", (root / "install.sh").read_text(encoding="utf-8"))
        self.assertIn("v1.5.14-beta.13", (root / "README.md").read_text(encoding="utf-8"))

    def test_skill_requires_friendly_private_rate_limit_messages(self) -> None:
        skill = (SCRIPTS.parent / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("X Chat 消息读取暂时受到限流", skill)
        self.assertIn("Never expose a concrete conversation ID", skill)

    def test_skill_permanently_forbids_reply_content(self) -> None:
        root = SCRIPTS.parent
        skill = (root / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("不得生成、推荐或改写任何回复内容", skill)
        self.assertNotIn("建议回复草稿", skill)
        for path in (root / "agents" / "openai.yaml", root / "references" / "x-twitter-digest.md"):
            guidance = path.read_text(encoding="utf-8")
            self.assertNotIn("建议回复草稿", guidance)
            self.assertNotIn("最近的 N 个会话", guidance)

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

    def test_unified_configuration_child_failure_has_no_python_traceback(self) -> None:
        failed = mock.Mock(returncode=1)
        with mock.patch.object(configure_all.subprocess, "run", return_value=failed):
            with self.assertRaisesRegex(SystemExit, "configure_chat.py failed"):
                configure_all.run_child("configure_chat.py")

    def test_unified_configuration_pauses_cleanly_when_passcode_must_be_set_in_x(self) -> None:
        verification = {"verified": True, "user_id": "owner"}
        output = io.StringIO()
        with (
            mock.patch.object(configure_all, "api_status", return_value=(True, verification)),
            mock.patch.object(configure_all, "load_api_config", return_value={"user_id": "owner"}),
            mock.patch.object(
                configure_all,
                "chat_status",
                side_effect=[(False, "X Chat keys are not configured."), (False, "X Chat keys are not configured.")],
            ),
            mock.patch.object(configure_all, "chat_configured", return_value=False),
            mock.patch.object(configure_all, "run_child"),
            mock.patch("sys.stdout", output),
        ):
            configure_all.configure_all()

        self.assertIn("请先在 X「消息」里设置 passcode", output.getvalue())
        self.assertNotIn('"configured": true', output.getvalue().lower())

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

    def test_post_install_configuration_runs_the_installed_unified_wizard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "twitter-digest"
            script = target / "scripts" / "configure_all.py"
            marker = target / "configured.marker"
            script.parent.mkdir(parents=True)
            script.write_text(
                "from pathlib import Path\n"
                "Path(__file__).resolve().parents[1].joinpath('configured.marker').write_text('configured')\n",
                encoding="utf-8",
            )

            install.run_post_install_configuration(target, "codex", True, False, False)

            self.assertEqual(marker.read_text(encoding="utf-8"), "configured")

    def test_post_install_configuration_skips_nonstandard_installs(self) -> None:
        for enabled, custom_skills_dir, dry_run in (
            (False, False, False),
            (True, True, False),
            (True, False, True),
        ):
            with self.subTest(enabled=enabled, custom_skills_dir=custom_skills_dir, dry_run=dry_run):
                with tempfile.TemporaryDirectory() as directory:
                    target = Path(directory) / "twitter-digest"
                    script = target / "scripts" / "configure_all.py"
                    marker = target / "configured.marker"
                    script.parent.mkdir(parents=True)
                    script.write_text(
                        "from pathlib import Path\n"
                        "Path(__file__).resolve().parents[1].joinpath('configured.marker').write_text('configured')\n",
                        encoding="utf-8",
                    )

                    install.run_post_install_configuration(
                        target,
                        "codex",
                        enabled,
                        custom_skills_dir,
                        dry_run,
                    )

                    self.assertFalse(marker.exists())

    def test_post_install_configuration_failure_keeps_installed_skill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "twitter-digest"
            script = target / "scripts" / "configure_all.py"
            script.parent.mkdir(parents=True)
            script.write_text("raise SystemExit(7)\n", encoding="utf-8")
            (target / "SKILL.md").write_text("installed", encoding="utf-8")

            with self.assertRaises(SystemExit) as raised:
                install.run_post_install_configuration(target, "codex", True, False, False)

            self.assertTrue((target / "SKILL.md").exists())
            self.assertIn("The Skill remains installed", str(raised.exception))
            self.assertIn("run_daily_digest.py --configure", str(raised.exception))
            self.assertNotIn("Traceback", str(raised.exception))

    def test_shell_installer_enables_post_install_configuration_by_default(self) -> None:
        args = self.run_shell_installer_args()

        self.assertIn("--configure-after-install", args)

    def test_shell_installer_allows_post_install_configuration_opt_out(self) -> None:
        args = self.run_shell_installer_args("0")

        self.assertNotIn("--configure-after-install", args)

    def test_shell_installer_forwards_configuration_choice_to_terminal_child(self) -> None:
        terminal_command = self.capture_terminal_installer_command("0")

        self.assertIn("TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL='0'", terminal_command)

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

    def test_x_chat_401_fails_once_with_reconfiguration_guidance(self) -> None:
        error = subprocess.CalledProcessError(
            1,
            ["chat"],
            output="",
            stderr="GET /chat/conversations failed with HTTP 401: Unauthorized",
        )
        with (
            mock.patch.object(run_daily_digest.subprocess, "run", side_effect=error) as run,
            self.assertRaises(run_daily_digest.ChatCollectionError) as raised,
        ):
            run_daily_digest.run_chat_command(["chat"], {})

        self.assertEqual(run.call_count, 1)
        self.assertEqual(str(raised.exception), "X Chat 授权已失效。请运行统一配置后重新生成日报。")
        self.assertNotIn("/chat/conversations", str(raised.exception))
        self.assertEqual(
            run_daily_digest.format_chat_collection_failure(str(raised.exception)),
            "X Chat 授权已失效。请运行统一配置后重新生成日报。",
        )

    def test_x_chat_non_auth_failure_is_not_retried(self) -> None:
        error = subprocess.CalledProcessError(1, ["chat"], output="", stderr="HTTP 429 Too Many Requests")
        with mock.patch.object(run_daily_digest.subprocess, "run", side_effect=error) as run:
            with self.assertRaises(run_daily_digest.ChatCollectionError):
                run_daily_digest.run_chat_command(["chat"], {})
        self.assertEqual(run.call_count, 1)

    def test_friendly_chat_rate_limit_names_event_read_and_rounds_minutes(self) -> None:
        summary = (
            'TWITTER_DIGEST_API_ERROR '
            '{"source":"x_chat","endpoint":"conversation_events","status":429,'
            '"retry_after_seconds":317}'
        )
        message = run_daily_digest.friendly_chat_collection_error(summary)
        self.assertEqual(
            message,
            "X Chat 消息读取暂时受到限流，预计约 6 分钟后恢复。请稍后再生成日报。",
        )

    def test_friendly_chat_rate_limit_maps_all_categories_without_paths(self) -> None:
        expected = {
            "conversation_list": "X Chat 会话列表暂时受到限流。请稍后再生成日报。",
            "public_keys": "X Chat 公钥读取暂时受到限流。请稍后再生成日报。",
            "x_chat_other": "X Chat 接口暂时受到限流。请稍后再生成日报。",
        }
        for endpoint, message in expected.items():
            summary = (
                'TWITTER_DIGEST_API_ERROR '
                f'{{"source":"x_chat","endpoint":"{endpoint}","status":429}}'
            )
            self.assertEqual(run_daily_digest.friendly_chat_collection_error(summary), message)
            self.assertNotIn("/", message)

    def test_friendly_chat_error_keeps_legacy_summary(self) -> None:
        self.assertEqual(
            run_daily_digest.friendly_chat_collection_error("HTTP 403; Forbidden"),
            "HTTP 403; Forbidden",
        )

    def test_structured_rate_limit_failure_has_no_english_wrapper_prefix(self) -> None:
        summary = (
            'TWITTER_DIGEST_API_ERROR '
            '{"source":"x_chat","endpoint":"conversation_list","status":429}'
        )
        self.assertEqual(
            run_daily_digest.format_chat_collection_failure(summary),
            "X Chat 会话列表暂时受到限流。请稍后再生成日报。",
        )

    def test_legacy_failure_keeps_collection_context(self) -> None:
        self.assertEqual(
            run_daily_digest.format_chat_collection_failure("HTTP 403; Forbidden"),
            "X Chat collection failed; digest was not generated: HTTP 403; Forbidden",
        )


if __name__ == "__main__":
    unittest.main()
