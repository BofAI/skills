from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import digest_context  # noqa: E402
import digest_io  # noqa: E402


class DigestContextChatTests(unittest.TestCase):
    def test_missing_or_null_dm_reply_state_is_unknown(self) -> None:
        normalizer = getattr(digest_context, "normalize_dm_reply_state", None)
        self.assertIsNotNone(normalizer)
        self.assertEqual(normalizer({}), "unknown")
        self.assertEqual(normalizer({"replied": None}), "unknown")

    def test_legacy_boolean_dm_reply_state_is_supported(self) -> None:
        normalizer = getattr(digest_context, "normalize_dm_reply_state", None)
        self.assertIsNotNone(normalizer)
        self.assertEqual(normalizer({"replied": True}), "last_from_me")
        self.assertEqual(normalizer({"replied": False}), "waiting_reply")

    def test_raw_renderers_do_not_default_missing_dm_state_to_waiting(self) -> None:
        data = {
            "generated_at": "2026-08-10T16:20:16+08:00",
            "source": "api",
            "handle": "owner",
            "pages": [
                {
                    "kind": "messages",
                    "url": "https://api.x.com/2/chat/conversations",
                    "items": [],
                    "dm_status": "x_chat_collected",
                    "dm_threads": [{"participant": "@peer", "text": "hello"}],
                }
            ],
        }

        context_markdown = digest_context.render_digest_input(data)
        io_markdown = digest_io.render_markdown(data)

        self.assertIn("会话状态: `unknown`", context_markdown)
        self.assertIn("会话状态: `unknown`", io_markdown)
        self.assertNotIn("会话状态: `等我回复`", context_markdown)
        self.assertNotIn("会话状态: `等我回复`", io_markdown)

    def test_unverified_message_request_signal_is_not_shown_as_current_todo(self) -> None:
        page = {
            "kind": "messages",
            "url": "https://api.x.com/2/chat/conversations",
            "items": [],
            "dm_status": "x_chat_collected",
            "dm_has_message_requests": True,
            "todo_items": [
                {
                    "source": "x_chat",
                    "status": "message_request_pending",
                    "detail": "Legacy collector claimed a current request.",
                    "requires_user_ui": True,
                    "user_action": "Open X to confirm.",
                    "action_url": "https://x.com/messages",
                }
            ],
        }
        data = {
            "generated_at": "2026-08-10T16:20:16+08:00",
            "source": "api",
            "handle": "owner",
            "pages": [page],
        }

        summary = digest_context.summarize_current_run(data)
        facts = digest_context.build_digest_facts(data, summary)
        context = digest_context.render_context_slice(summary, facts, "dm")
        raw_markdown = digest_io.render_markdown(data)

        self.assertNotIn("message_requests", summary["dm_counts"])
        self.assertEqual(facts["todo_items"], [])
        self.assertNotIn("消息请求", context)
        self.assertNotIn("message request", context.lower())
        self.assertNotIn("Chat 请求", raw_markdown)

    def test_verified_manual_action_uses_generic_label(self) -> None:
        facts = {
            "dms": {"counts": {}, "threads": []},
            "todo_items": [
                {
                    "source": "x_chat",
                    "status": "verified_manual_action",
                    "detail": "A verified action needs the X interface.",
                    "requires_user_ui": True,
                    "user_action": "请在 X 中完成操作。",
                    "action_url": "https://x.com/messages",
                }
            ],
        }

        context = digest_context.render_dm_facts_section(facts)

        self.assertIn("**X 界面操作**", context)
        self.assertNotIn("X Chat 消息请求", context)

    def test_unknown_chat_thread_remains_unknown_and_adds_gap(self) -> None:
        data = {
            "generated_at": "2026-08-03T12:00:00+08:00",
            "source": "api",
            "handle": "owner",
            "pages": [
                {
                    "kind": "messages",
                    "dm_status": "x_chat_collected",
                    "dm_window_hours": 168,
                    "dm_visible_thread_count": 1,
                    "dm_unknown_thread_count": 1,
                    "dm_threads": [
                        {
                            "participant": "@peer",
                            "reply_state": "unknown",
                            "replied": None,
                            "message_count": 0,
                            "collection_status": "history_unavailable",
                            "collection_detail": "No history returned.",
                            "requires_user_ui": True,
                            "user_action": "请打开 X 会话手动确认。",
                            "dm_load_complete": False,
                        }
                    ],
                    "data_gaps": [
                        {
                            "source": "x_chat",
                            "status": "conversation_history_unavailable",
                            "detail": "One conversation was unreadable.",
                            "requires_user_ui": True,
                            "user_action": "请在 X → 消息中确认。",
                            "action_url": "https://x.com/messages",
                        }
                    ],
                    "todo_items": [
                        {
                            "source": "x_chat",
                            "status": "message_request_pending",
                            "detail": "A request exists but its sender is unavailable.",
                            "requires_user_ui": True,
                            "user_action": "打开 X → 消息 → 请求后自行处理。",
                            "action_url": "https://x.com/messages",
                        }
                    ],
                }
            ],
        }
        summary = digest_context.summarize_current_run(data)
        facts = digest_context.build_digest_facts(data, summary)

        self.assertEqual(summary["dm_counts"]["unknown"], 1)
        self.assertEqual(summary["dm_window_hours"], 168)
        self.assertEqual(facts["run"]["window_hours"], 24)
        self.assertEqual(facts["dms"]["window_hours"], 168)
        self.assertEqual(facts["dms"]["threads"][0]["reply_state"], "unknown")
        self.assertFalse(facts["dms"]["threads"][0]["should_summarize"])
        self.assertEqual(facts["dms"]["threads"][0]["noise_reason"], "collection_state_unknown")
        self.assertFalse(facts["dms"]["threads"][0]["requires_user_ui"])
        self.assertEqual(facts["dms"]["threads"][0]["user_action"], "")
        chat_gaps = [gap for gap in facts["data_gaps"] if gap.get("source") == "x_chat"]
        self.assertEqual(len(chat_gaps), 1)
        self.assertEqual(chat_gaps[0]["status"], "conversation_history_unavailable")
        dm_context = digest_context.render_context_slice(summary, facts, "dm")
        self.assertNotIn("## 需要你在 X 界面操作", dm_context)
        self.assertNotIn("X → 消息 → 请求", dm_context)
        self.assertIn("曾经收到过消息：@peer", dm_context)
        self.assertNotIn("状态未知会话 @peer", dm_context)
        self.assertNotIn("请打开 X 会话手动确认", dm_context)
        self.assertIn("One conversation was unreadable.", dm_context)

    def test_context_outputs_are_owner_only(self) -> None:
        data = {"generated_at": "2026-08-03T12:00:00+08:00", "source": "api", "pages": []}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "digest-input.json"
            markdown_path = root / "digest-input.md"
            input_path.write_text("{}")
            digest_context.build_current_context_from_file(input_path, root, markdown_path)
            for path in root.glob("digest-*"):
                self.assertEqual(path.stat().st_mode & 0o777, 0o600, path.name)

    def test_historical_senders_are_deduplicated_and_listed_without_actions(self) -> None:
        facts = {
            "dms": {
                "threads": [
                    {"participant": "@alice", "reply_state": "unknown", "requires_user_ui": True},
                    {"participant": "@bob", "reply_state": "unknown", "requires_user_ui": True},
                    {"participant": "@alice", "reply_state": "unknown", "requires_user_ui": True},
                ]
            }
        }
        rendered = digest_context.render_dm_facts_section(facts)
        self.assertIn("曾经收到过消息：@alice、@bob", rendered)
        self.assertNotIn("状态未知会话", rendered)
        self.assertNotIn("请在 X 界面检查", rendered)

    def test_safe_scan_limit_uses_friendly_checked_count(self) -> None:
        data = {
            "generated_at": "2026-08-10T12:00:00+08:00",
            "source": "api",
            "handle": "owner",
            "pages": [
                {
                    "kind": "messages",
                    "dm_status": "x_chat_collected",
                    "dm_listed_conversation_count": 50,
                    "dm_scanned_conversation_count": 4,
                    "dm_event_request_count": 4,
                    "dm_api_request_counts": {
                        "conversation_list": 1,
                        "conversation_events": 5,
                        "public_keys": 2,
                    },
                    "dm_scan_complete": False,
                    "dm_scan_stop_reason": "consecutive_old_conversations",
                    "dm_threads": [],
                    "data_gaps": [
                        {
                            "source": "x_chat",
                            "status": "safe_scan_limited",
                            "detail": "Stopped safely.",
                        }
                    ],
                }
            ],
        }
        summary = digest_context.summarize_current_run(data)
        facts = digest_context.build_digest_facts(data, summary)
        rendered = digest_context.render_context_slice(summary, facts, "dm")
        self.assertIn("X Chat 已按 X 返回顺序检查 4 个会话", rendered)
        self.assertNotIn("最近的 4 个会话", rendered)
        self.assertIn("checked `4`", rendered)
        self.assertFalse(facts["dms"]["scan"]["complete"])
        self.assertEqual(
            facts["dms"]["scan"]["api_request_counts"],
            {"conversation_list": 1, "conversation_events": 5, "public_keys": 2},
        )
        self.assertIn("HTTP attempts", rendered)


if __name__ == "__main__":
    unittest.main()
