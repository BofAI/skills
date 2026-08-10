from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import chat_rate_limit_store  # noqa: E402


class ChatRateLimitStoreTests(unittest.TestCase):
    def paths(self, directory: str):
        root = Path(directory)
        return (
            mock.patch.object(chat_rate_limit_store, "CHAT_STATE_DIR", root),
            mock.patch.object(chat_rate_limit_store, "RATE_LIMIT_PATH", root / "rate_limits.json"),
        )

    def test_records_remaining_cooldown_and_removes_expired_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_patch, path_patch = self.paths(directory)
            with state_patch, path_patch:
                chat_rate_limit_store.record_rate_limit("conversation_events", 90, now=1000)
                self.assertEqual(chat_rate_limit_store.active_rate_limit("conversation_events", now=1030), 60)
                self.assertIsNone(chat_rate_limit_store.active_rate_limit("conversation_events", now=1091))
                self.assertFalse(chat_rate_limit_store.RATE_LIMIT_PATH.exists())

    def test_unknown_reset_and_invalid_endpoint_are_not_saved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_patch, path_patch = self.paths(directory)
            with state_patch, path_patch:
                chat_rate_limit_store.record_rate_limit("conversation_events", None, now=1000)
                chat_rate_limit_store.record_rate_limit("/secret/path", 90, now=1000)
                self.assertFalse(chat_rate_limit_store.RATE_LIMIT_PATH.exists())

    def test_state_is_owner_only_and_contains_only_sanitized_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_patch, path_patch = self.paths(directory)
            with state_patch, path_patch:
                chat_rate_limit_store.record_rate_limit("public_keys", 90, now=1000)
                data = json.loads(chat_rate_limit_store.RATE_LIMIT_PATH.read_text(encoding="utf-8"))
                self.assertEqual(set(data["public_keys"]), {"endpoint", "retry_after_epoch"})
                self.assertEqual(data["public_keys"]["endpoint"], "public_keys")
                self.assertEqual(chat_rate_limit_store.RATE_LIMIT_PATH.stat().st_mode & 0o777, 0o600)
                self.assertEqual(chat_rate_limit_store.CHAT_STATE_DIR.stat().st_mode & 0o777, 0o700)


if __name__ == "__main__":
    unittest.main()
