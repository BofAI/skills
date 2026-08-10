from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from collector_commands import summarize_collector_error  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
