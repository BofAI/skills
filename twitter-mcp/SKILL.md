---
name: twitter-mcp
description: Use when the user wants to install, authorize, register, verify, or troubleshoot the official X/Twitter MCP server for Codex, Claude Code, or another MCP-capable agent. Also use when the user asks "生成X日报", "X日报", "推特日报", or "Twitter digest" and wants the digest generated from X MCP tools rather than local API/browser collectors.
---

# X/Twitter MCP

## Overview

Use this skill to install and register the official X MCP server through `@xdevplatform/xurl`, and to generate X/Twitter daily digests from X MCP tool results when those tools are visible in the current agent session. This skill does not use local API collectors, local browser collectors, or `twitter-digest` scripts.

After successful setup, the MCP server is registered as `xapi` by default. The user usually needs to start a new Codex or Claude Code session before newly registered MCP tools become visible.

If the user asks to generate an X/Twitter daily digest, says `生成X日报`, `X日报`, `推特日报`, or asks for a Twitter digest, use available `xapi` / X MCP tools directly and write the digest from those tool results. Do not create a generic report template. Do not run `twitter-digest` scripts or local browser/API collectors from this skill.

## MCP Digest Workflow

When X MCP tools are available, collect data directly through MCP:

- Resolve the authenticated account with `get_users_me` or the closest available current-user tool.
- Collect home timeline / followed-account activity with `get_users_timeline` or the closest available timeline tool.
- Collect direct mentions with `get_users_mentions`.
- Collect the user's own recent posts with `get_users_posts`.
- Use search tools such as `search_posts_all` only for explicit keywords, extra mention searches, or user-requested topics.
- Use trends or news tools only when available and relevant.
- Collect DM/X Chat data only if the current X MCP tool list exposes a DM/chat capability. If it does not, clearly report that DMs were not collected through MCP; do not claim there are no private messages.

If X MCP tools are not visible in the current session:

- Say that the MCP server may be installed but the current agent session cannot see its tools yet.
- Tell the user to open a new Codex or Claude Code session after installation.
- If tools are still missing, troubleshoot registration with this skill.

Write the final response in Chinese by default for `X日报` requests. Use this structure:

- 今日概览: 3-6 bullets with the highest-signal changes.
- 需要处理: direct asks, risks, reply opportunities, urgent DMs if collected.
- 时间线热点: grouped by topic with why it matters.
- 我的账号动态: notable own posts or engagement.
- 数据缺口: missing MCP tools, auth/tier errors, unavailable DMs, or rate limits.
- 建议动作: concise reply/follow-up suggestions. Do not post or send anything without explicit approval.

## Install And Register

From the repository `skills/` directory:

```bash
/bin/bash twitter-mcp/scripts/install_xmcp.sh
```

For a one-line Codex install from this beta tag:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.11-beta.8/twitter-mcp/install.sh | X_MCP_REGISTER_CODEX=1 X_MCP_REGISTER_CLAUDE=0 sh
```

For a one-line Claude Code install from this beta tag:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.11-beta.8/twitter-mcp/install.sh | X_MCP_REGISTER_CODEX=0 X_MCP_REGISTER_CLAUDE=1 sh
```

The installer:

- Installs this `twitter-mcp` skill into the selected local skills directory.
- Requires Node.js and npm.
- Installs `@xdevplatform/xurl` globally with npm.
- Opens the X OAuth2 authorization flow.
- Registers an MCP server named `xapi` for Codex by editing `~/.codex/config.toml`.
- Registers the same MCP server for Claude Code when the `claude` CLI is available.

When launched by Codex or Claude Code on macOS, the installer opens a real Terminal window for OAuth2 Client ID / Secret input and browser authorization. Do not ask the user to paste OAuth credentials into chat.

## Configuration

Environment controls:

```bash
XMCP_PACKAGE=@xdevplatform/xurl
XMCP_VERSION=latest
X_MCP_APP_NAME=xmcp
X_MCP_REDIRECT_URI=http://localhost:8080/callback
X_MCP_SERVER_NAME=xapi
X_MCP_REGISTER_CODEX=1
X_MCP_REGISTER_CLAUDE=auto
CODEX_CONFIG=~/.codex/config.toml
X_MCP_OPEN_TERMINAL=auto
X_MCP_CLIENT_ID=<client-id>
X_MCP_CLIENT_SECRET=<client-secret>
```

Use `X_MCP_CLIENT_ID` and `X_MCP_CLIENT_SECRET` only when the user explicitly provides them through a secure environment. Prefer the interactive Terminal prompts for secrets.

## Manual MCP Command

For MCP clients that need the command directly:

```bash
xurl --app xmcp mcp https://api.x.com/mcp
```

Codex config shape:

```toml
[mcp_servers.xapi]
command = "xurl"
args = ["--app", "xmcp", "mcp", "https://api.x.com/mcp"]
```

Claude Code command shape:

```bash
claude mcp add xapi -- xurl --app xmcp mcp https://api.x.com/mcp
```

## Verification

After installation:

1. Start a new Codex or Claude Code session.
2. Check whether X MCP tools are visible under the `xapi` server.
3. If tools are missing, verify `xurl` is on `PATH`, the MCP config contains `xapi`, and the OAuth app name matches the configured `--app` value.

If an X MCP endpoint returns an auth, subscription, tier, or scope error, report the exact failing capability as a setup or account limitation. Do not infer that the requested X data does not exist.

## Boundaries

- Use `twitter-mcp` for installing, authorizing, registering, troubleshooting X MCP, and generating MCP-sourced X/Twitter digests.
- Do not use local API tokens, local browser sessions, cookies, screenshots, or `twitter-digest` run outputs from this skill.
- Do not install or modify unrelated skills from this skill.
