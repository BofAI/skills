---
name: twitter-digest
description: Use when the user asks to generate an X/Twitter daily digest or says phrases such as "生成X日报", "生成 x 日报", "X日报", "推特日报", "Twitter digest", or wants an agent to analyze their own X/Twitter mentions, X Chat, home timeline, reply opportunities, and daily social-media summaries. This skill is API-only and requires X Chat.
---

# X/Twitter Digest

## Overview

Use this skill to produce a concise Chinese daily digest from the user's own X/Twitter account. The data source is API-only and includes required X Chat collection through the official Chat XDK.

Normal daily runs use:

```bash
RUN_DAILY_DIGEST
```

`RUN_DAILY_DIGEST` means the installed command for the current agent:

- Claude Code: `python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py`
- Codex: `python3 ~/.codex/skills/twitter-digest/scripts/run_daily_digest.py`

For API maintenance, `CONFIGURE_API` means:

- Claude Code: `python3 ~/.claude/skills/twitter-digest/scripts/configure_api.py`
- Codex: `python3 ~/.codex/skills/twitter-digest/scripts/configure_api.py`

For X Chat maintenance, `CONFIGURE_CHAT` means:

- Claude Code: `python3 ~/.claude/skills/twitter-digest/scripts/configure_chat.py`
- Codex: `python3 ~/.codex/skills/twitter-digest/scripts/configure_chat.py`

## Source Contract

`twitter-digest` has one API source composed of two required collectors:

```bash
python3 twitter-digest/scripts/api_x_digest.py
python3 twitter-digest/scripts/chat_x_digest.py
```

The wrapper `scripts/run_daily_digest.py` runs both collectors and merges their current-run output.

Source rules:

- A normal "生成日报" / "日报" / "要" request always runs `RUN_DAILY_DIGEST`.
- API credentials and X Chat decryption keys are required before a digest can be generated.
- If API credentials are already saved, the run uses API and refreshes OAuth tokens when possible.
- If API credentials are missing or expired, the wrapper starts API configuration. If X Chat is not configured, it starts X Chat configuration. The digest must be rerun after either configuration succeeds.
- When configuration is opened in Terminal, do not ask the user to paste Client ID, Client Secret, tokens, app credentials, or X Chat passcode in chat. One Terminal wizard collects all three inputs and completes OAuth. Tell the user to finish that single flow, then rerun `RUN_DAILY_DIGEST`.
- Do not switch to another data source on API or X Chat errors, rate limits, permission errors, or user requests for "more complete" data.
- If the user asks for a non-API source or cookies, explain that this skill only supports API collection.

API source isolation is strict:

- It runs `api_x_digest.py` for public/account data.
- It runs `chat_x_digest.py` in the private Chat XDK runtime for X Chat.
- It never reads a local profile or cookies.
- It never supplements missing API data with another collector.
- It never asks the user to copy cookies.

OAuth setup may open the X authorization page. That is only for authorization and is not data collection.

## Required API Configuration

API access is required. If the user asks to configure API access, run:

```bash
RUN_DAILY_DIGEST --configure
```

This is the only primary setup flow. It opens one real Terminal window and, when needed, asks in sequence for the X Developer App Client ID, Client Secret, and X Chat passcode. OAuth authorization still completes in the browser. Existing valid API and X Chat configuration is skipped. Request scopes:

```text
tweet.read users.read offline.access dm.read dm.write
```

If the agent is not inside an interactive Terminal, use the wrapper. It opens one real Terminal window for all secure credential input, OAuth callback handling, and Chat key unlock. After that command reports `configuration_required`, stop and tell the user to finish the Terminal flow. When the user says configuration is done, rerun `RUN_DAILY_DIGEST`.

Verify saved API configuration with:

```bash
CONFIGURE_API --verify
```

Clear saved API configuration with:

```bash
CONFIGURE_API --clear
```

## Required X Chat Configuration

After normal API configuration, run:

```bash
RUN_DAILY_DIGEST --configure
```

The secure Terminal flow:

- Reuses the saved OAuth2 user token with `dm.read`, `dm.write`, `users.read`, and `tweet.read`.
- Fetches the authenticated account's registered X Chat public-key record.
- Prompts for the X Chat passcode in Terminal. Never ask the user to paste it into Agent chat.
- Uses Chat XDK to unlock the identity and exports a local key blob with owner-only permissions.
- Never saves the passcode.

The local key blob is unencrypted private identity material, as defined by Chat XDK. It is stored only because unattended daily runs cannot prompt for the passcode every time. Keep the skill's `.state` directory private; use uninstall `--purge-state` to remove the active blob and all backed-up copies.

Normal runs require this configuration and fail instead of producing a partial digest when X Chat cannot be read or decrypted.

Check or clear X Chat configuration:

```bash
RUN_DAILY_DIGEST --chat-status
RUN_DAILY_DIGEST --disable-chat
```

