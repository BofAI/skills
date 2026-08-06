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

    def test_collects_liking_users_for_recent_own_posts_with_likes(self) -> None:
        args = self.args()
        posts = [
            {"id": "10", "time": "2026-08-06T01:00:00Z", "url": "https://x.com/me/status/10", "text": "hello", "metrics": {"like_count": 2}},
            {"id": "11", "time": "2026-08-06T02:00:00Z", "url": "https://x.com/me/status/11", "text": "quiet", "metrics": {"like_count": 0}},
        ]
        with mock.patch.object(
            api_x_digest,
            "api_get",
            return_value={"data": [{"id": "1", "username": "alice"}, {"id": "2", "username": "bob"}]},
        ) as api_get:
            items, errors = api_x_digest.collect_recent_own_post_likes(args, posts)

        self.assertEqual([item["author_username"] for item in items], ["alice", "bob"])
        self.assertTrue(all(item["interaction_type"] == "liked_your_post" for item in items))
        self.assertEqual(errors, [])
        api_get.assert_called_once_with(
            args,
            "/tweets/10/liking_users",
            {"max_results": 100, "user.fields": "username,name"},
        )


if __name__ == "__main__":
    unittest.main()
