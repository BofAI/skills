from __future__ import annotations

import base64
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import chat_config_store  # noqa: E402
import chat_rate_limit_store  # noqa: E402


class ChatConfigStoreTests(unittest.TestCase):
    def cache_paths(self, directory: str):
        root = Path(directory)
        return (
            mock.patch.object(chat_config_store, "CHAT_STATE_DIR", root),
            mock.patch.object(chat_config_store, "CHAT_SIGNING_KEY_CACHE_PATH", root / "signing_keys.json"),
        )
    def test_corrupt_private_blob_is_not_configured(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            with (
                mock.patch.object(chat_config_store, "CHAT_CONFIG_PATH", path),
                mock.patch.object(chat_config_store, "CHAT_STATE_DIR", path.parent),
            ):
                chat_config_store.save_chat_config(
                    {"enabled": True, "user_id": "1", "key_version": "1", "private_key_blob": "not-base64"}
                )
                self.assertFalse(chat_config_store.chat_configured())

    def test_valid_private_blob_is_configured(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            with (
                mock.patch.object(chat_config_store, "CHAT_CONFIG_PATH", path),
                mock.patch.object(chat_config_store, "CHAT_STATE_DIR", path.parent),
            ):
                chat_config_store.save_chat_config(
                    {
                        "enabled": True,
                        "user_id": "1",
                        "key_version": "1",
                        "private_key_blob": base64.b64encode(b"key").decode(),
                    }
                )
                self.assertTrue(chat_config_store.chat_configured())

    def test_signing_keys_are_reused_for_24_hours(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_patch, path_patch = self.cache_paths(directory)
            fetch = mock.Mock(side_effect=lambda user_id: [{"user_id": user_id, "public_key_version": "1"}])
            with state_patch, path_patch:
                first = chat_config_store.cached_signing_keys("owner", {"owner", "peer"}, fetch, now=1000)
                second = chat_config_store.cached_signing_keys("owner", {"owner", "peer"}, fetch, now=2000)

                self.assertEqual(first, second)
                self.assertEqual(fetch.call_count, 2)
                self.assertEqual(chat_config_store.CHAT_SIGNING_KEY_CACHE_PATH.stat().st_mode & 0o777, 0o600)

    def test_expired_or_forced_signing_keys_are_refreshed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_patch, path_patch = self.cache_paths(directory)
            fetch = mock.Mock(side_effect=lambda user_id: [{"user_id": user_id, "public_key_version": str(fetch.call_count)}])
            with state_patch, path_patch:
                chat_config_store.cached_signing_keys("owner", {"peer"}, fetch, now=1000)
                chat_config_store.cached_signing_keys(
                    "owner", {"peer"}, fetch, force_refresh_ids={"peer"}, now=1100
                )
                chat_config_store.cached_signing_keys(
                    "owner", {"peer"}, fetch, now=1100 + chat_config_store.SIGNING_KEY_CACHE_TTL_SECONDS + 1
                )
                self.assertEqual(fetch.call_count, 3)

    def test_switching_owner_does_not_reuse_signing_key_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_patch, path_patch = self.cache_paths(directory)
            fetch = mock.Mock(side_effect=lambda user_id: [{"user_id": user_id}])
            with state_patch, path_patch:
                chat_config_store.cached_signing_keys("owner-a", {"peer"}, fetch, now=1000)
                chat_config_store.cached_signing_keys("owner-b", {"peer"}, fetch, now=1100)
                self.assertEqual(fetch.call_count, 2)

    def test_clearing_chat_config_also_clears_signing_key_cache_and_cooldown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.json"
            cache_path = root / "signing_keys.json"
            config_path.write_text("{}", encoding="utf-8")
            cache_path.write_text("{}", encoding="utf-8")
            with (
                mock.patch.object(chat_config_store, "CHAT_CONFIG_PATH", config_path),
                mock.patch.object(chat_config_store, "CHAT_SIGNING_KEY_CACHE_PATH", cache_path),
                mock.patch.object(chat_rate_limit_store, "clear_rate_limits") as clear_rate_limits,
            ):
                chat_config_store.clear_chat_config()
            self.assertFalse(config_path.exists())
            self.assertFalse(cache_path.exists())
            clear_rate_limits.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
