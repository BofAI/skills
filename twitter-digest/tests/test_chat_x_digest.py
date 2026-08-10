from __future__ import annotations

import datetime as dt
import io
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import chat_x_digest  # noqa: E402


class ChatCollectorTests(unittest.TestCase):
    def test_api_get_retries_transient_url_error(self) -> None:
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{"data": []}'
        with (
            mock.patch.object(
                chat_x_digest.urllib.request,
                "urlopen",
                side_effect=[urllib.error.URLError("TLS EOF"), response],
            ) as urlopen,
            mock.patch.object(chat_x_digest.time, "sleep") as sleep,
        ):
            payload = chat_x_digest.api_get("token", "/chat/conversations")

        self.assertEqual(payload, {"data": []})
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_api_get_stops_immediately_on_429_and_reports_retry_after(self) -> None:
        error = urllib.error.HTTPError(
            "https://api.x.com/2/chat/conversations",
            429,
            "Too Many Requests",
            {"Retry-After": "3"},
            io.BytesIO(b"rate limited"),
        )
        with (
            mock.patch.object(chat_x_digest.urllib.request, "urlopen", side_effect=error) as urlopen,
            mock.patch.object(chat_x_digest.time, "sleep") as sleep,
        ):
            with self.assertRaisesRegex(chat_x_digest.RateLimitError, "retry after about 3 seconds"):
                chat_x_digest.api_get("token", "/chat/conversations")

        self.assertEqual(urlopen.call_count, 1)
        sleep.assert_not_called()

    def test_active_conversations_filters_old_threads_before_key_lookup(self) -> None:
        cutoff = dt.datetime(2026, 8, 10, 0, tzinfo=dt.timezone.utc)
        conversations = [
            {"id": "new", "updated_at": "2026-08-10T01:00:00Z"},
            {"id": "old", "updated_at": "2026-08-09T01:00:00Z"},
            {"id": "unknown"},
        ]
        active = chat_x_digest.active_conversations(conversations, cutoff)
        self.assertEqual([item["id"] for item in active], ["new", "unknown"])

    def test_collect_conversations_follows_pagination_and_keeps_request_flag(self) -> None:
        responses = [
            {
                "data": [{"id": "one", "participant_ids": ["2"]}],
                "includes": {"users": [{"id": "2", "username": "two"}]},
                "meta": {"next_token": "next", "has_message_requests": True},
            },
            {
                "data": [{"id": "three", "participant_ids": ["3"]}],
                "meta": {"has_message_requests": False},
            },
        ]
        with mock.patch.object(chat_x_digest, "api_get", side_effect=responses) as api_get:
            conversations, users, has_requests = chat_x_digest.collect_conversations("token", 50)

        self.assertEqual([item["id"] for item in conversations], ["one", "three"])
        self.assertEqual(users["2"]["username"], "two")
        self.assertTrue(has_requests)
        self.assertEqual(api_get.call_count, 2)
        self.assertEqual(api_get.call_args_list[1].args[2]["pagination_token"], "next")

    def test_collect_events_stops_after_page_older_than_cutoff(self) -> None:
        cutoff = dt.datetime(2026, 8, 2, 12, tzinfo=dt.timezone.utc)
        responses = [
            {
                "data": [{"id": "new", "created_at": "2026-08-03T01:00:00Z"}],
                "meta": {"next_token": "older", "conversation_key_events": ["key"]},
            },
            {
                "data": [{"id": "old", "created_at": "2026-08-01T01:00:00Z"}],
                "meta": {"next_token": "unused"},
            },
        ]
        with mock.patch.object(chat_x_digest, "api_get", side_effect=responses) as api_get:
            events, keys = chat_x_digest.collect_events("token", "conversation", cutoff)

        self.assertEqual([item["id"] for item in events], ["new", "old"])
        self.assertEqual(keys, ["key"])
        self.assertEqual(api_get.call_count, 2)

    def test_unavailable_thread_never_claims_reply_state(self) -> None:
        thread = chat_x_digest.unavailable_thread(
            {"id": "1-2", "participant_ids": ["2"]},
            {"2": {"id": "2", "username": "peer"}},
            "1",
            "history_unavailable",
            "No events returned.",
        )

        self.assertIsNone(thread["replied"])
        self.assertEqual(thread["reply_state"], "unknown")
        self.assertFalse(thread["dm_load_complete"])
        self.assertEqual(thread["participant"], "@peer")
        self.assertTrue(thread["requires_user_ui"])
        self.assertIn("X 界面", thread["user_action"])

    def test_parse_time_normalizes_naive_values_to_utc(self) -> None:
        parsed = chat_x_digest.parse_time("2026-08-03T10:00:00")
        self.assertEqual(parsed, dt.datetime(2026, 8, 3, 10, tzinfo=dt.timezone.utc))


if __name__ == "__main__":
    unittest.main()
