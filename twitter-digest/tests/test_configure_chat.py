from __future__ import annotations

import io
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import configure_chat  # noqa: E402
from collector_commands import parse_structured_api_error  # noqa: E402


class ConfigureChatTests(unittest.TestCase):
    def test_configure_fetches_all_public_key_fields_without_selector(self) -> None:
        api_config = {
            "bearer_token": "token",
            "user_id": "secret-user",
            "scopes": "dm.read users.read tweet.read",
        }
        with (
            mock.patch.object(configure_chat, "load_api_config", return_value=api_config),
            mock.patch.object(configure_chat, "refresh_oauth_token_if_needed", return_value=api_config),
            mock.patch.object(configure_chat, "chat_configured", return_value=False),
            mock.patch.object(configure_chat, "api_get", return_value={"data": []}) as api_get,
            self.assertRaisesRegex(SystemExit, "No passcode-backed X Chat public key"),
        ):
            configure_chat.configure()

        api_get.assert_called_once_with("token", "/users/secret-user/public_keys")

    def test_api_get_stops_after_first_429_and_hides_user_id(self) -> None:
        error = urllib.error.HTTPError(
            "https://api.x.com/2/users/secret-user/public_keys",
            429,
            "Too Many Requests",
            {"Retry-After": "90"},
            io.BytesIO(b"secret-user"),
        )
        with (
            mock.patch.object(configure_chat.urllib.request, "urlopen", side_effect=error) as urlopen,
            mock.patch.object(configure_chat.time, "sleep") as sleep,
        ):
            with self.assertRaises(SystemExit) as raised:
                configure_chat.api_get(
                    "token",
                    "/users/secret-user/public_keys?public_key.fields=juicebox_config",
                )

        self.assertEqual(urlopen.call_count, 1)
        sleep.assert_not_called()
        self.assertNotIn("secret-user", str(raised.exception))
        self.assertIn("X Chat 公钥读取暂时受到限流", str(raised.exception))
        self.assertEqual(
            parse_structured_api_error(str(raised.exception)),
            {
                "source": "x_chat",
                "endpoint": "public_keys",
                "status": 429,
                "retry_after_seconds": 90,
            },
        )

    def test_api_get_still_retries_transient_503(self) -> None:
        error = urllib.error.HTTPError(
            "https://api.x.com/2/users/me/public_keys",
            503,
            "Unavailable",
            {},
            io.BytesIO(b"temporary"),
        )
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{"data": []}'
        with (
            mock.patch.object(configure_chat.urllib.request, "urlopen", side_effect=[error, response]) as urlopen,
            mock.patch.object(configure_chat.time, "sleep") as sleep,
        ):
            payload = configure_chat.api_get("token", "/users/me/public_keys")

        self.assertEqual(payload, {"data": []})
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_api_get_uses_rate_limit_reset_when_retry_after_is_missing(self) -> None:
        error = urllib.error.HTTPError(
            "https://api.x.com/2/users/me/public_keys",
            429,
            "Too Many Requests",
            {"x-rate-limit-reset": "1090"},
            io.BytesIO(b"limited"),
        )
        with (
            mock.patch.object(configure_chat.urllib.request, "urlopen", side_effect=error),
            mock.patch.object(configure_chat.time, "time", return_value=1000),
        ):
            with self.assertRaises(SystemExit) as raised:
                configure_chat.api_get("token", "/users/me/public_keys")

        self.assertEqual(
            parse_structured_api_error(str(raised.exception))["retry_after_seconds"],
            90,
        )


if __name__ == "__main__":
    unittest.main()
