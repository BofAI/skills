from __future__ import annotations

import datetime as dt
import io
import json
import sys
import tempfile
import types
import unittest
import urllib.error
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import chat_x_digest  # noqa: E402
from collector_commands import parse_structured_api_error  # noqa: E402


class ChatCollectorTests(unittest.TestCase):
    def setUp(self) -> None:
        chat_x_digest.RATE_LIMIT_TRACKER.clear()
        chat_x_digest.HTTP_REQUEST_COUNTS.clear()
        self.active_rate_limit = mock.patch.object(chat_x_digest, "active_rate_limit", return_value=None)
        self.record_rate_limit = mock.patch.object(chat_x_digest, "record_rate_limit")
        self.active_rate_limit.start()
        self.record_rate_limit.start()
        self.addCleanup(self.active_rate_limit.stop)
        self.addCleanup(self.record_rate_limit.stop)

    def test_default_collector_profile_is_bounded_to_ten_recent_conversations(self) -> None:
        self.assertEqual(chat_x_digest.DEFAULT_MAX_CONVERSATIONS, 10)
        self.assertEqual(chat_x_digest.DEFAULT_EVENT_REQUEST_BUDGET, 10)
        self.assertEqual(chat_x_digest.DEFAULT_MAX_EVENT_PAGES_PER_CONVERSATION, 1)

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
            with self.assertRaises(chat_x_digest.RateLimitError) as raised:
                chat_x_digest.api_get("token", "/chat/conversations")

        self.assertEqual(urlopen.call_count, 1)
        sleep.assert_not_called()
        self.assertEqual(
            parse_structured_api_error(str(raised.exception)),
            {
                "source": "x_chat",
                "endpoint": "conversation_list",
                "status": 429,
                "retry_after_seconds": 3,
            },
        )

    def test_api_get_skips_network_during_persisted_cooldown(self) -> None:
        with (
            mock.patch.object(chat_x_digest, "active_rate_limit", return_value=60),
            mock.patch.object(chat_x_digest.urllib.request, "urlopen") as urlopen,
        ):
            with self.assertRaises(chat_x_digest.RateLimitError) as raised:
                chat_x_digest.api_get("token", "/chat/conversations")

        urlopen.assert_not_called()
        self.assertEqual(parse_structured_api_error(str(raised.exception))["retry_after_seconds"], 60)

    def test_api_get_persists_http_429_cooldown(self) -> None:
        error = urllib.error.HTTPError(
            "https://api.x.com/2/chat/conversations",
            429,
            "Too Many Requests",
            {"Retry-After": "90"},
            io.BytesIO(b"limited"),
        )
        with (
            mock.patch.object(chat_x_digest, "active_rate_limit", return_value=None),
            mock.patch.object(chat_x_digest, "record_rate_limit") as record,
            mock.patch.object(chat_x_digest.urllib.request, "urlopen", side_effect=error),
        ):
            with self.assertRaises(chat_x_digest.RateLimitError):
                chat_x_digest.api_get("token", "/chat/conversations")

        record.assert_called_once_with("conversation_list", 90)

    def test_endpoint_categories_hide_resource_ids(self) -> None:
        self.assertEqual(chat_x_digest.endpoint_category("/chat/conversations"), "conversation_list")
        self.assertEqual(
            chat_x_digest.endpoint_category("/chat/conversations/secret-id/events"),
            "conversation_events",
        )
        self.assertEqual(chat_x_digest.endpoint_category("/users/secret-user/public_keys"), "public_keys")

    def test_api_get_counts_every_http_attempt_by_endpoint(self) -> None:
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{"data": []}'
        with (
            mock.patch.object(
                chat_x_digest.urllib.request,
                "urlopen",
                side_effect=[urllib.error.URLError("TLS EOF"), response],
            ),
            mock.patch.object(chat_x_digest.time, "sleep"),
        ):
            chat_x_digest.api_get("token", "/chat/conversations/secret-id/events")

        self.assertEqual(
            chat_x_digest.request_count_snapshot(),
            {"conversation_list": 0, "conversation_events": 2, "public_keys": 0},
        )

    def test_429_diagnostic_never_contains_conversation_id(self) -> None:
        error = urllib.error.HTTPError(
            "https://api.x.com/2/chat/conversations/secret-id/events",
            429,
            "Too Many Requests",
            {},
            io.BytesIO(b"secret-id also appeared in the response body"),
        )
        with mock.patch.object(chat_x_digest.urllib.request, "urlopen", side_effect=error):
            with self.assertRaises(chat_x_digest.RateLimitError) as raised:
                chat_x_digest.api_get("token", "/chat/conversations/secret-id/events")

        self.assertNotIn("secret-id", str(raised.exception))
        self.assertEqual(
            parse_structured_api_error(str(raised.exception))["endpoint"],
            "conversation_events",
        )

    def test_collect_conversations_follows_pagination_and_ignores_request_flag(self) -> None:
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
            result = chat_x_digest.collect_conversations("token", 50)

        self.assertEqual(len(result), 3)
        conversations, users, scan = result
        self.assertEqual([item["id"] for item in conversations], ["one", "three"])
        self.assertEqual(users["2"]["username"], "two")
        self.assertTrue(scan["complete"])
        self.assertEqual(scan["next_token"], "")
        self.assertEqual(scan["missing_id_count"], 0)
        self.assertEqual(scan["pages_used"], 2)
        self.assertEqual(api_get.call_count, 2)
        self.assertEqual(api_get.call_args_list[1].args[2]["pagination_token"], "next")
        self.assertEqual(
            api_get.call_args_list[0].args[2]["chat_conversation.fields"],
            "id,type,group_name,created_at",
        )

    def test_message_request_meta_is_not_written(self) -> None:
        class FakeChat:
            def import_keys(self, _private_blob: bytes, version: str) -> None:
                return None

            def set_identity(self, _user_id: str, _key_version: str) -> None:
                return None

            def set_cache_keys(self, _enabled: bool) -> None:
                return None

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "chat.json"
            with (
                mock.patch.dict(sys.modules, {"chat_xdk": types.SimpleNamespace(Chat=FakeChat)}),
                mock.patch.object(
                    chat_x_digest,
                    "load_chat_config",
                    return_value={"user_id": "me", "key_version": "1", "private_key_blob": "a2V5"},
                ),
                mock.patch.object(
                    chat_x_digest,
                    "api_get",
                    return_value={"data": [], "meta": {"has_message_requests": True}},
                ),
                mock.patch.object(sys, "argv", ["chat_x_digest.py", "--bearer-token", "token", "--out", str(output)]),
            ):
                chat_x_digest.main()

            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertNotIn("dm_has_message_requests", payload)
        self.assertEqual(payload["todo_items"], [])

    def test_collect_conversations_marks_remaining_page_incomplete_at_limit(self) -> None:
        response = {
            "data": [{"id": str(index)} for index in range(50)],
            "meta": {"next_token": "more"},
        }
        with mock.patch.object(chat_x_digest, "api_get", return_value=response):
            conversations, _users, scan = chat_x_digest.collect_conversations("token", 50)

        self.assertEqual(len(conversations), 50)
        self.assertFalse(scan["complete"])
        self.assertEqual(scan["next_token"], "more")

    def test_collect_conversations_counts_missing_ids_as_incomplete(self) -> None:
        response = {
            "data": [{"participant_ids": ["2"]}, {"id": "valid"}],
            "meta": {},
        }
        with mock.patch.object(chat_x_digest, "api_get", return_value=response):
            conversations, _users, scan = chat_x_digest.collect_conversations("token", 50)

        self.assertEqual(conversations, [{"id": "valid"}])
        self.assertFalse(scan["complete"])
        self.assertEqual(scan["missing_id_count"], 1)

    def test_collect_conversations_continues_after_one_empty_page(self) -> None:
        responses = [
            {"meta": {"next_token": "next", "has_more": True}},
            {"data": [{"id": "one"}], "meta": {"has_more": False}},
        ]
        with mock.patch.object(chat_x_digest, "api_get", side_effect=responses) as api_get:
            conversations, _users, scan = chat_x_digest.collect_conversations("token", 10)

        self.assertEqual(conversations, [{"id": "one"}])
        self.assertEqual(api_get.call_count, 2)
        self.assertTrue(scan["complete"])
        self.assertEqual(scan["empty_pages"], 1)

    def test_collect_conversations_stops_after_three_consecutive_empty_pages(self) -> None:
        responses = [
            {"meta": {"next_token": f"page-{index + 1}", "has_more": True}}
            for index in range(3)
        ]
        with mock.patch.object(chat_x_digest, "api_get", side_effect=responses) as api_get:
            conversations, _users, scan = chat_x_digest.collect_conversations("token", 10)

        self.assertEqual(conversations, [])
        self.assertEqual(api_get.call_count, 3)
        self.assertFalse(scan["complete"])
        self.assertEqual(scan["stop_reason"], "empty_page_limit")

    def test_collect_conversations_stops_on_repeated_pagination_token(self) -> None:
        responses = [
            {"data": [{"id": "one"}], "meta": {"next_token": "same", "has_more": True}},
            {"data": [{"id": "two"}], "meta": {"next_token": "same", "has_more": True}},
        ]
        with mock.patch.object(chat_x_digest, "api_get", side_effect=responses) as api_get:
            conversations, _users, scan = chat_x_digest.collect_conversations("token", 10)

        self.assertEqual([item["id"] for item in conversations], ["one", "two"])
        self.assertEqual(api_get.call_count, 2)
        self.assertFalse(scan["complete"])
        self.assertEqual(scan["stop_reason"], "repeated_pagination_token")

    def test_collect_conversations_stops_when_has_more_has_no_token(self) -> None:
        with mock.patch.object(
            chat_x_digest,
            "api_get",
            return_value={"data": [{"id": "one"}], "meta": {"has_more": True}},
        ) as api_get:
            conversations, _users, scan = chat_x_digest.collect_conversations("token", 10)

        self.assertEqual(conversations, [{"id": "one"}])
        self.assertEqual(api_get.call_count, 1)
        self.assertFalse(scan["complete"])
        self.assertEqual(scan["stop_reason"], "missing_pagination_token")

    def test_collect_conversations_never_exceeds_five_list_requests(self) -> None:
        responses = [
            {"data": [{"id": str(index)}], "meta": {"next_token": f"page-{index + 1}", "has_more": True}}
            for index in range(5)
        ]
        with mock.patch.object(chat_x_digest, "api_get", side_effect=responses) as api_get:
            conversations, _users, scan = chat_x_digest.collect_conversations("token", 10)

        self.assertEqual(len(conversations), 5)
        self.assertEqual(api_get.call_count, 5)
        self.assertEqual(scan["stop_reason"], "conversation_list_request_limit")

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
            events, keys, scan = chat_x_digest.collect_events(
                "token",
                "conversation",
                cutoff,
                chat_x_digest.EventRequestBudget(max_requests=20),
                max_pages=3,
            )

        self.assertEqual([item["id"] for item in events], ["new", "old"])
        self.assertEqual(keys, ["key"])
        self.assertEqual(api_get.call_count, 2)
        self.assertEqual(scan["pages_used"], 2)
        self.assertFalse(scan["truncated"])

    def test_collect_events_requests_only_pagination_controls(self) -> None:
        cutoff = dt.datetime(2026, 8, 2, 12, tzinfo=dt.timezone.utc)
        with mock.patch.object(
            chat_x_digest,
            "api_get",
            return_value={"data": [], "meta": {}},
        ) as api_get:
            chat_x_digest.collect_events(
                "token",
                "conversation",
                cutoff,
                chat_x_digest.EventRequestBudget(max_requests=20),
            )

        self.assertEqual(
            api_get.call_args.args,
            (
                "token",
                "/chat/conversations/conversation/events",
                {"max_results": 100, "pagination_token": ""},
            ),
        )

    def test_fetch_signing_keys_does_not_send_unsupported_field_selector(self) -> None:
        with mock.patch.object(chat_x_digest, "api_get", return_value={"data": []}) as api_get:
            chat_x_digest.fetch_user_signing_keys("token", "42")

        self.assertEqual(api_get.call_args.args, ("token", "/users/42/public_keys"))

    def test_signing_key_user_ids_include_raw_event_senders_when_members_are_missing(self) -> None:
        user_ids = chat_x_digest.signing_key_user_ids(
            {"id": "conversation"},
            [{"encoded_event": "ciphertext", "sender_id": "peer"}],
            "me",
        )

        self.assertEqual(user_ids, {"me", "peer"})

    def test_collect_events_caps_pages_for_busy_conversation(self) -> None:
        cutoff = dt.datetime(2026, 8, 2, 12, tzinfo=dt.timezone.utc)
        responses = [
            {
                "data": [{"id": f"event-{index}", "created_at": "2026-08-03T01:00:00Z"}],
                "meta": {"next_token": f"page-{index + 1}"},
            }
            for index in range(4)
        ]
        budget = chat_x_digest.EventRequestBudget(max_requests=20)
        with mock.patch.object(chat_x_digest, "api_get", side_effect=responses) as api_get:
            events, _keys, scan = chat_x_digest.collect_events(
                "token", "conversation", cutoff, budget, max_pages=3
            )

        self.assertEqual([item["id"] for item in events], ["event-0", "event-1", "event-2"])
        self.assertEqual(api_get.call_count, 3)
        self.assertEqual(budget.used, 3)
        self.assertTrue(scan["truncated"])
        self.assertEqual(scan["stop_reason"], "conversation_page_limit")

    def test_event_budget_stops_before_exceeding_safe_request_count(self) -> None:
        budget = chat_x_digest.EventRequestBudget(max_requests=2)
        budget.consume()
        budget.consume()
        with self.assertRaises(chat_x_digest.EventBudgetExhausted):
            budget.consume()
        self.assertEqual(budget.used, 2)

    def test_event_budget_reserves_reported_rate_limit_capacity(self) -> None:
        budget = chat_x_digest.EventRequestBudget(max_requests=20, reserve=5)
        chat_x_digest.RATE_LIMIT_TRACKER["/chat/conversations/:id/events"] = {
            "remaining": 5,
            "reset": 2000,
        }
        with self.assertRaises(chat_x_digest.EventBudgetExhausted):
            budget.consume(now=1000)
        self.assertEqual(budget.used, 0)

    def test_conversation_is_before_window_requires_a_reliable_message_time(self) -> None:
        cutoff = dt.datetime(2026, 8, 10, tzinfo=dt.timezone.utc)
        old_rows = [
            {
                "original_b64": "old",
                "event": {"type": "Message", "created_at": "2026-08-09T00:00:00Z"},
            }
        ]
        self.assertTrue(chat_x_digest.conversation_is_before_window(old_rows, [], cutoff))
        self.assertFalse(
            chat_x_digest.conversation_is_before_window(
                [{"original_b64": "missing", "event": {"type": "Message"}}], [], cutoff
            )
        )

    def test_main_stops_after_first_confirmed_old_conversation(self) -> None:
        class FakeChat:
            def import_keys(self, _blob: bytes, version: str) -> None:
                return None

            def set_identity(self, _user_id: str, _key_version: str) -> None:
                return None

            def set_cache_keys(self, _enabled: bool) -> None:
                return None

            def set_signing_keys(self, _keys: list[dict[str, str]]) -> None:
                return None

            def decrypt_events(self, _encoded_events: list[str]) -> dict[str, object]:
                return {
                    "errors": [],
                    "messages": [
                        {
                            "original_b64": "ciphertext",
                            "event": {
                                "type": "Message",
                                "sender_id": "peer",
                                "created_at": "2020-01-01T00:00:00Z",
                                "content": {"content_type": "Text", "text": "old"},
                            },
                        }
                    ],
                }

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "chat.json"
            with (
                mock.patch.dict(sys.modules, {"chat_xdk": types.SimpleNamespace(Chat=FakeChat)}),
                mock.patch.object(
                    chat_x_digest,
                    "load_chat_config",
                    return_value={"user_id": "me", "key_version": "1", "private_key_blob": "a2V5"},
                ),
                mock.patch.object(
                    chat_x_digest,
                    "collect_conversations",
                    return_value=([{"id": "old"}, {"id": "new"}], {}, {"complete": True, "next_token": "", "missing_id_count": 0}),
                ),
                mock.patch.object(
                    chat_x_digest,
                    "collect_events",
                    return_value=([{"encoded_event": "ciphertext"}], [], {"pages_used": 1, "truncated": False}),
                ) as collect_events,
                mock.patch.object(chat_x_digest, "signing_keys", return_value=[]),
                mock.patch.object(sys, "argv", ["chat_x_digest.py", "--bearer-token", "token", "--out", str(output)]),
            ):
                chat_x_digest.main()

            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(collect_events.call_count, 1)
        self.assertEqual(payload["dm_scan_stop_reason"], "first_conversation_before_window")
        self.assertFalse(payload["dm_scan_complete"])

    def test_zero_events_only_fail_after_complete_scan(self) -> None:
        conversations = [{"id": "one"}]
        self.assertTrue(chat_x_digest.zero_event_history_is_failure(conversations, 0, scan_complete=True))
        self.assertFalse(chat_x_digest.zero_event_history_is_failure(conversations, 0, scan_complete=False))

    def test_api_get_tracks_rate_limit_headers(self) -> None:
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{"data": []}'
        response.__enter__.return_value.headers = {
            "x-rate-limit-limit": "30",
            "x-rate-limit-remaining": "17",
            "x-rate-limit-reset": "2000",
        }
        with mock.patch.object(chat_x_digest.urllib.request, "urlopen", return_value=response):
            chat_x_digest.api_get("token", "/chat/conversations/abc/events")

        self.assertEqual(
            chat_x_digest.RATE_LIMIT_TRACKER["/chat/conversations/:id/events"]["remaining"],
            17,
        )

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

    def test_message_time_uses_decrypted_created_at_msec_without_raw_timestamp(self) -> None:
        value = chat_x_digest.message_time({"created_at_msec": 1786320000000}, {})
        self.assertEqual(value, dt.datetime.fromtimestamp(1786320000, tz=dt.timezone.utc))

    def test_message_time_falls_back_to_raw_event_timestamp(self) -> None:
        value = chat_x_digest.message_time({}, {"created_at": "2026-08-10T00:00:00Z"})
        self.assertEqual(value, dt.datetime(2026, 8, 10, tzinfo=dt.timezone.utc))

    def test_main_does_not_skip_new_decrypted_message_when_raw_timestamp_is_old(self) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        created_at_msec = int(now.timestamp() * 1000)

        class FakeChat:
            decrypted_inputs: list[list[str]] = []

            def import_keys(self, _blob: bytes, version: str) -> None:
                self.version = version

            def set_identity(self, _user_id: str, _key_version: str) -> None:
                return None

            def set_cache_keys(self, _enabled: bool) -> None:
                return None

            def set_signing_keys(self, _keys: list[dict[str, str]]) -> None:
                return None

            def decrypt_events(self, encoded_events: list[str]) -> dict[str, object]:
                self.decrypted_inputs.append(encoded_events)
                if "ciphertext" not in encoded_events:
                    return {"messages": [], "errors": []}
                return {
                    "errors": [],
                    "messages": [
                        {
                            "original_b64": "ciphertext",
                            "event": {
                                "type": "Message",
                                "sender_id": "peer",
                                "created_at_msec": created_at_msec,
                                "verified": True,
                                "content": {"content_type": "Text", "text": "hello"},
                            },
                        }
                    ],
                }

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "chat.json"
            with (
                mock.patch.dict(sys.modules, {"chat_xdk": types.SimpleNamespace(Chat=FakeChat)}),
                mock.patch.object(
                    chat_x_digest,
                    "load_chat_config",
                    return_value={"user_id": "me", "key_version": "1", "private_key_blob": "a2V5"},
                ),
                mock.patch.object(
                    chat_x_digest,
                    "collect_conversations",
                    return_value=(
                        [{"id": "chat", "participant_ids": ["me", "peer"]}],
                        {},
                        {"complete": False, "next_token": "more", "missing_id_count": 0},
                    ),
                ),
                mock.patch.object(
                    chat_x_digest,
                    "collect_events",
                    return_value=(
                        [
                            {
                                "id": "event",
                                "encoded_event": "ciphertext",
                                "created_at": "2020-01-01T00:00:00Z",
                            }
                        ],
                        [],
                        {"pages_used": 1, "truncated": False},
                    ),
                ),
                mock.patch.object(chat_x_digest, "signing_keys", return_value=[]),
                mock.patch.object(sys, "argv", ["chat_x_digest.py", "--bearer-token", "token", "--out", str(output)]),
            ):
                chat_x_digest.main()

            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(FakeChat.decrypted_inputs, [["ciphertext"]])
        self.assertEqual(payload["dm_captured_message_count"], 1)
        self.assertEqual(payload["dm_threads"][0]["messages"][0]["text"], "hello")
        self.assertFalse(payload["dm_scan_complete"])
        self.assertEqual(payload["dm_scan_stop_reason"], "conversation_list_limit")


if __name__ == "__main__":
    unittest.main()
