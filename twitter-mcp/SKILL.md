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

Before collecting X data, determine the user's current local timezone and the exact 24-hour window:

```bash
date '+%Y-%m-%d %H:%M:%S %Z %z'
```

Use that local time as `now`, compute `cutoff = now - 24 hours`, and include only X items whose timestamp is within `[cutoff, now]` in the user's local timezone. Convert UTC `created_at` timestamps from X into the user's local timezone before filtering or grouping. Do not use calendar-day-only filtering unless the user explicitly asks for "today" by date instead of "past 24 hours". Do not rely on `xurl` result ordering, labels such as "recent", or search date operators as proof that an item is inside the window; every item used in the digest must pass this timestamp check.

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

These commands are mandatory for daily digest collection. Do not write a final digest if any of them has not been attempted. If you notice during drafting that `from:<handle>`, `@<handle>`, or `to:<handle>` search was skipped, stop drafting, run the missing command(s), then rebuild the digest from the combined outputs.

Rules for collection:

- If `xurl whoami` does not reveal a handle, ask the user for the handle or skip handle-dependent commands and report the gap.
- Keep only posts, mentions, searches, and timeline items from the last 24 hours in the user's current local timezone. This rule is strict for `xurl mentions`: mentions older than `cutoff` must be discarded before analysis and must not appear in `需要处理`.
- `xurl mentions` is not enough to conclude current mention state. If `xurl mentions` returns only old items or no in-window items, the `@<handle>` and `to:<handle>` searches are still required before saying there are no current mentions or no reply tasks.
- Do not put "未跑关键词搜索" in the final data gaps for mandatory `from:/@/to:` searches. Missing mandatory searches are a collection error to fix by running the commands before the final answer. Only report a mandatory search as a data gap if it was attempted and failed with an error, auth limit, tier limit, or rate limit.
- If an item has no parseable timestamp, do not use it for time-bound facts; report it under data gaps as time-unverified.
- When using `xurl search`, search date operators may be used only as a coarse prefilter; still post-filter each returned item to the exact 24-hour window.
- Before adding any mention or direct ask to `需要处理` as "needs reply", verify whether the authenticated account has already replied after that mention's timestamp. Use `xurl posts <handle>` and `xurl search "from:<handle> to:<author>" -n 100` or equivalent `xurl` output to check for replies in the same conversation/thread or to the same author. If a reply from the authenticated account already exists after the mention timestamp, mark it as already handled or omit it from `需要处理`; do not ask the user to reply again.
- For every mention considered for `需要处理`, write down the reply verification result before summarizing: `already_replied`, `reply_unverified`, or `not_replied_found`. Only `not_replied_found` may be phrased as a pending reply. `already_replied` must be omitted from pending actions or shown as already handled. `reply_unverified` must be labeled `回复状态未确认`.
- If the reply status cannot be verified from available `xurl` output, label it as `回复状态未确认` instead of claiming the user still needs to reply.
- If a specific `xurl` command fails, report that command under data gaps and continue with successful command outputs.
- Do not run the DM command during normal daily digest collection. Current DM/API coverage is not reliable for this workflow and should not appear in the daily digest.
- If the user explicitly asks for private messages, explain that this skill does not collect them by default because the current API path is unavailable or unreliable; do not claim there are no private messages.
- Do not post, reply, like, repost, bookmark, follow, or send DMs without explicit approval after showing a draft/action summary.
- If `xurl` is missing or unauthenticated, help the user install or authorize it with this skill before generating the digest.

Write the final response in Chinese by default for `X日报` requests. Use this structure:

- 今日概览: 3-6 bullets with the highest-signal changes.
- 需要处理: unresolved direct asks, risks, and reply opportunities from public timeline, mentions, and searches. Exclude out-of-window mentions and already replied-to mentions. For mention rows, include the reply verification state; do not call a mention a reply task unless verification found no later reply from the authenticated account.
- 时间线热点: grouped by topic with why it matters.
- 我的账号动态: notable own posts or engagement.
- 数据缺口: failed `xurl` commands, auth/tier errors, rate limits, or items excluded because timestamps were missing/unparseable.
- 建议动作: concise reply/follow-up suggestions. Do not post or send anything without explicit approval.

## Install And Register

From the repository `skills/` directory:

```bash
/bin/bash twitter-mcp/scripts/install_xmcp.sh
```

For a one-line Codex install from this beta tag:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.12-beta.3/twitter-mcp/install.sh | env X_MCP_REGISTER_CODEX=1 X_MCP_REGISTER_CLAUDE=0 sh
```

For a one-line Claude Code install from this beta tag:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.12-beta.3/twitter-mcp/install.sh | env X_MCP_REGISTER_CODEX=0 X_MCP_REGISTER_CLAUDE=1 sh
```

The installer:

- Installs this `twitter-mcp` skill into the selected local skills directory.
- Reinstalling is the upgrade path: it replaces the skill code and preserves the existing installed `.state` directory.
- If the selected `X_MCP_APP_NAME` already has a usable `xurl` OAuth token, reinstall skips `npm install`, Client ID / Secret prompts, and OAuth browser authorization. Set `X_MCP_FORCE_CONFIGURE=1` only when the user explicitly wants to re-enter credentials or reauthorize.
- Requires Node.js 18+ and npm. Node.js 20 LTS+ is recommended.
- Installs `@xdevplatform/xurl` globally with npm.
- Opens the X OAuth2 authorization flow.
- Does not register the hosted X MCP bridge by default. To also register MCP, set `X_MCP_REGISTER_CODEX_MCP=1` or `X_MCP_REGISTER_CLAUDE_MCP=1`.

When launched by Codex, Claude Code, or another non-interactive agent on macOS, the one-line installer immediately opens a real Terminal window and re-runs the full installation there. Node/npm checks, `xurl` installation, OAuth2 Client ID / Secret input, and browser authorization all happen in Terminal, not inside the agent permission sandbox. Do not ask the user to paste OAuth credentials into chat.

## Uninstall

Safe uninstall moves the installed skill to `.backups/` and preserves `.state`:

```bash
~/.codex/skills/twitter-mcp/uninstall.sh --client codex
~/.claude/skills/twitter-mcp/uninstall.sh --client claude
```

By default, uninstall leaves global `xurl`, OAuth app config, and MCP registrations in place. Add `--remove-mcp-config` to remove the `xapi` MCP registration, add `--uninstall-xurl` to run `npm uninstall -g @xdevplatform/xurl`, and add `--purge-state` only when the user explicitly wants local state removed permanently.

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
