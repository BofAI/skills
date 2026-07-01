---
name: twitter-mcp
description: Use when the user wants to install or authorize xurl for X/Twitter, generate "生成X日报", "X日报", "推特日报", or "Twitter digest" from the local xurl CLI, or optionally register/troubleshoot the hosted X MCP bridge.
---

# X/Twitter xurl Digest

## Overview

Use this skill to install and authorize `@xdevplatform/xurl`, and to generate X/Twitter daily digests from the local `xurl` CLI. The primary digest data source is `xurl` CLI output, not the hosted X MCP tool list. This skill does not use local API collectors, local browser collectors, or `twitter-digest` scripts.

The hosted X MCP bridge can still be registered as `xapi` when explicitly requested, but daily digest generation should not depend on MCP tools being visible. `xurl` CLI exposes direct digest-relevant commands such as `whoami`, `timeline`, `mentions`, `posts`, and `search`.

If the user asks to generate an X/Twitter daily digest, says `生成X日报`, `X日报`, `推特日报`, or asks for a Twitter digest, use this skill to guide direct `xurl` CLI collection. Do not create a generic report template. Do not run digest helper scripts, `twitter-digest` scripts, or local browser/API collectors from this skill.

## xurl Digest Workflow

For daily digest requests, run `xurl` commands directly from the agent shell and use their outputs as the digest source. Do not create or run wrapper/helper scripts for digest collection.

```bash
xurl whoami
xurl timeline -n 100
xurl mentions -n 100
```

Detect the authenticated handle from `xurl whoami`. Then run:

```bash
xurl posts <handle> -n 100
xurl search "from:<handle>" -n 100
xurl search "@<handle>" -n 100
xurl search "to:<handle>" -n 100
```

Rules for collection:

- If `xurl whoami` does not reveal a handle, ask the user for the handle or skip handle-dependent commands and report the gap.
- If a specific `xurl` command fails, report that command under data gaps and continue with successful command outputs.
- Do not run the DM command during normal daily digest collection. Current DM/API coverage is not reliable for this workflow and should not appear in the daily digest.
- If the user explicitly asks for private messages, explain that this skill does not collect them by default because the current API path is unavailable or unreliable; do not claim there are no private messages.
- Do not post, reply, like, repost, bookmark, follow, or send DMs without explicit approval after showing a draft/action summary.
- If `xurl` is missing or unauthenticated, help the user install or authorize it with this skill before generating the digest.

Write the final response in Chinese by default for `X日报` requests. Use this structure:

- 今日概览: 3-6 bullets with the highest-signal changes.
- 需要处理: direct asks, risks, and reply opportunities from public timeline, mentions, and searches.
- 时间线热点: grouped by topic with why it matters.
- 我的账号动态: notable own posts or engagement.
- 数据缺口: failed `xurl` commands, auth/tier errors, or rate limits.
- 建议动作: concise reply/follow-up suggestions. Do not post or send anything without explicit approval.

## Install And Register

From the repository `skills/` directory:

```bash
/bin/bash twitter-mcp/scripts/install_xmcp.sh
```

For a one-line Codex install from this beta tag:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.11-beta.13/twitter-mcp/install.sh | X_MCP_REGISTER_CODEX=1 X_MCP_REGISTER_CLAUDE=0 sh
```

For a one-line Claude Code install from this beta tag:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.11-beta.13/twitter-mcp/install.sh | X_MCP_REGISTER_CODEX=0 X_MCP_REGISTER_CLAUDE=1 sh
```

The installer:

- Installs this `twitter-mcp` skill into the selected local skills directory.
- Requires Node.js and npm.
- Installs `@xdevplatform/xurl` globally with npm.
- Opens the X OAuth2 authorization flow.
- Does not register the hosted X MCP bridge by default. To also register MCP, set `X_MCP_REGISTER_CODEX_MCP=1` or `X_MCP_REGISTER_CLAUDE_MCP=1`.

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
X_MCP_REGISTER_CODEX_MCP=0
X_MCP_REGISTER_CLAUDE_MCP=0
CODEX_CONFIG=~/.codex/config.toml
X_MCP_OPEN_TERMINAL=auto
X_MCP_CLIENT_ID=<client-id>
X_MCP_CLIENT_SECRET=<client-secret>
```

Use `X_MCP_CLIENT_ID` and `X_MCP_CLIENT_SECRET` only when the user explicitly provides them through a secure environment. Prefer the interactive Terminal prompts for secrets.

## Manual MCP Command

For optional hosted MCP clients that need the bridge command directly:

```bash
xurl --app xmcp mcp https://api.x.com/mcp
```

Codex config shape:

```toml
[mcp_servers.xapi]
command = "/absolute/path/to/xurl"
args = ["--app", "xmcp", "mcp", "https://api.x.com/mcp"]
```

Claude Code command shape:

```bash
claude mcp add xapi -- xurl --app xmcp mcp https://api.x.com/mcp
```

## Verification

After installation:

1. Run `xurl whoami` to verify the local CLI is authorized.
2. Run `xurl timeline -n 10` and `xurl mentions -n 10` to verify digest collection.
3. If optional MCP registration was enabled, start a new Codex or Claude Code session and check whether X MCP tools are visible under the `xapi` server.

If an X MCP endpoint returns an auth, subscription, tier, or scope error, report the exact failing capability as a setup or account limitation. Do not infer that the requested X data does not exist.

## Boundaries

- Use `twitter-mcp` for installing and authorizing `xurl`, generating `xurl` CLI-sourced X/Twitter digests, and optionally registering/troubleshooting the hosted X MCP bridge.
- Do not use local API tokens, local browser sessions, cookies, screenshots, or `twitter-digest` run outputs from this skill.
- Do not install or modify unrelated skills from this skill.
