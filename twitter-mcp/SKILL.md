---
name: twitter-mcp
description: Use when the user wants to install, authorize, register, verify, or troubleshoot the official X/Twitter MCP server for Codex, Claude Code, or another MCP-capable agent.
---

# X/Twitter MCP

## Overview

Use this skill to install and register the official X MCP server through `@xdevplatform/xurl`. This skill only handles MCP setup and troubleshooting. It does not collect timeline data, generate digests, read DMs, or install `twitter-digest`.

After successful setup, the MCP server is registered as `xapi` by default. The user usually needs to start a new Codex or Claude Code session before newly registered MCP tools become visible.

## Install And Register

From the repository `skills/` directory:

```bash
/bin/bash twitter-mcp/scripts/install_xmcp.sh
```

For a one-line Codex install from this beta tag:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.11-beta.5/twitter-mcp/install.sh | X_MCP_REGISTER_CODEX=1 X_MCP_REGISTER_CLAUDE=0 sh
```

For a one-line Claude Code install from this beta tag:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.11-beta.5/twitter-mcp/install.sh | X_MCP_REGISTER_CODEX=0 X_MCP_REGISTER_CLAUDE=1 sh
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

- Use `twitter-mcp` for installing, authorizing, registering, and troubleshooting X MCP.
- Use a separate data or digest skill, such as `twitter-digest`, for analyzing X/Twitter content after MCP tools are visible.
- Do not install or modify unrelated skills from this skill.
