from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from collector_commands import (  # noqa: E402
    parse_structured_api_error,
    structured_api_error,
    summarize_collector_error,
)


class CollectorErrorTests(unittest.TestCase):
    def test_unmarked_error_keeps_traceback_tail(self) -> None:
        text = "urllib stack " + ("x" * 600) + " final exception detail"
        summary = summarize_collector_error(text)
        self.assertNotIn("urllib stack", summary)
        self.assertTrue(summary.endswith("final exception detail"))

    def test_ssl_eof_marker_is_preserved(self) -> None:
        summary = summarize_collector_error("traceback [SSL: UNEXPECTED_EOF_WHILE_READING] failure")
        self.assertEqual(summary, "UNEXPECTED_EOF_WHILE_READING")

    def test_429_summary_keeps_retry_wait(self) -> None:
        summary = summarize_collector_error("HTTP 429 Too Many Requests; retry after about 317 seconds")
        self.assertEqual(summary, "HTTP 429; Too Many Requests; retry after about 317 seconds")

    def test_structured_error_round_trips_allowlisted_fields(self) -> None:
        marker = structured_api_error("x_chat", "conversation_events", 429, 317)
        parsed = parse_structured_api_error("traceback\n" + marker)
        self.assertEqual(
            parsed,
            {
                "source": "x_chat",
                "endpoint": "conversation_events",
                "status": 429,
                "retry_after_seconds": 317,
            },
        )

    def test_structured_summary_discards_surrounding_identifiers(self) -> None:
        marker = structured_api_error("x_chat", "conversation_events", 429, 12)
        summary = summarize_collector_error(
            "GET /chat/conversations/secret-conversation-id/events failed\n" + marker
        )
        self.assertEqual(summary, marker)
        self.assertNotIn("secret-conversation-id", summary)


if __name__ == "__main__":
    unittest.main()
