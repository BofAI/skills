#!/usr/bin/env python3
"""Configure required X Chat decryption for twitter-digest."""

from __future__ import annotations

import argparse
import base64
import getpass
import json
import subprocess
import sys
from pathlib import Path

from api_config_store import load_api_config, refresh_oauth_token_if_needed
from chat_config_store import (
    CHAT_CONFIG_PATH,
    CHAT_RUNTIME_DIR,
    chat_configured,
    clear_chat_config,
    save_chat_config,
)
from script_utils import (
    open_script_in_terminal,
    rerun_from_installed_if_needed,
)

CHATXDK_VERSION = "0.4.3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", action="store_true", help="Show whether required X Chat collection is configured.")
    parser.add_argument("--clear", action="store_true", help="Disable X Chat and remove the saved private-key blob.")
    return parser.parse_args()


def runtime_python() -> Path:
    return CHAT_RUNTIME_DIR / "bin" / "python"


def ensure_runtime() -> Path:
    python = runtime_python()
    if python.exists():
        probe = subprocess.run(
            [str(python), "-c", "import chat_xdk; print('ready')"],
            check=False,
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            return python
    CHAT_RUNTIME_DIR.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "venv", str(CHAT_RUNTIME_DIR)], check=True)
    subprocess.run(
        [str(python), "-m", "pip", "install", "--disable-pip-version-check", f"chatxdk=={CHATXDK_VERSION}"],
        check=True,
    )
    return python


def run_unlock_helper(python: Path, passcode: str, record: dict[str, object]) -> bytes:
    helper = (
        "import base64,json,sys\n"
        "from chat_xdk import Chat\n"
        "record=json.loads(sys.stdin.readline())\n"
        "pin=sys.stdin.readline().rstrip('\\n')\n"
        "chat=Chat(json.dumps(record['juicebox_config']))\n"
        "chat.unlock(pin)\n"
        "sys.stdout.write(base64.b64encode(bytes(chat.export_keys())).decode('ascii'))\n"
    )
    completed = subprocess.run(
        [str(python), "-c", helper],
        check=False,
        input=json.dumps(record) + "\n" + passcode + "\n",
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise SystemExit(f"X Chat key unlock failed: {' '.join(completed.stderr.split())[:600]}")
    try:
        return base64.b64decode(completed.stdout.strip(), validate=True)
    except ValueError as exc:
        raise SystemExit("X Chat key unlock returned an invalid key blob.") from exc


def api_get(token: str, path: str) -> dict[str, object]:
    import urllib.error
    import urllib.request

    request = urllib.request.Request(
        "https://api.x.com/2" + path,
        headers={"Authorization": f"Bearer {token}", "User-Agent": "twitter-digest-chat/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"X Chat API request failed with HTTP {exc.code}: {detail[:600]}") from exc


def configure() -> None:
    api_config = refresh_oauth_token_if_needed(load_api_config())
    token = str(api_config.get("bearer_token") or "")
    user_id = str(api_config.get("user_id") or "")
    if not token or not user_id:
        raise SystemExit("Configure and verify the normal X API first; X Chat reuses that OAuth2 user token.")
    scopes = set(str(api_config.get("scopes") or "").split())
    required = {"dm.read", "dm.write", "users.read", "tweet.read"}
    if scopes and not required.issubset(scopes):
        missing = ", ".join(sorted(required - scopes))
        raise SystemExit(f"Saved OAuth token is missing required X Chat scopes: {missing}. Re-run X API configuration.")

    payload = api_get(
        token,
        f"/users/{user_id}/public_keys?public_key.fields=public_key_version,public_key,signing_public_key,identity_public_key_signature,juicebox_config",
    )
    records = payload.get("data") if isinstance(payload, dict) else None
    usable = [record for record in (records or []) if isinstance(record, dict) and record.get("juicebox_config")]
    if not usable:
        raise SystemExit("No passcode-backed X Chat public key was found for this account. Open X Chat in X and complete its key setup first.")
    record = usable[-1]
    passcode = getpass.getpass("X Chat passcode (used only to unlock keys now; it will not be saved): ")
    if not passcode:
        raise SystemExit("No X Chat passcode entered. Configuration was not changed.")
    python = ensure_runtime()
    private_blob = run_unlock_helper(python, passcode, record)
    save_chat_config(
        {
            "enabled": True,
            "user_id": user_id,
            "key_version": str(record.get("public_key_version") or ""),
            "private_key_blob": base64.b64encode(private_blob).decode("ascii"),
            "chatxdk_version": CHATXDK_VERSION,
            "storage": "owner_only_local_key_blob",
        }
    )
    print(
        json.dumps(
            {
                "configured": True,
                "chat_config": str(CHAT_CONFIG_PATH),
                "passcode_saved": False,
                "next_step": "Run the normal daily digest. X Chat will be included automatically.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> None:
    rerun_from_installed_if_needed(__file__)
    args = parse_args()
    if args.status:
        print(json.dumps({"configured": chat_configured(), "chat_config": str(CHAT_CONFIG_PATH)}, ensure_ascii=False, indent=2))
        return
    if args.clear:
        clear_chat_config()
        print(json.dumps({"configured": False, "cleared": True}, ensure_ascii=False, indent=2))
        return
    if not sys.stdin.isatty():
        opened = open_script_in_terminal(
            script=Path(__file__).resolve(),
            args=[],
            cwd=Path(__file__).resolve().parents[1],
            heading="X Chat 配置向导",
            description="请输入 X Chat passcode 解锁密钥。passcode 不会保存，也不要粘贴到 Agent 对话。",
        )
        if opened:
            print("已打开 Terminal 窗口用于配置 X Chat。", flush=True)
            return
        raise SystemExit("X Chat configuration requires an interactive Terminal.")
    configure()


if __name__ == "__main__":
    main()
