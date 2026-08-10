#!/usr/bin/env python3
"""Configure the X API and required X Chat access in one Terminal session."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from api_config_store import load_api_config
from chat_config_store import chat_configured, chat_runtime_status, clear_chat_config, load_chat_config
from configure_api import verify_api_config
from script_utils import open_script_in_terminal, rerun_from_installed_if_needed

REQUIRED_CHAT_SCOPES = {"dm.read", "users.read", "tweet.read"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", action="store_true", help="Show API and X Chat configuration status without prompting.")
    return parser.parse_args()


def api_status() -> tuple[bool, dict[str, object]]:
    config = load_api_config()
    if not config.get("bearer_token") and not config.get("refresh_token"):
        return False, {"verified": False, "error": "No saved API credentials."}
    saved_scopes = set(str(config.get("scopes") or "").split())
    if not saved_scopes:
        return False, {"verified": False, "error": "Saved OAuth token has no scope metadata; read-only reauthorization is required."}
    if "dm.write" in saved_scopes:
        return False, {"verified": False, "error": "Saved OAuth token has forbidden dm.write scope; read-only reauthorization is required."}
    if saved_scopes and not REQUIRED_CHAT_SCOPES.issubset(saved_scopes):
        missing = ", ".join(sorted(REQUIRED_CHAT_SCOPES - saved_scopes))
        return False, {"verified": False, "error": f"Saved OAuth token is missing required scopes: {missing}."}
    result = verify_api_config(config, save=True)
    return bool(result.get("verified")), result


def chat_status(user_id: str) -> tuple[bool, str]:
    config = load_chat_config()
    if not chat_configured():
        return False, "X Chat keys are not configured."
    if str(config.get("user_id") or "") != user_id:
        return False, "Saved X Chat keys belong to a different X account."
    runtime_ready, runtime_error = chat_runtime_status()
    if not runtime_ready:
        return False, runtime_error
    return True, ""


def run_child(script_name: str, *args: str) -> None:
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).with_name(script_name)), *args],
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"Configuration step {script_name} failed. See the actionable message above.")


def configure_all() -> None:
    print("步骤 1/2：检查 X API 配置", flush=True)
    api_ready, verification = api_status()
    if api_ready:
        print("X API 已配置并验证通过，跳过 Client ID / Secret 输入。", flush=True)
    else:
        print(f"X API 需要配置：{verification.get('error') or 'saved credentials are invalid'}", flush=True)
        print("请依次输入 Client ID、Client Secret，然后在浏览器完成 X OAuth 授权。", flush=True)
        run_child("configure_api.py", "--oauth")
        api_ready, verification = api_status()
        if not api_ready:
            raise SystemExit(f"X API configuration did not verify successfully: {verification.get('error') or 'unknown error'}")

    user_id = str(load_api_config().get("user_id") or verification.get("user_id") or "")
    if not user_id:
        raise SystemExit("X API verification did not return the authenticated user ID.")

    print("\n步骤 2/2：检查 X Chat 配置", flush=True)
    chat_ready, chat_error = chat_status(user_id)
    if chat_ready:
        print("X Chat 已配置，跳过 passcode 输入。", flush=True)
    else:
        existing_chat_user = str(load_chat_config().get("user_id") or "")
        if chat_configured() and existing_chat_user != user_id:
            clear_chat_config()
        print(f"X Chat 需要配置：{chat_error}", flush=True)
        print("请输入 X Chat passcode。它只用于本次解锁，不会保存。", flush=True)
        run_child("configure_chat.py")
        chat_ready, chat_error = chat_status(user_id)
        if not chat_ready:
            raise SystemExit(f"X Chat configuration is incomplete: {chat_error}")

    print(
        json.dumps(
            {
                "configured": True,
                "api_verified": True,
                "chat_configured": True,
                "next_step": "返回 Agent 对话重新生成 X 日报。",
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )


def main() -> None:
    rerun_from_installed_if_needed(__file__)
    args = parse_args()
    if args.status:
        api_ready, verification = api_status()
        user_id = str(load_api_config().get("user_id") or verification.get("user_id") or "")
        chat_ready, chat_error = chat_status(user_id) if user_id else (False, "Authenticated X user is unknown.")
        print(
            json.dumps(
                {
                    "configured": api_ready and chat_ready,
                    "api_verified": api_ready,
                    "api_error": "" if api_ready else str(verification.get("error") or ""),
                    "chat_configured": chat_ready,
                    "chat_error": chat_error,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    if not sys.stdin.isatty():
        opened = open_script_in_terminal(
            script=Path(__file__).resolve(),
            args=[],
            cwd=Path(__file__).resolve().parents[1],
            heading="X 日报统一配置向导",
            description="请在此窗口依次输入 Client ID、Client Secret 和 X Chat passcode，并在浏览器完成 OAuth 授权。",
        )
        if opened:
            print("已打开一个 Terminal 窗口，用于一次性完成 X API 和 X Chat 配置。", flush=True)
            return
        raise SystemExit("Configuration requires an interactive Terminal.")
    configure_all()


if __name__ == "__main__":
    main()
