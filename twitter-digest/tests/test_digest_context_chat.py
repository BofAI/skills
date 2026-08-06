from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import digest_context  # noqa: E402


class DigestContextChatTests(unittest.TestCase):
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
        self.assertTrue(facts["dms"]["threads"][0]["requires_user_ui"])
        chat_gaps = [gap for gap in facts["data_gaps"] if gap.get("source") == "x_chat"]
        self.assertEqual(len(chat_gaps), 1)
        self.assertEqual(chat_gaps[0]["status"], "conversation_history_unavailable")
        dm_context = digest_context.render_context_slice(summary, facts, "dm")
        self.assertIn("## 需要你在 X 界面操作", dm_context)
        self.assertIn("X → 消息 → 请求", dm_context)
        self.assertIn("状态未知会话 @peer", dm_context)
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


if __name__ == "__main__":
    unittest.main()
