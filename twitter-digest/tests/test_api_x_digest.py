from __future__ import annotations

import io
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import api_x_digest  # noqa: E402


class ApiCollectorTests(unittest.TestCase):
    def args(self):
        return mock.Mock(api_base="https://api.x.com/2", bearer_token="token")

    def test_api_get_retries_tls_failure(self) -> None:
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{"data": []}'
        with (
            mock.patch.object(api_x_digest.urllib.request, "urlopen", side_effect=[urllib.error.URLError("TLS EOF"), response]) as urlopen,
            mock.patch.object(api_x_digest.time, "sleep") as sleep,
        ):
            payload = api_x_digest.api_get(self.args(), "/users/me")

        self.assertEqual(payload, {"data": []})
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_api_get_retries_server_error_with_retry_after(self) -> None:
        error = urllib.error.HTTPError(
            "https://api.x.com/2/users/me", 503, "Unavailable", {"Retry-After": "2"}, io.BytesIO(b"try later")
        )
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{"ok": true}'
        with (
            mock.patch.object(api_x_digest.urllib.request, "urlopen", side_effect=[error, response]),
            mock.patch.object(api_x_digest.time, "sleep") as sleep,
        ):
            payload = api_x_digest.api_get(self.args(), "/users/me")

        self.assertTrue(payload["ok"])
        sleep.assert_called_once_with(2.0)


if __name__ == "__main__":
    unittest.main()
