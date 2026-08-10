---
name: twitter-digest
description: Use when the user asks to generate an X/Twitter daily digest or says phrases such as "生成X日报", "生成 x 日报", "X日报", "推特日报", "Twitter digest", or wants an agent to analyze their own X/Twitter mentions, X Chat, home timeline, reply opportunities, and daily social-media summaries. This skill is API-only and requires X Chat.
---

# X/Twitter Digest

## Overview

Use this skill to produce a concise Chinese daily digest from the user's own X/Twitter account. The data source is API-only and includes required X Chat collection through the official Chat XDK.

For a normal digest in Claude Code, the first tool action must be exactly:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py
```

For a normal digest in Codex, the first tool action must be exactly:

```bash
python3 ~/.codex/skills/twitter-digest/scripts/run_daily_digest.py
```

These installed wrapper commands are the only normal execution entry points. `RUN_DAILY_DIGEST` below is shorthand for the matching command:

- Claude Code: `python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py`
- Codex: `python3 ~/.codex/skills/twitter-digest/scripts/run_daily_digest.py`

For API maintenance, `CONFIGURE_API` means:

- Claude Code: `python3 ~/.claude/skills/twitter-digest/scripts/configure_api.py`
- Codex: `python3 ~/.codex/skills/twitter-digest/scripts/configure_api.py`

For X Chat maintenance, `CONFIGURE_CHAT` means:

- Claude Code: `python3 ~/.claude/skills/twitter-digest/scripts/configure_chat.py`
- Codex: `python3 ~/.codex/skills/twitter-digest/scripts/configure_chat.py`

## Source Contract

`twitter-digest` has one API source. The installed wrapper internally runs the public/account collector and the X Chat collector, then merges their current-run output.

Never invoke `api_x_digest.py`, `chat_x_digest.py`, `digest_context.py`, or other internal scripts directly during a normal digest run.

### Operator mode (mandatory)

A digest request is an operation, not a software-development task.

- Run the installed wrapper immediately. Do not inspect repository files first.
- Do not create, edit, patch, or propose Python, shell, JavaScript, temporary scripts, replacement collectors, or diagnostic programs.
- Do not use inline code such as `python3 -c` to reproduce, verify, bypass, or repair collection.
- Do not change the installed skill, its dependencies, Claude settings, or `.state` during a digest run, except through documented wrapper options.
- On any wrapper failure, preserve and report the wrapper's exact actionable error. Use only the documented commands in this file.
- Enter code-development/debugging mode only when the user explicitly asks to inspect, fix, or develop the twitter-digest skill itself.

If the user merely says “重试”, “继续”, “再试一次”, “要”, “日报”, or “生成”, run the same installed wrapper again. Those words do not authorize writing code.

Source rules:

- A normal "生成日报" / "日报" / "要" request always runs `RUN_DAILY_DIGEST`.
- API credentials and X Chat decryption keys are required before a digest can be generated.
- If API credentials are already saved, the run uses API and refreshes OAuth tokens when possible.
- If API credentials are missing or expired, the wrapper starts API configuration. If X Chat is not configured, it starts X Chat configuration. The digest must be rerun after either configuration succeeds.
- When configuration is opened in Terminal, do not ask the user to paste Client ID, Client Secret, tokens, app credentials, or X Chat passcode in chat. One Terminal wizard collects all three inputs and completes OAuth. Tell the user to finish that single flow, then rerun `RUN_DAILY_DIGEST`.
- Do not switch to another data source on API or X Chat errors, rate limits, permission errors, or user requests for "more complete" data.
- Do not repair a failed run by inspecting or modifying source code. Report the error and the documented next action.
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
tweet.read users.read offline.access dm.read
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

- Reuses a read-only OAuth2 user token with `dm.read`, `users.read`, and `tweet.read`.
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

Do not write ad-hoc token verification scripts or any other diagnostic code. Direct bearer-token and environment-variable token overrides are unsupported; use only the verified read-only OAuth configuration flow.

## Data Collection

For every new digest request, run collection again before reading `digest-context.*`. Do not reuse previous run files as if they were fresh.

If public collection succeeds but required X Chat fails, the wrapper records a private retry marker. A matching retry within 15 minutes reuses only that fresh public result and reruns X Chat; it is still the same failed digest attempt, not historical-memory reuse. A normal new run or a changed account/window/query recollects public data.

Default scope:

- Mentions of the authenticated handle.
- Home timeline hotspots.
- Own profile activity.
- People who currently like the user's own posts published inside the 24-hour window.
- X Chat conversations and text messages from the same strict 24-hour window.
- Optional keyword searches only when the user explicitly passes `--keywords`.

For an explicit seven-day Chat request, run `RUN_DAILY_DIGEST --chat-window-hours 168 --chat-scan more`. This changes only the X Chat window; public timeline, mentions, and own activity remain on the strict 24-hour digest window. If the user explicitly asks to “查看更多私信” or see more Chat conversations, run `RUN_DAILY_DIGEST --chat-scan more`.

X Chat rules:

- Chat XDK decrypts messages locally; no Chat passcode is saved.
- A conversation needs a reply only when its latest in-window text message came from another participant.
- Process the conversation list in X's returned order. Inspect the first event page before fetching signing keys. Do not classify an unscanned conversation as empty, handled, or waiting for reply.
- For an `unknown` conversation, do not expose the technical state or ask the user to verify it. Mention it only as historical context using the exact friendly pattern `曾经收到过消息：@sender1、@sender2`, listing the known participants and adding no explanation or action.
- Exclude messages with missing/unparseable timestamps and all messages outside the exact 24-hour window.
- If a required attempted X Chat request or decryption fails, fail the run instead of claiming the inbox is empty. Reaching a deliberate safe-scan boundary is a reported data gap, not a network failure.
- In the default `recent` profile, inspect at most 10 conversations, use at most 10 Chat event requests, and load at most 1 event page per conversation. Use the `more` profile only on an explicit user request; it allows at most 50 conversations, 20 event requests, and 3 event pages per conversation. Always reserve the last 5 requests reported by X.
- For conversation-list pagination, use at most 5 requests, stop after 3 consecutive empty pages, stop on a repeated pagination token, and stop when X says more results exist without returning a token. Preserve already collected conversations and mark coverage incomplete.
- Fetch participant signing keys only after the first event page shows that a conversation may contain in-window events.
- When safe scanning stops before the returned list is exhausted, say `X Chat 已按 X 返回顺序检查 N 个会话`. The conversations endpoint does not expose a reliable recency field, so never call this list “最近的会话”. Do not expose request-budget internals or say the remaining conversations had no messages.
- A remaining conversation-list pagination token or a listed conversation without an ID is also a safe-scan boundary. Mark the scan incomplete and use the same friendly checked-count sentence; never claim that later or unscannable conversations had no messages.
- Cache participant signing public keys locally for 24 hours, keyed by X account and user ID. Query only missing or expired entries. If Chat XDK reports verification/decryption errors, refresh the affected conversation's keys once and retry; fail normally if verification still fails.
- On HTTP 429, stop immediately in both normal collection and initial Chat configuration. Name only the friendly category: `X Chat 会话列表暂时受到限流`, `X Chat 消息读取暂时受到限流`, or `X Chat 公钥读取暂时受到限流`; include the estimated recovery time when available. Never expose a concrete conversation ID, user ID, raw API path, or response body. Do not repeatedly hit the same rate-limited endpoint inside one run.
- When X returns a known retry interval for a Chat 429, cache only the sanitized endpoint category and expiry in owner-only local state. Until expiry, do not send another request to that endpoint; return the same friendly rate-limit message locally. Never cache an unknown reset time.
- Per-endpoint HTTP attempt counts are internal diagnostics. Do not include them in a normal digest unless the user explicitly asks for API statistics.

Time window rules:

- Public final-summary facts must use only items inside `[now - 24 hours, now]` in the user's current local timezone. X Chat uses 24 hours by default or the explicit `--chat-window-hours` value requested by the user.
- Items with missing or unparseable timestamps are excluded from final-summary facts and reported as data gaps.
- Mentions older than the 24-hour window must not appear as pending reply opportunities.

Mention handling:

- Consider both direct mention/notification data and recent search results when available.
- Do not present an already-replied mention as needing reply.
- When a mention is a direct `replied_to` reference to one of the user's posts, say `@sender 回复了你的帖子`. Do not add `回复状态未确认`. Add `你已回复` only when current API data contains positive reply evidence.
- If reply status cannot be verified from current API data, label it `回复状态未确认` instead of claiming the user must reply.

Like handling:

- X provides current liking users for a Post, but not a timestamped like-notification list through this lookup.
- Query liking users only for the user's own posts published inside the digest window and having `like_count > 0`; this keeps the resulting likes within the same window.
- Say `@sender 点赞了你的帖子` and identify the target post. Do not invent an exact like time.
- If liking-user lookup is unavailable for the user's API tier, report that source as unavailable instead of claiming there were no likes.

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

Keep the digest compact and use these six sections only when they contain useful information:

- 今日必须知道.
- 今日必须处理.
- Mentions.
- Timeline.
- 私信.
- 数据缺口.

When a verified manual action exists, add a `需要你在 X 界面操作` section near `该处理`. Write plain Chinese instructions rather than exposing raw API fields or English states. Do not put unknown conversations in this action section. If unknown conversations have known participants, add one compact informational line elsewhere: `曾经收到过消息：@sender1、@sender2`. Add no technical explanation, warning, or instruction after it.

If `dm_scan_complete=false`, add one quiet informational sentence: `X Chat 已按 X 返回顺序检查 N 个会话。` Do not present this as an error or ask the user to retry immediately.

Never post, reply, like, follow, block, open suspicious links, accept requests, or send DMs. 不得生成、推荐或改写任何回复内容，也不要提供回复草稿、模板或可复制话术。

This skill never sends messages, even after review. If the user asks to send or asks what to reply, explain briefly that twitter-digest is permanently read-only and does not prepare reply content. Never create code or call another tool to bypass this restriction.


## Install

Codex:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.14-beta.14/twitter-digest/install.sh | env TWITTER_DIGEST_INSTALL_CLIENT=codex sh
```

Claude Code:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.14-beta.14/twitter-digest/install.sh | env TWITTER_DIGEST_INSTALL_CLIENT=claude TWITTER_DIGEST_ALLOW_CLAUDE_COMMANDS=1 TWITTER_DIGEST_ALLOW_CLAUDE_STATE_READ=1 sh
```

The installer checks Python 3.10+ and installs the skill into the target agent skill directory.

After a standard install, immediately run the installed unified X API and X Chat configuration check. Reuse valid saved state and prompt only for missing or invalid setup. Custom `--skills-dir` installs and dry runs skip this step. Set `TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL=0` only when the user intentionally wants installation without configuration.

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
- `<installed-skill>/.state/chat/signing_keys.json`
- `<installed-skill>/.state/chat/rate_limits.json`
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
- Token refresh failed: let the wrapper open configuration; after the user finishes it, rerun `RUN_DAILY_DIGEST`.
- X Chat API/decryption failure: report the wrapper's exact error. Run `RUN_DAILY_DIGEST --configure` only when the error explicitly says configuration or saved keys are invalid.
- Public API permission/tier/rate-limit errors: report the wrapper's exact data gap or failure and stop. Do not build a workaround.
- Non-API source requests: unsupported in this skill.
