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


class ChatConfigStoreTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