Do not write ad-hoc token verification scripts. Do not ask the user to export bearer tokens manually unless they explicitly want to use environment variables.

## Data Collection

For every new digest request, run collection again before reading `digest-context.*`. Do not reuse previous run files as if they were fresh.

Default scope:

- Mentions of the authenticated handle.
- Home timeline hotspots.
- Own profile activity.
- X Chat conversations and text messages from the same strict 24-hour window.
- Optional keyword searches only when the user explicitly passes `--keywords`.

X Chat rules:

- Chat XDK decrypts messages locally; no Chat passcode is saved.
- A conversation needs a reply only when its latest in-window text message came from another participant.
- Preserve every conversation returned by X. If its history is empty or unreadable, mark its reply state `unknown`; never classify it as handled or waiting for reply.
- `has_message_requests=true` is a required todo. The current conversations endpoint does not identify the requester, so state that limitation instead of inventing a participant or claiming the request inbox is empty.
- Exclude messages with missing/unparseable timestamps and all messages outside the exact 24-hour window.
- If any required X Chat request or decryption fails, fail the run instead of claiming the inbox is empty.

Time window rules:

- Final summary facts must use only items inside `[now - 24 hours, now]` in the user's current local timezone.
- Items with missing or unparseable timestamps are excluded from final-summary facts and reported as data gaps.
- Mentions older than the 24-hour window must not appear as pending reply opportunities.

Mention handling:

- Consider both direct mention/notification data and recent search results when available.
- Do not present an already-replied mention as needing reply.
- If reply status cannot be verified from current API data, label it `回复状态未确认` instead of claiming the user must reply.

## Writing The Digest

After collection, read the installed current-run context with the agent's file Read tool, not shell text commands.

Normal context paths:

- Claude Code: `~/.claude/skills/twitter-digest/.state/run/digest-context.md`
- Codex: `~/.codex/skills/twitter-digest/.state/run/digest-context.md`

Focused slices:

- `digest-context-timeline.md`
- `digest-context-mentions.md`
- `digest-context-dm.md`

Use `digest-context.md` and its `Final Summary Facts` as the content source for the Chinese digest. Use `digest-input.*` only for debugging collection issues.

Do not use `cat`, `head`, `tail`, `grep`, `sed`, `python3 -c`, or temporary scripts to inspect private context during normal summarization. If counts or structure must be checked, run:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/inspect_digest.py
python3 ~/.codex/skills/twitter-digest/scripts/inspect_digest.py
```

Adjust the path to the current agent.

Digest format:

- 今日总结.
- 该处理.
- 谁 @ 了你.
- 时间线热点.
- 你的动态.
- 数据缺口.
- 建议回复草稿.

Never automatically post, reply, like, follow, block, open suspicious links, accept requests, or send DMs. Replies are drafts only unless the user explicitly asks to send after reviewing.

## Install

From a checked-out repository:

```bash
python3 twitter-digest/scripts/install.py
```

The installer checks Python 3.10+ and installs the skill into the target agent skill directory.

Default install targets the current agent client:

- Codex: `~/.codex/skills/twitter-digest`
- Claude Code: `~/.claude/skills/twitter-digest`

Use `--client codex`, `--client claude`, or `--skills-dir` to override. Local development can use `--symlink`.

Reinstalling is upgrading. The installer moves the existing installed skill to `.backups/`, disables backup `SKILL.md` files so agents do not load old duplicate skills, and preserves the active installed `.state` directory, including X Chat runtime and key state.

Uninstall:

```bash
~/.codex/skills/twitter-digest/uninstall.sh --client codex
~/.claude/skills/twitter-digest/uninstall.sh --client claude
```

Use `--purge-state` only when the user explicitly wants API config and current-run files removed permanently.

## Run Outputs

Each run writes only current-run files:

- `<installed-skill>/.state/config.json`
- `<installed-skill>/.state/api_config.json`
- `<installed-skill>/.state/chat/config.json`
- `<installed-skill>/.state/chat/runtime/`
- `<installed-skill>/.state/run/digest-context.md`
- `<installed-skill>/.state/run/digest-context.json`
- `<installed-skill>/.state/run/digest-context-timeline.md`
- `<installed-skill>/.state/run/digest-context-mentions.md`
- `<installed-skill>/.state/run/digest-context-dm.md`
- `<installed-skill>/.state/run/digest-input.md`
- `<installed-skill>/.state/run/digest-input.json`

No long-term memory or daily archive is produced. Run dates use the user's local timezone.

## Troubleshooting

- Missing or invalid API config, X Chat config, or Chat runtime: run `RUN_DAILY_DIGEST --configure`. It opens one Terminal wizard and skips any valid existing step.
- Token refresh failed: the wrapper opens API configuration and retries once.
- X Chat API/decryption failure: the digest fails; reconfigure Chat or report the exact API error.
- Public API permission/tier/rate-limit errors: report the data gap or failure.
- Non-API source requests: unsupported in this skill.
