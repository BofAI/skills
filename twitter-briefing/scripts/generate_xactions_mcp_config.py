#!/usr/bin/env python3
"""Print starter MCP config for cookie-based Twitter/X access."""

from __future__ import annotations

import argparse
import json
import textwrap


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--client",
        choices=["generic", "claude-desktop"],
        default="generic",
        help="Config style to print. Generic works as a stdio MCP recipe for Codex, Claude, Cursor, and similar clients.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = {
        "mcpServers": {
            "twitter": {
                "command": "npx",
                "args": ["-y", "agent-twitter-client-mcp"],
                "env": {
                    "AUTH_METHOD": "cookies",
                    "TWITTER_COOKIES": "PASTE_COOKIE_JSON_ARRAY_IN_LOCAL_CONFIG_ONLY"
                },
            }
        }
    }
    if args.client == "claude-desktop":
        print("Add this server to claude_desktop_config.json:")
    else:
        print("Add an equivalent stdio MCP server to your agent/MCP client:")
    print(json.dumps(config, indent=2))
    print()
    print(
        textwrap.dedent(
            """
            Setup notes:
            1. Log in to https://x.com in a local browser.
            2. Open DevTools -> Application -> Cookies -> https://x.com.
            3. Copy the `auth_token` cookie value.
            4. Store auth_token, ct0, and twid locally as the `TWITTER_COOKIES` env value.
            5. Restart the MCP client and verify that Twitter MCP tools are visible.

            Security:
            - Treat auth_token like a password.
            - Do not commit it, paste it into shared chats, or print it in logs.
            - Prefer read-only briefing tasks; require explicit approval before write actions.
            """
        ).strip()
    )


if __name__ == "__main__":
    main()
